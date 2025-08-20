import os
from flask import Blueprint, jsonify, request, send_from_directory, current_app
from flask_jwt_extended import jwt_required, get_jwt
from database.models import db, Questions, Sessions, Users, ProfilsPonderation
from services import session_service
from sqlalchemy import not_

session_bp = Blueprint('session_bp', __name__)

# ===================================================================
# SECTION 1 : ROUTES POUR LE RECRUTEUR
# ===================================================================

@session_bp.route('/api/session/create', methods=['POST'])
@jwt_required()
def create_session_by_recruiter():
    """
    Crée une nouvelle session d'entretien en se basant sur les choix du recruteur,
    notamment les compétences à évaluer.
    """
    claims = get_jwt()
    
    # 1. Vérification des permissions
    if claims.get('role') not in ['recruteur', 'admin']:
        return jsonify({"msg": "Action réservée aux recruteurs et administrateurs."}), 403

    # 2. Récupération et validation des données du frontend
    data = request.get_json()
    
    # On ajoute 'competences' à la liste des champs requis
    required_fields = ['candidate_id', 'poste_vise', 'profil_ponderation_id', 'competences']
    if not all(k in data for k in required_fields):
        return jsonify({"msg": "Données manquantes. Tous les champs sont requis."}), 400
    
    # On vérifie que la liste des compétences n'est pas vide
    if not data['competences'] or not isinstance(data['competences'], list):
        return jsonify({"msg": "Veuillez sélectionner au moins une compétence à évaluer."}), 400

    # 3. On délègue toute la logique de création au service
    #    C'est plus propre et plus facile à tester.
    try:
        new_session = session_service.create_session_for_recruiter(
            recruteur_id=claims.get('user_id'),
            user_id=data['candidate_id'],
            poste_vise=data['poste_vise'],
            profil_ponderation_id=data['profil_ponderation_id'],
            competences=data['competences']
        )
        return jsonify({
            "msg": "Session d'entretien créée avec succès.", 
            "session_id": new_session.id
        }), 201
    except ValueError as ve:
        # Erreurs métier spécifiques levées par le service (ex: candidat non trouvé)
        return jsonify({"msg": str(ve)}), 404
    except Exception as e:
        # Autres erreurs inattendues
        print(f"ERREUR lors de la création de la session : {e}")
        return jsonify({"msg": "Une erreur interne est survenue lors de la création de la session."}), 500

@session_bp.route('/api/profiles', methods=['GET'])
@jwt_required()
def get_all_profiles_for_selection():
    profiles = db.session.execute(db.select(ProfilsPonderation.id, ProfilsPonderation.nom_profil)).all()
    return jsonify([{"id": p.id, "nom_profil": p.nom_profil} for p in profiles])

# ===================================================================
# SECTION 2 : ROUTES POUR LE CANDIDAT
# ===================================================================

@session_bp.route('/api/sessions/pending', methods=['GET'])
@jwt_required()
def get_my_pending_sessions():
    claims = get_jwt()
    user_id = claims.get('user_id')
    
    sessions = db.session.execute(
        db.select(Sessions).filter_by(user_id=user_id, statut='pending')
        .order_by(Sessions.date_entretien.desc())
    ).scalars().all()
    
    sessions_data = [{
        "id": session.id,
        "date_creation": session.date_entretien.strftime("%d/%m/%Y"),
        "poste_vise": session.poste_vise,
        "statut": session.statut
    } for session in sessions]
        
    return jsonify(sessions_data), 200


@session_bp.route('/api/sessions/history', methods=['GET'])
@jwt_required()
def get_my_session_history():
    """
    [Candidat] Récupère l'historique de ses entretiens passés,
    en y joignant la note globale depuis la table des rapports.
    """
    claims = get_jwt()
    user_id = claims.get('user_id')

    print("--- REQUÊTE REÇUE : /api/sessions/history ---")

    try:
        sessions_with_reports = db.session.execute(
            db.select(Sessions)
            .options(db.joinedload(Sessions.report)) 
            .filter(
                Sessions.user_id == user_id,
                not_(Sessions.statut == 'pending')
            )
            .order_by(Sessions.date_entretien.desc())
        ).scalars().unique().all() 

        sessions_data = []
        for session in sessions_with_reports:
            sessions_data.append({
                "id": session.id,
                "date_entretien": session.date_entretien.isoformat(),
                "poste_vise": session.poste_vise,
                "statut": session.statut,
                "global_score": session.report.note_globale if session.report else None
            })
        
        print(f"-> {len(sessions_data)} sessions d'historique trouvées pour l'utilisateur {user_id}.")
        return jsonify(sessions_data), 200

    except Exception as e:
        print(f"!!! ERREUR DANS /api/sessions/history: {e}")
        return jsonify({"msg": "Erreur interne du serveur"}), 500
        

