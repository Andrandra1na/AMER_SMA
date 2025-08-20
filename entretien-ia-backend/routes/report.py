from flask import Blueprint, jsonify, make_response, request
from flask_jwt_extended import jwt_required, get_jwt
from tasks import run_analysis_task
from database.models import db, Sessions, Reports, Answers, AudioFeatures, Users, Questions, EmotionScores, FacialFeatures

report_bp = Blueprint('report_bp', __name__)

def _get_full_report_data(session_id: int, current_user_id: int, current_user_role: str) -> dict:
    session = db.session.get(Sessions, session_id)
    if not session:
        return {"error": "Session non trouvée.", "status": 404}

    is_candidat_owner = (session.user_id == current_user_id)
    is_recruiter_owner = (session.recruteur_id == current_user_id)
    is_admin = (current_user_role == 'admin')

    if not (is_candidat_owner or is_recruiter_owner or is_admin):
        return {"error": "Accès non autorisé à ce rapport.", "status": 403}
    
    report_data = db.session.execute(db.select(Reports).filter_by(session_id=session_id)).scalar_one_or_none()
    if not report_data:
        return {"error": "Le rapport de base pour cette session n'est pas encore généré.", "status": 404}
    
    audio_features_data = db.session.execute(db.select(AudioFeatures).filter_by(session_id=session_id)).scalar_one_or_none()
    emotion_scores_data = db.session.execute(db.select(EmotionScores).filter_by(session_id=session_id)).scalar_one_or_none()
    facial_features_data = db.session.execute(db.select(FacialFeatures).filter_by(session_id=session_id)).scalar_one_or_none()
    
    answers_data_query = db.session.execute(
        db.select(Answers, Questions.intitule, Questions.category)
        .join(Questions, Answers.question_id == Questions.id)
        .filter(Answers.session_id == session_id).order_by(Answers.id)
    ).all()
    
    candidat = db.session.get(Users, session.user_id)

    if not report_data:
        return {"error": "Le rapport de base pour cette session n'a pas encore été généré.", "status": 404}

    relevance_scores = [a.score_pertinence for a, _, _ in answers_data_query if a.score_pertinence is not None]
    avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0

    final_report = {
        "session_info": {
            "id": session.id,
            "date": session.date_entretien.strftime("%d/%m/%Y à %H:%M"),
            "poste_vise": session.poste_vise,
            "candidat_nom": candidat.nom if candidat else "N/A",
            "video_path": session.fichier_video,
            "audio_path": session.fichier_audio
        },
        "global_scores": {
            "note_globale": report_data.note_globale,
            "relevance_avg": avg_relevance,
            "grammar_avg": report_data.score_grammaire,
            "transcription_complete": report_data.transcription_complete
        },
        "validation_info": {
            "validated": report_data.validated,
            "commentaire_rh": report_data.commentaire_rh
        },
        "vocal_analysis": {
            "speech_rate": audio_features_data.speech_rate if audio_features_data else None,
            "pause_count": audio_features_data.pause_count if audio_features_data else None,
            "average_pause_duration": audio_features_data.average_pause_duration if audio_features_data else None
        },
        "emotion_scores": {
            "dominant_emotion": emotion_scores_data.dominant_emotion if emotion_scores_data else None,
            "scores": emotion_scores_data.scores if emotion_scores_data else {}
        },
        "gaze_analysis": {
            "global_distribution": facial_features_data.gaze_global_distribution if facial_features_data else {},
            "by_question": facial_features_data.gaze_by_question if facial_features_data else {}
        },
        "detailed_answers": [{
            "question_id": answer.question_id,
            "question_intitule": question_intitule,
            "question_category": question_category,
            "transcription": answer.transcription,
            "score_pertinence": answer.score_pertinence,
            "pertinence_explication": answer.pertinence_explication,
            "score_grammaire": answer.score_grammaire,
            "erreurs_grammaire_details": answer.erreurs_grammaire 
        } for answer, question_intitule, question_category in answers_data_query]
    }
    return final_report

@report_bp.route('/api/report/generate/<int:session_id>', methods=['POST'])
@jwt_required()
def generate_report_task(session_id):
    claims = get_jwt()
    if claims.get('role') not in ['recruteur', 'admin']:
        return jsonify({"msg": "Action non autorisée."}), 403
    
    session = db.session.get(Sessions, session_id)
    if not session:
        return jsonify({"msg": "Session non trouvée."}), 404
        
    session.statut = 'analyzing'
    db.session.commit()

    run_analysis_task.delay(session_id)
    return jsonify({"msg": "L'analyse a été lancée en arrière-plan."}), 202

@report_bp.route('/api/report/<int:session_id>', methods=['GET'])
@jwt_required()
def get_report_data(session_id):
    claims = get_jwt()
    report_dict = _get_full_report_data(session_id, claims.get('user_id'), claims.get('role'))
    
    if "error" in report_dict:
        return jsonify({"msg": report_dict["error"]}), report_dict["status"]
    
    return jsonify(report_dict), 200


@report_bp.route('/api/report/<int:session_id>/validate', methods=['POST'])
@jwt_required()
def validate_report(session_id):
    
    claims = get_jwt()
    user_role = claims.get('role')
    user_id = claims.get('user_id')

    if user_role not in ['recruteur', 'admin']:
        return jsonify({"msg": "Action réservée aux recruteurs et administrateurs."}), 403

    commentaire = request.get_json().get('commentaire')
    if commentaire is None:
        return jsonify({"msg": "Le champ 'commentaire' est requis."}), 400

    report = db.session.execute(db.select(Reports).filter_by(session_id=session_id)).scalar_one_or_none()
    if not report:
        return jsonify({"msg": "Aucun rapport trouvé pour cette session."}), 404
        
    session = db.session.get(Sessions, session_id)
    if user_role == 'recruteur' and session.recruteur_id != user_id:
        return jsonify({"msg": "Vous ne pouvez valider que les entretiens que vous avez créés."}), 403

    report.commentaire_rh = commentaire
    report.validated = True
    session.statut = 'validated'
    db.session.commit()

    updated_report_data = _get_full_report_data(session_id, user_id, user_role)
    if "error" in updated_report_data:
        return jsonify({"msg": updated_report_data["error"]}), updated_report_data["status"]
    
    return jsonify(updated_report_data)

@report_bp.route('/api/report/<int:session_id>/pdf', methods=['GET'])
@jwt_required()
def download_pdf_report(session_id):
    claims = get_jwt()
    
    report_dict = _get_full_report_data(session_id, claims.get('user_id'), claims.get('role'))
    if "error" in report_dict:
        return jsonify({"msg": report_dict["error"]}), report_dict["status"]

    from agents.RapportAgent import RapportAgent

    rapport_agent = RapportAgent()
    pdf_content = rapport_agent.generate_pdf_report(report_dict)

    if pdf_content is None:
        return jsonify({"msg": "Échec de la génération du PDF."}), 500

    response = make_response(pdf_content)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=rapport_session_{session_id}.pdf'
    
    return response