import os
import subprocess
import numpy as np
import torch
import torchaudio
from database.models import db, Sessions, Reports, Questions, Answers, AudioFeatures, EmotionScores, FacialFeatures
from agents.NLPAgent import NLPAgent
from agents.AudioAgent import AudioAgent
from agents.EmotionAgent import EmotionAgent
from agents.RapportAgent import RapportAgent
from agents.VideoAgent import VideoAgent

def get_agents():
    print("Initialisation des instances d'agents pour cette tâche...")
    nlp_agent = NLPAgent(model_size="small")
    audio_agent = AudioAgent()
    emotion_agent = EmotionAgent()
    rapport_agent = RapportAgent()
    video_agent = VideoAgent()
    return nlp_agent, audio_agent, emotion_agent, rapport_agent, video_agent


def convert_to_wav(source_path: str) -> str:
    """
    Convertit un fichier média en un fichier WAV mono 16kHz temporaire.
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Fichier source introuvable pour la conversion: {source_path}")

    directory = os.path.dirname(source_path)
    filename_without_ext = os.path.splitext(os.path.basename(source_path))[0]
    temp_wav_path = os.path.join(directory, f"{filename_without_ext}_temp.wav")

    command = ["ffmpeg", "-i", source_path, "-ar", "16000", "-ac", "1", "-y", temp_wav_path]

    print(f"Exécution de la conversion : {' '.join(command)}")
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Conversion en WAV réussie : {temp_wav_path}")
        return temp_wav_path
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise Exception(f"La conversion avec ffmpeg a échoué. Assurez-vous que ffmpeg est installé et dans le PATH. Erreur: {e}")


def run_analysis(session_id: int):
    print(f"--- DÉBUT DE L'ANALYSE COMPLÈTE - SESSION ID: {session_id} ---")
    nlp_agent, audio_agent, emotion_agent, rapport_agent, videoAgent = get_agents()
    session = db.session.get(Sessions, session_id)
    if not session: return None

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path_from_db = session.fichier_video or session.fichier_audio
    if not path_from_db: raise Exception(f"Aucun fichier média pour la session {session_id}.")
    absolute_media_path = os.path.join(BASE_DIR, 'data', 'uploads', path_from_db)

    events = session.events_timeline
    if not events: raise Exception(f"Timeline non trouvée pour la session {session_id}.")

    session.statut = 'analyzing'
    db.session.commit()
    
    wav_path_for_analysis = None
    try:
        # ÉTAPE 0 : CONVERSION & CHARGEMENT
        print("\n[Étape 0/5] Conversion et Chargement Audio...")
        wav_path_for_analysis = convert_to_wav(absolute_media_path)
        wav_tensor, sr = torchaudio.load(wav_path_for_analysis)
        if sr != audio_agent.sr: wav_tensor = torchaudio.transforms.Resample(sr, audio_agent.sr)(wav_tensor)
        if wav_tensor.shape[0] > 1: wav_tensor = torch.mean(wav_tensor, dim=0, keepdim=True)
        wav_tensor = wav_tensor.float()
        print("-> Audio chargé en mémoire.")

        # ÉTAPE 1 : TRANSCRIPTION GLOBALE
        print("\n[Étape 1/6] Transcription globale...")
        segments, info = nlp_agent.transcribe_media(wav_path_for_analysis)
        list_of_segments = list(segments)
        full_transcription = " ".join([s.text.strip() for s in list_of_segments])
        print("-> Transcription terminée.")

        # ÉTAPE 2 : ANALYSE DÉTAILLÉE PAR QUESTION/RÉPONSE (AVEC LOGIQUE RAG)
        print("\n[Étape 2/6] Analyse détaillée par question (Logique Hybride RAG)...")
        questions = db.session.execute(db.select(Questions).filter(Questions.id.in_(session.questions_ids))).scalars().all()
        questions_map = {q.id: q for q in questions}

        # --- RAG --- On définit les catégories qui nécessitent une vérification factuelle
        RAG_CATEGORIES = ['Motivation', 'Culture d\'entreprise']

        db.session.query(Answers).filter_by(session_id=session_id).delete()
        
        answers_analysis_list = []
        for i, event in enumerate(events):
            question = questions_map.get(event['questionId'])
            if not question: continue

            start_time = event['timestamp']
            end_time = events[i + 1]['timestamp'] if i + 1 < len(events) else info.duration
            response_text = " ".join([s.text.strip() for s in list_of_segments if s.start >= start_time and s.start < end_time])
            if not response_text.strip(): continue

            # --- RAG --- Logique Hybride : on choisit la bonne méthode d'analyse
            if question.category in RAG_CATEGORIES:
                print(f"-> Analyse RAG pour la question (cat: {question.category})")
                # On passe maintenant les DEUX arguments : la question ET la réponse.
                rag_analysis = nlp_agent.analyze_relevance_with_rag(question.intitule, response_text)
                relevance_score = rag_analysis.get('score_pertinence_factuelle', 0.0)
                relevance_explanation = rag_analysis.get('explication', '')
            else:
                print(f"-> Analyse Sémantique simple pour la question (cat: {question.category})")
                relevance_score = nlp_agent.analyze_relevance(question.ideal_answer, response_text)
                relevance_explanation = None
            
            # Analyses vocale et grammaticale sur le segment
            start_sample = int(start_time * audio_agent.sr)
            end_sample = int(end_time * audio_agent.sr)
            audio_chunk = wav_tensor[:, start_sample:end_sample]
            vocal_chunk_features = audio_agent.analyze_audio_chunk(audio_chunk, response_text)
            grammar_analysis = nlp_agent.analyze_grammar(response_text)
            
            answers_analysis_list.append({
                'score_pertinence': relevance_score,
                'score_grammaire': grammar_analysis['grammar_score'],
                'speech_rate': vocal_chunk_features.get('speech_rate'),
                'pause_count': vocal_chunk_features.get('pause_count'),
                'average_pause_duration': vocal_chunk_features.get('average_pause_duration')
            })

            db.session.add(Answers(
                session_id=session_id, question_id=question.id, transcription=response_text,
                score_pertinence=relevance_score,
                pertinence_explication=relevance_explanation, 
                score_grammaire=grammar_analysis['grammar_score'],
                erreurs_grammaire=grammar_analysis['errors'],
                speech_rate=vocal_chunk_features.get('speech_rate'),
                pause_count=vocal_chunk_features.get('pause_count')
            ))
        print(f"-> {len(answers_analysis_list)} réponses analysées en détail.")
        
        # --- ÉTAPE 3 - ANALYSE VISUELLE (REGARD) ---
        print("\n[Étape 3/6] Analyse visuelle du regard (MediaPipe)...")
        # On utilise le fichier vidéo original, pas le WAV
        gaze_analysis_results = videoAgent.analyze_gaze(absolute_media_path, events)
        
        if gaze_analysis_results:
            # On sauvegarde les résultats
            facial_features_entry = db.session.execute(db.select(FacialFeatures).filter_by(session_id=session_id)).scalar_one_or_none()
            if not facial_features_entry:
                facial_features_entry = FacialFeatures(session_id=session_id)
                db.session.add(facial_features_entry)
            
            facial_features_entry.gaze_global_distribution = gaze_analysis_results['gaze_global_distribution']
            facial_features_entry.gaze_by_question = gaze_analysis_results['gaze_by_question']
            
            print("-> Analyse du regard terminée et sauvegardée.")
        else:
            print("AVERTISSEMENT: L'analyse du regard n'a retourné aucun résultat.")

        # --- ÉTAPE 4 - AGRÉGATION ET ANALYSE GLOBALE ---
        print("\n[Étape 4/6] Agrégation des scores et analyse globale...")
        
        # Calcul des moyennes et totaux à partir des analyses détaillées
        valid_rates = [a['speech_rate'] for a in answers_analysis_list if a.get('speech_rate')]
        global_avg_speech_rate = np.mean(valid_rates) if valid_rates else 0
        global_total_pauses = sum([a['pause_count'] for a in answers_analysis_list if a.get('pause_count') is not None])

        # Analyses globales sur le fichier complet (pitch, émotion)
        global_vocal_features = audio_agent.analyze_speech_vocal_characteristics(wav_path_for_analysis, full_transcription)
        emotion_prediction = emotion_agent.predict_emotion(wav_path_for_analysis)
        
        # ON CALCULE LA MOYENNE PONDÉRÉE DES DURÉES DE PAUSE
        total_pause_duration_sum = sum([(a.get('average_pause_duration', 0) or 0) * (a.get('pause_count', 0) or 0) for a in answers_analysis_list])
        global_avg_pause_duration = total_pause_duration_sum / global_total_pauses if global_total_pauses > 0 else 0
        
        audio_features_entry = db.session.execute(db.select(AudioFeatures).filter_by(session_id=session_id)).scalar_one_or_none()
        if not audio_features_entry:
            audio_features_entry = AudioFeatures(session_id=session_id)
            db.session.add(audio_features_entry)
        
        audio_features_entry.speech_rate = global_avg_speech_rate
        audio_features_entry.pause_count = global_total_pauses
        audio_features_entry.average_pause_duration = global_avg_pause_duration
        audio_features_entry.pitch_mean = global_vocal_features['pitch_mean']
        audio_features_entry.pitch_std = global_vocal_features['pitch_std']
        audio_features_entry.fluency_score = global_vocal_features.get('fluency_score', 0.0) 
        
        emotion_scores_entry = db.session.execute(db.select(EmotionScores).filter_by(session_id=session_id)).scalar_one_or_none()
        if not emotion_scores_entry:
            emotion_scores_entry = EmotionScores(session_id=session_id)
            db.session.add(emotion_scores_entry)
        emotion_scores_entry.dominant_emotion = emotion_prediction['dominant_emotion']
        emotion_scores_entry.scores = emotion_prediction['scores']
        
        print(f"-> Analyse vocale globale terminée : Débit moyen={global_avg_speech_rate:.2f} mots/min, Pauses totales={global_total_pauses}")
        print(f"-> Analyse émotionnelle terminée : Émotion dominante={emotion_prediction['dominant_emotion'].capitalize()}")

        # ÉTAPE 5 : FUSION DES SCORES
        print("\n[Étape 5/6] Fusion des scores et calcul de la note globale...")
        
        final_analysis_data = {
            'vocal_analysis': audio_features_entry.to_dict(),
            'emotion_analysis': emotion_scores_entry.to_dict(),
            'answers_analysis': answers_analysis_list
        }
        
        note_globale = rapport_agent.calculate_global_score(session_id, final_analysis_data)
        print(f"-> Note globale calculée : {note_globale:.2f} / 100")
        
        # ÉTAPE 6 : FINALISATION DU RAPPORT
        print("\n[Étape 6/6] Finalisation du rapport...")
        report = db.session.execute(db.select(Reports).filter_by(session_id=session_id)).scalar_one_or_none()
        if not report:
            report = Reports(session_id=session_id)
            db.session.add(report)

        report.transcription_complete = full_transcription
        grammar_scores = [a['score_grammaire'] for a in answers_analysis_list if a.get('score_grammaire') is not None]
        if grammar_scores:
            report.score_grammaire = round(np.mean(grammar_scores), 2)
        report.note_globale = note_globale
        
        session.statut = 'analysis_complete'
        db.session.commit()

        print(f"\n ANALYSE COMPLÈTE TERMINÉE ET SAUVEGARDÉE (SESSION {session_id})")
        return {"status": "success"}

    except Exception as e:
        db.session.rollback()
        session.statut = 'analysis_failed'
        db.session.commit()
        print(f" ERREUR FATALE lors de l’analyse de la session {session_id}: {e}")
        return None
    finally:
        if wav_path_for_analysis and os.path.exists(wav_path_for_analysis):
            os.remove(wav_path_for_analysis)
            print(f" Fichier temporaire supprimé : {wav_path_for_analysis}")