@session_bp.route('/api/session/<int:session_id>/submit', methods=['POST'])
@jwt_required()
def submit_session(session_id):
    """
    Finalise une session d'entretien. Le statut passe à 'file_uploaded'.
    Cette action est définitive.
    """
    claims = get_jwt()
    user_id = claims.get('user_id')

    session = db.session.get(Sessions, session_id)
    if not session or session.user_id != user_id:
        return jsonify({"msg": "Session non trouvée ou accès non autorisé."}), 404

    if session.tentatives_realisees == 0:
        return jsonify({"msg": "Vous ne pouvez pas soumettre un entretien sans avoir fait au moins une tentative."}), 400
        
    if session.statut != 'pending':
        return jsonify({"msg": "Cet entretien a déjà été soumis."}), 409

    session.statut = 'file_uploaded'
    db.session.commit()

    return jsonify({"msg": "Entretien soumis avec succès pour analyse."}), 200


# ===================================================================
# SECTION 3 : ROUTES PARTAGÉES ET RESSOURCES SPÉCIFIQUES
# ===================================================================

@session_bp.route('/api/session/<int:session_id>', methods=['GET', 'DELETE'])
@jwt_required()
def handle_single_session(session_id):
    """
    [Partagé] Gère les opérations sur une session unique.
    - GET: Récupère les détails (pour le lecteur vidéo).
    - DELETE: Supprime une session.
    """
    claims = get_jwt()
    user_id = claims.get('user_id')
    user_role = claims.get('role')

    session = db.session.get(Sessions, session_id)
    if not session:
        return jsonify({"msg": "Session non trouvée."}), 404

    is_candidat_owner = (session.user_id == user_id)
    is_recruiter_owner = (session.recruteur_id == user_id)
    is_admin = (user_role == 'admin')
    
    if not (is_candidat_owner or is_recruiter_owner or is_admin):
        return jsonify({"msg": "Accès non autorisé à cette session."}), 403

    if request.method == 'GET':
        return jsonify({
            "id": session.id,
            "date_entretien": session.date_entretien.strftime("%d/%m/%Y à %H:%M"),
            "video_path": session.fichier_video,
            "audio_path": session.fichier_audio,
            "poste_vise": session.poste_vise,
            "statut": session.statut,
            "nombre_tentatives": session.nombre_tentatives,
            "tentatives_realisees": session.tentatives_realisees
        }), 200

    if request.method == 'DELETE':
        if not (is_recruiter_owner or is_admin):
             return jsonify({"msg": "Seul le créateur ou un admin peut supprimer cette session."}), 403
        
        db.session.delete(session)
        db.session.commit()
        return jsonify({"msg": f"Session {session_id} supprimée avec succès."}), 200


@session_bp.route('/api/session/<int:session_id>/questions', methods=['GET'])
@jwt_required()
def get_session_questions(session_id):
    claims = get_jwt()
    user_id = claims.get('user_id')

    session = db.session.get(Sessions, session_id)
    if not session or session.user_id != user_id:
        return jsonify({"msg": "Session non trouvée ou accès non autorisé."}), 404
        
    if not session.questions_ids:
        return jsonify({"msg": "Aucune question n'a été assignée à cet entretien."}), 404

    questions = db.session.execute(
        db.select(Questions).filter(Questions.id.in_(session.questions_ids))
    ).scalars().all()
    
    questions_map = {q.id: q for q in questions}
    sorted_questions = [questions_map[id] for id in session.questions_ids if id in questions_map]

    questions_data = [{
        "id": q.id,
        "intitule": q.intitule,
        "category": q.category
    } for q in sorted_questions]

    return jsonify(questions_data)


@session_bp.route('/media/<path:user_path>')
@jwt_required(locations=["cookies", "query_string"]) 
def serve_media(user_path):
    """
    Sert un fichier média depuis le dossier d'uploads.
    'user_path' est le chemin stocké en BDD, ex: "3/fichier.webm".
    """
    # 1. Définir le chemin absolu du dossier qui contient TOUS les uploads.
    upload_folder_absolute = os.path.join(current_app.root_path, 'data', 'uploads')
    
    print(f"--- SERVE MEDIA ---")
    print(f"Dossier de base des uploads : {upload_folder_absolute}")
    print(f"Chemin de fichier demandé : {user_path}")
    
    # 2. send_from_directory va chercher 'user_path' à l'intérieur de 'upload_folder_absolute'.
    #    Exemple: /.../backend/data/uploads/ + 3/fichier.webm
    try:
        return send_from_directory(upload_folder_absolute, user_path, as_attachment=False)
    except FileNotFoundError:
        return jsonify({"msg": "Fichier non trouvé sur le serveur."}), 404
    

