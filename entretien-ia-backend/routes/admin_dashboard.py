from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from database.models import db, Users, Sessions, Questions, Reports 
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

admin_dashboard_bp = Blueprint('admin_dashboard_bp', __name__)

def admin_required():
    def wrapper(fn):
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') != 'admin':
                return jsonify({"msg": "Accès réservé aux administrateurs."}), 403
            return fn(*args, **kwargs)
        decorator.__name__ = f"admin_wrapper_{fn.__name__}"
        return decorator
    return wrapper

@admin_dashboard_bp.route('/api/admin/dashboard', methods=['GET'])
@admin_required()
def get_admin_dashboard_stats():
    total_users = db.session.scalar(db.select(func.count(Users.id)))
    role_distribution_query = db.session.execute(db.select(Users.role, func.count(Users.id)).group_by(Users.role)).all()
    role_distribution = {role: count for role, count in role_distribution_query}
    total_sessions = db.session.scalar(db.select(func.count(Sessions.id)))
    total_questions = db.session.scalar(db.select(func.count(Questions.id)))
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_activity_query = db.session.execute(
        db.select(
            func.date(Sessions.date_entretien), 
            func.count(Sessions.id),
            func.avg(Reports.note_globale) 
        )
        .join(Reports, Sessions.id == Reports.session_id) 
        .filter(Sessions.date_entretien >= thirty_days_ago)
        .group_by(func.date(Sessions.date_entretien))
        .order_by(func.date(Sessions.date_entretien))
    ).all()
    
    daily_activity = {
        date.strftime("%Y-%m-%d"): {
            "count": count,
            "avg_score": float(avg_score) if avg_score is not None else 0
        } for date, count, avg_score in daily_activity_query
    }

    latest_sessions_query = db.session.execute(
        db.select(Sessions, Reports.note_globale)
        .options(joinedload(Sessions.candidat)) 
        .outerjoin(Reports, Sessions.id == Reports.session_id) 
        .order_by(Sessions.date_entretien.desc())
        .limit(10) 
    ).all()
    
    latest_sessions = []
    for s, note_globale in latest_sessions_query:
        candidat_nom = s.candidat.nom if s.candidat else "Candidat Supprimé"
        latest_sessions.append({
            "id": s.id,
            "poste_vise": s.poste_vise,
            "candidat_nom": candidat_nom,
            "date": s.date_entretien.isoformat(), 
            "statut": s.statut, 
            "note_globale": note_globale 
        })
   
    stats = {
        "kpis": {
            "total_users": total_users, 
            "total_sessions": total_sessions,
            "total_questions": total_questions, 
            "total_recruiters": role_distribution.get('recruteur', 0),
        },
        "charts": {
            "role_distribution": role_distribution, 
            "daily_activity": daily_activity,
        },
        "latest_sessions": latest_sessions
    }
    return jsonify(stats)