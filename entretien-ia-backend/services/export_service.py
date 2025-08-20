import pandas as pd
from io import BytesIO
from database.models import Answers, db, Sessions, Reports, Users
from sqlalchemy import text

def get_export_data(filters: dict):
    query = db.select(
        Sessions.id.label("session_id"),
        Sessions.date_entretien,
        Sessions.poste_vise,
        Users.nom.label("nom_candidat"),
        Reports.note_globale,
        Reports.score_grammaire,
        (db.select(db.func.avg(Answers.score_pertinence)).where(Answers.session_id == Sessions.id)).label("score_pertinence_moyen")
    ).select_from(Sessions).join(
        Users, Users.id == Sessions.user_id
    ).outerjoin(
        Reports, Reports.session_id == Sessions.id
    )

    if filters.get('start_date'):
        query = query.where(Sessions.date_entretien >= filters['start_date'])
    if filters.get('end_date'):
        query = query.where(Sessions.date_entretien <= filters['end_date'])
    if filters.get('recruiter_id'):
        query = query.where(Sessions.recruteur_id == int(filters['recruiter_id']))
    if filters.get('poste_vise'):
        query = query.where(Sessions.poste_vise.ilike(f"%{filters['poste_vise']}%"))

    results = db.session.execute(query.order_by(Sessions.date_entretien.desc())).all()
    
    # Conversion en dictionnaire pour le JSON et le DataFrame Pandas
    data_list = [row._asdict() for row in results]
    return data_list

def export_to_csv(data: list) -> BytesIO:
    """
    Convertit une liste de dictionnaires en un fichier CSV en mémoire.
    """
    if not data:
        return None
    df = pd.DataFrame(data)
    df = df.rename(columns={
        "session_id": "ID Session",
        "date_entretien": "Date",
        "poste_vise": "Poste Visé",
        "nom_candidat": "Candidat",
        "note_globale": "Note Globale (/100)",
        "score_grammaire": "Score Grammaire (/1)",
        "score_pertinence_moyen": "Score Pertinence (/1)"
    })
    
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    return output