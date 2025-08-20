from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
import numpy as np
from database.models import Answers, EmotionScores, Reports, db,Users, Sessions
from sqlalchemy import func, not_, cast, Date

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/api/users/candidates', methods=['GET'])
@jwt_required()
def get_candidates():
    claims = get_jwt()
    if claims.get('role') not in ['recruteur', 'admin']:
        return jsonify({"msg": "Accès réservé aux recruteurs et administrateurs."}), 403

    candidates = db.session.execute(
        db.select(Users).filter_by(role='candidat').order_by(Users.nom)
    ).scalars().all()

    candidates_data = [{"id": user.id, "nom": user.nom, "email": user.email} for user in candidates]
    
    return jsonify(candidates_data), 200


@user_bp.route('/api/users/profile', methods=['PUT'])
@jwt_required()
def update_my_profile():
    claims = get_jwt()
    user_id = claims.get('user_id')
    
    user = db.session.get(Users, user_id)
    if not user:
        return jsonify({"msg": "Utilisateur non trouvé."}), 404
        
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Aucune donnée fournie."}), 400

    if 'nom' in data:
        user.nom = data['nom']
        
    if 'new_password' in data and data['new_password']:
        user.set_password(data['new_password'])
        # On met le flag à FALSE
        user.doit_changer_mdp = False
        print(f"L'utilisateur {user.email} a changé son mot de passe, flag mis à FALSE.")
    
    db.session.commit()
    
    return jsonify({
        "msg": "Profil mis à jour avec succès.",
        "user_info": {
            "user_id": user.id,
            "nom": user.nom,
            "role": user.role,
            "doit_changer_mdp": user.doit_changer_mdp
        }
    }), 200
    


@user_bp.route('/api/candidate/dashboard', methods=['GET'])
@jwt_required()
def get_candidate_dashboard_data():
    """
    Rassemble et agrège des données complètes pour le tableau de bord du candidat.
    """
    claims = get_jwt()
    user_id = claims.get('user_id')
    
    if claims.get('role') != 'candidat':
        return jsonify({"msg": "Accès réservé aux candidats."}), 403

    # 1. Récupérer les entretiens en attente
    pending_sessions_query = db.session.execute(
        db.select(Sessions).filter_by(user_id=user_id, statut='pending').order_by(Sessions.date_entretien.desc())
    ).scalars().all()
    pending_sessions = [{"id": s.id, "poste_vise": s.poste_vise, "date_creation": s.date_entretien.strftime("%d/%m/%Y")} for s in pending_sessions_query]

    # 2. Récupérer les détails de chaque session terminée et analysée
    completed_sessions_query = db.session.execute(
        db.select(Sessions, Reports, EmotionScores)
        .join(Reports, Sessions.id == Reports.session_id)
        .outerjoin(EmotionScores, Sessions.id == EmotionScores.session_id)
        .filter(Sessions.user_id == user_id, Sessions.statut.in_(['analysis_complete', 'validated', 'file_uploaded', 'analyzing', 'analysis_failed']))
        .order_by(Sessions.date_entretien.desc())
    ).all()
    
    completed_sessions_details = []
    for session, report, emotion_scores in completed_sessions_query:
        # Pour chaque session, on calcule sa propre moyenne de pertinence
        avg_relevance_result = db.session.execute(
            db.select(func.avg(Answers.score_pertinence)).filter_by(session_id=session.id)
        ).scalar_one_or_none() or 0.0
        
        completed_sessions_details.append({
            "id": session.id,
            "poste_vise": session.poste_vise,
            "date": session.date_entretien.isoformat(),
            "global_score": report.note_globale if report else None,
            "relevance_score": float(avg_relevance_result),
            "grammar_score": report.score_grammaire if report else None,
            "dominant_emotion": emotion_scores.dominant_emotion if emotion_scores else "N/A",
            "statut": session.statut
        })
        
    # 3. Assemblage final de la réponse
    dashboard_data = {
        "nom_candidat": claims.get('nom'),
        "pending_sessions": pending_sessions,
        "completed_sessions": completed_sessions_details
    }

    return jsonify(dashboard_data), 200