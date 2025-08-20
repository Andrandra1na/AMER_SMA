from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.orm import joinedload
from database.models import db, Users, Sessions, Reports

recruiter_dashboard_bp = Blueprint('recruiter_dashboard_bp', __name__)

def recruiter_or_admin_required():
    def wrapper(fn):
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') not in ['recruteur', 'admin']:
                return jsonify({"msg": "Accès réservé."}), 403
            return fn(*args, **kwargs)
        decorator.__name__ = f"recruiter_admin_wrapper_{fn.__name__}"
        return decorator
    return wrapper

@recruiter_dashboard_bp.route('/api/recruiter/dashboard', methods=['GET'])
@recruiter_or_admin_required()
def get_recruiter_dashboard_data():
    """
    Récupère les données du dashboard recruteur.
    """
    claims = get_jwt()
    recruteur_id = claims.get('user_id')
    
    # On fait une seule requête pour récupérer toutes les sessions du recruteur
    all_sessions_query = db.session.execute(
        db.select(Sessions)
        .options(
            joinedload(Sessions.candidat), # On charge la relation 'candidat'
            joinedload(Sessions.report)   # On charge la relation 'report'
        )
        .filter(Sessions.recruteur_id == recruteur_id)
        .order_by(Sessions.date_entretien.desc())
    ).scalars().unique().all()

    # On traite les données en Python
    kpis = {"total": 0, "pending": 0, "analyzing": 0, "review_needed": 0}
    sessions_data = []

    for session in all_sessions_query:
        final_statut = session.statut
        if session.report and session.report.validated:
            final_statut = 'validated'
        elif session.statut == 'validated' and (not session.report or not session.report.validated):
            final_statut = 'analysis_complete'

        kpis["total"] += 1
        if final_statut == 'pending': kpis["pending"] += 1
        elif final_statut == 'analyzing': kpis["analyzing"] += 1
        elif final_statut == 'analysis_complete': kpis["review_needed"] += 1
            
        sessions_data.append({
            "id": session.id,
            "poste_vise": session.poste_vise,
            "statut": final_statut,
            "date_creation": session.date_entretien.isoformat(),
            "candidat": {
                # C'est maintenant sûr d'accéder à session.candidat
                "id": session.candidat.id,
                "nom": session.candidat.nom,
                "email": session.candidat.email,
            }
        })
        
    return jsonify({"sessions": sessions_data, "kpis": kpis})