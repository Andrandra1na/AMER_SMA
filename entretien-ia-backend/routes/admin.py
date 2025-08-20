import os
from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt
from database.models import db, Users, Configurations, ProfilsPonderation
from services import auth_service 
from flask import send_file
from utils import test_runner_service
from services import export_service

admin_bp = Blueprint('admin_bp', __name__)

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

@admin_bp.route('/api/admin/users', methods=['GET'])
@admin_required()
def get_all_users():
    users = db.session.execute(db.select(Users).order_by(Users.id)).scalars().all()
    return jsonify([{
        "id": u.id, "nom": u.nom, "email": u.email,
        "role": u.role, "date_inscription": u.date_inscription.strftime("%d/%m/%Y")
    } for u in users])

@admin_bp.route('/api/admin/users', methods=['POST'])
@admin_required()
def create_user():
    data = request.get_json()
    if not all(k in data for k in ['nom', 'email', 'password', 'role']):
        return jsonify({"msg": "Données manquantes."}), 400
    
    user = auth_service.register_user(
        nom=data['nom'],
        email=data['email'],
        password=data['password'],
        role=data['role'],
        must_change_password=True
    )
    if user is None:
        return jsonify({"msg": "Cet email ou nom d'utilisateur est déjà pris."}), 409
    
    return jsonify({"msg": "Utilisateur créé avec succès."}), 201

@admin_bp.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@admin_required()
def update_user(user_id):
    user = db.session.get(Users, user_id)
    if not user:
        return jsonify({"msg": "Utilisateur non trouvé."}), 404
        
    data = request.get_json()
    user.nom = data.get('nom', user.nom)
    user.email = data.get('email', user.email)
    user.role = data.get('role', user.role)
    
    # Logique de réinitialisation du mot de passe
    if 'password' in data and data['password']:
        user.set_password(data['password'])
        print(f"Le mot de passe de l'utilisateur {user_id} a été mis à jour.")
    
    db.session.commit()
    return jsonify({"msg": "Utilisateur mis à jour avec succès."})

@admin_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required()
def delete_user(user_id):
    claims = get_jwt()
    # Sécurité : un admin ne peut pas se supprimer lui-même
    if claims.get('user_id') == user_id:
        return jsonify({"msg": "Vous ne pouvez pas supprimer votre propre compte."}), 403
        
    user = db.session.get(Users, user_id)
    if not user:
        return jsonify({"msg": "Utilisateur non trouvé."}), 404
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({"msg": "Utilisateur supprimé avec succès."})


@admin_bp.route('/api/admin/export/preview', methods=['GET'])
@admin_required()
def preview_export_data():
    """
    Retourne les données filtrées en JSON pour l'aperçu dans le tableau frontend.
    """
    # On récupère les filtres depuis les arguments de l'URL (ex: ?start_date=...)
    filters = request.args.to_dict()
    data = export_service.get_export_data(filters)
    return jsonify(data)

@admin_bp.route('/api/admin/export/csv', methods=['GET'])
@admin_required()
def export_data_csv():
    filters = request.args.to_dict()
    data = export_service.get_export_data(filters)
    
    csv_file = export_service.export_to_csv(data)
    if csv_file is None:
        return jsonify({"msg": "Aucune donnée à exporter."}), 404

    return send_file(
        csv_file,
        mimetype='text/csv',
        as_attachment=True,
        download_name='export_entretiens.csv'
    )
    

@admin_bp.route('/api/admin/weights', methods=['GET'])
@admin_required()
def get_weights():
    from agents.RapportAgent import RapportAgent
    temp_agent = RapportAgent()
    return jsonify(temp_agent.weights)

@admin_bp.route('/api/admin/weights', methods=['POST'])
@admin_required()
def update_weights():
    new_weights = request.get_json()
    if not new_weights:
        return jsonify({"msg": "Aucune donnée fournie."}), 400

    # Sécurité : on vérifie que la somme est proche de 1 (100%)
    if abs(sum(new_weights.values()) - 1.0) > 0.01:
        return jsonify({"msg": "La somme des poids doit être égale à 1.0 (100%)."}), 400

    try:
        for key, value in new_weights.items():
            config_key = f"poids_{key}"
            config_entry = db.session.execute(
                db.select(Configurations).filter_by(cle=config_key)
            ).scalar_one_or_none()
            
            if config_entry:
                config_entry.valeur = str(value)
            else:
                new_config = Configurations(cle=config_key, valeur=str(value))
                db.session.add(new_config)
        
        db.session.commit()
        return jsonify({"msg": "Pondérations mises à jour avec succès."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Erreur lors de la mise à jour : {e}"}), 500


@admin_bp.route('/api/admin/profiles', methods=['GET'])
@admin_required()
def get_profiles_alias():
    """
    [Admin] C'est un alias pour /api/admin/weights.
    Elle appelle la même logique pour être compatible avec l'appel frontend existant.
    """
    # On appelle simplement la fonction de la route principale pour ne pas dupliquer le code.
    return get_profiles()

# --- ROUTES POUR LA GESTION DES PROFILS DE PONDÉRATION ---
@admin_bp.route('/api/admin/profiles', methods=['GET'])
@admin_required()
def get_profiles():
    profiles = db.session.execute(db.select(ProfilsPonderation)).scalars().all()
    return jsonify([{"id": p.id, "nom_profil": p.nom_profil, "description": p.description, "poids": p.poids} for p in profiles])

@admin_bp.route('/api/admin/profiles', methods=['POST'])
@admin_required()
def create_profile():
    data = request.get_json()
    new_profile = ProfilsPonderation(nom_profil=data['nom_profil'], description=data.get('description'), poids=data['poids'])
    db.session.add(new_profile)
    db.session.commit()
    return jsonify({"msg": "Profil créé."}), 201

@admin_bp.route('/api/admin/profiles/<int:profile_id>', methods=['PUT'])
@admin_required()
def update_profile(profile_id):
    profile = db.session.get(ProfilsPonderation, profile_id)
    if not profile: return jsonify({"msg": "Profil non trouvé."}), 404
    data = request.get_json()
    profile.nom_profil = data.get('nom_profil', profile.nom_profil)
    profile.description = data.get('description', profile.description)
    profile.poids = data.get('poids', profile.poids)
    db.session.commit()
    return jsonify({"msg": "Profil mis à jour."})

@admin_bp.route('/api/admin/profiles/<int:profile_id>', methods=['DELETE'])
@admin_required()
def delete_profile(profile_id):
    profile = db.session.get(ProfilsPonderation, profile_id)
    if not profile: return jsonify({"msg": "Profil non trouvé."}), 404
    db.session.delete(profile)
    db.session.commit()
    return jsonify({"msg": "Profil supprimé."})

@admin_bp.route('/api/admin/system-status/run-tests', methods=['POST'])
@admin_required()
def run_system_tests():
    report = test_runner_service.run_tests_and_generate_reports()
    if not report:
        return jsonify({"msg": "Erreur lors de l'exécution des tests."}), 500
    return jsonify(report)

# Route pour récupérer le dernier rapport JSON
@admin_bp.route('/api/admin/system-status/latest', methods=['GET'])
@admin_required()
def get_latest_system_status():
    report = test_runner_service.get_latest_json_report()
    if not report:
        return jsonify({"msg": "Aucun rapport de test n'a encore été généré."}), 404
    return jsonify(report)

# Route pour servir le rapport HTML
@admin_bp.route('/api/admin/system-status/html-report', methods=['GET'])
@admin_required()
def get_html_report():
    report_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'tests')
    return send_from_directory(report_dir, 'report.html')