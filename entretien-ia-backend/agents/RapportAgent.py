import numpy as np
from flask import render_template
from database.models import db, Sessions

try:
    from weasyprint import HTML
except ImportError:
    HTML = None

class RapportAgent:
    def __init__(self):
        print("RapportAgent instancié.")
        if HTML is None:
            print("AVERTISSEMENT: WeasyPrint n'est pas installé. La génération de PDF sera désactivée.")

    def _load_weights_for_session(self, session: Sessions) -> dict:
        """
        Lit les poids du profil associé à la session.
        Retourne des poids par défaut si aucun profil n'est trouvé.
        Les poids sont retournés en tant que POURCENTAGES (ex: 40, 30...).
        """
        default_weights = {
            'relevance': 40, 'clarity': 30, 
            'fluency': 15, 'engagement': 15
        }
        
        if not session or not session.profil_ponderation or not isinstance(session.profil_ponderation.poids, dict):
            print("AVERTISSEMENT: Aucun profil de pondération valide trouvé. Utilisation des poids par défaut.")
            return default_weights
        
        weights = session.profil_ponderation.poids
        print(f"Utilisation des poids du profil '{session.profil_ponderation.nom_profil}': {weights}")
        # On fusionne avec les défauts pour s'assurer que toutes les clés sont présentes
        return {**default_weights, **weights}

    def _normalize_score(self, value, min_val, max_val):
        if value is None: return 0
        return max(0, min(100, ((value - min_val) / (max_val - min_val)) * 100))

    def calculate_global_score(self, session_id: int, analysis_results: dict) -> float:
        """
        Calcule la note globale pondérée en chargeant les poids spécifiques à la session.
        """
        if not analysis_results:
            return 0.0

        # 1. On charge la session pour obtenir le profil de poids (en pourcentages)
        session = db.session.get(Sessions, session_id)
        weights_percent = self._load_weights_for_session(session)

        weights_proportion = {key: value / 100.0 for key, value in weights_percent.items()}
        
        # 2. Extraction et calcul des scores de base (sur 100) - (déjà correct)
        relevance_scores = [a.get('score_pertinence') for a in analysis_results.get('answers_analysis', []) if a.get('score_pertinence') is not None]
        avg_relevance = np.mean(relevance_scores) if relevance_scores else 0
        relevance_score_100 = avg_relevance * 100
        
        grammar_scores = [a.get('score_grammaire') for a in analysis_results.get('answers_analysis', []) if a.get('score_grammaire') is not None]
        avg_grammar = np.mean(grammar_scores) if grammar_scores else 0
        clarity_score_100 = avg_grammar * 100

        fluency_score_100 = analysis_results.get('vocal_analysis', {}).get('fluency_score', 0)
        
        emotion_scores = analysis_results.get('emotion_analysis', {}).get('scores', {})
        calm_happy = (emotion_scores.get('calme', 0) + emotion_scores.get('heureux', 0))
        anger_fear = (emotion_scores.get('colère', 0) + emotion_scores.get('peur', 0))
        engagement_score_raw = calm_happy - anger_fear
        engagement_score_100 = self._normalize_score(engagement_score_raw, -1, 1)

        print(f"Scores intermédiaires (sur 100) : Pertinence={relevance_score_100:.2f}, Clarté={clarity_score_100:.2f}, Fluidité={fluency_score_100:.2f}, Engagement={engagement_score_100:.2f}")
        
        final_score = (
            relevance_score_100 * weights_proportion.get('relevance', 0.4) +
            clarity_score_100 * weights_proportion.get('clarity', 0.3) +
            fluency_score_100 * weights_proportion.get('fluency', 0.15) +
            engagement_score_100 * weights_proportion.get('engagement', 0.15)
        )
        
        return round(final_score, 2)

    def interpret_communication_profile(self, report_data: dict) -> dict:
        relevance_avg = report_data.get('global_scores', {}).get('relevance_avg', 0)
        grammar_avg = report_data.get('global_scores', {}).get('grammar_avg', 0)
        speech_rate = report_data.get('vocal_analysis', {}).get('speech_rate', 0)
        pause_count = report_data.get('vocal_analysis', {}).get('pause_count', 0)
        dominant_emotion = report_data.get('emotion_scores', {}).get('dominant_emotion', '')
        
        # Profil "Analytique & Précis"
        if relevance_avg >= 0.75 and grammar_avg >= 0.8 and speech_rate < 145 and dominant_emotion in ['calme', 'neutre']:
            return {
                "title": "Profil : Analytique & Précis",
                "description": "Ce candidat est méthodique et structuré. Il prend le temps de réfléchir pour fournir des réponses précises et bien formulées. Son discours est factuel et maîtrisé."
            }
        # Profil "Dynamique & Persuasif"
        if relevance_avg >= 0.6 and speech_rate > 155 and dominant_emotion in ['heureux', 'surpris']:
            return {
                "title": "Profil : Dynamique & Persuasif",
                "description": "Ce candidat communique avec énergie et conviction. Il est capable de présenter ses idées de manière rapide et engageante. Son style est persuasif."
            }
        # Profil "Réfléchi & Hésitant"
        if relevance_avg >= 0.6 and speech_rate < 125 and pause_count > 8:
            return {
                "title": "Profil : Réfléchi & Hésitant",
                "description": "Le candidat semble bien connaître son sujet, mais montre des signes d'hésitation. Son discours est marqué par des pauses, indiquant une recherche de mots."
            }
        # Profil "Passionné & Potentiellement Confus"
        if relevance_avg < 0.5 and grammar_avg < 0.7 and speech_rate > 170:
             return {
                "title": "Profil : Passionné & Potentiellement Confus",
                "description": "Le candidat montre beaucoup d'énergie mais a des difficultés à structurer son discours et à répondre directement aux questions."
            }
        # Profil par défaut
        return {
            "title": "Profil : Communicant Équilibré",
            "description": "Le style de communication du candidat est équilibré et ne présente pas de trait dominant extrême. Il semble capable de s'adapter à différentes situations.",
        }


    def generate_pdf_report(self, report_data: dict) -> bytes:
        if HTML is None:
            print("ERREUR: WeasyPrint n'est pas disponible pour générer le PDF.")
            return None

        print("Génération du rapport PDF en cours...")
        try:
            communication_profile = self.interpret_communication_profile(report_data)
            report_data['communication_profile'] = communication_profile
            html_string = render_template('report_template.html', data=report_data)

            # On convertit le HTML en PDF en mémoire.
            pdf_bytes = HTML(string=html_string).write_pdf()
            
            print("Génération du PDF terminée avec succès.")
            return pdf_bytes

        except Exception as e:
            print(f"ERREUR lors de la génération du PDF avec WeasyPrint : {e}")
            return None