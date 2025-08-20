import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from services import storage_service
from database.models import Sessions, db

upload_bp = Blueprint('upload_bp', __name__)

@upload_bp.route('/api/upload/<int:session_id>', methods=['POST'])
@jwt_required()
def upload_file(session_id):
    claims = get_jwt()
    user_id = claims.get('user_id')
    
    session = db.session.get(Sessions, session_id)
    if not session or session.user_id != user_id:
        return jsonify({"msg": "Session non trouvée ou accès non autorisé."}), 404

    if session.tentatives_realisees >= session.nombre_tentatives:
        return jsonify({"msg": "Nombre maximum de tentatives atteint."}), 409

    file = request.files.get('file')
    events_json = request.form.get('events')
    if not file or not events_json:
        return jsonify({"msg": "Données manquantes."}), 400

    try:
        events = json.loads(events_json)
    except json.JSONDecodeError:
        return jsonify({"msg": "Format des événements invalide."}), 400

    old_file_path = session.fichier_video or session.fichier_audio
    if old_file_path:
        storage_service.delete_file(old_file_path)

    saved_path = storage_service.save_file(file, user_id)
    if not saved_path:
        return jsonify({"msg": "Erreur de sauvegarde."}), 500

    session.fichier_video = saved_path if saved_path.endswith(('.mp4', '.webm')) else None
    session.fichier_audio = saved_path if not session.fichier_video else None
    session.tentatives_realisees += 1
    session.events_timeline = events

    db.session.commit()
    
    return jsonify({
        "msg": "Tentative enregistrée avec succès.",
        "session_id": session.id,
        "tentatives_realisees": session.tentatives_realisees,
        "nombre_tentatives": session.nombre_tentatives
    }), 200