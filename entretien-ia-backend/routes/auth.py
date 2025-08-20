from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, decode_token
from services import auth_service, email_service
from database.models import Users, db
from datetime import timedelta

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not all(key in data for key in ['nom', 'email', 'password']):
        return jsonify({"msg": "Données manquantes : 'nom', 'email' et 'password' sont requis."}), 400

    user = auth_service.register_user(
        nom=data['nom'],
        email=data['email'],
        password=data['password'],
        role=data.get('role', 'candidat'),
        must_change_password=False 
    )

    if user is None:
        return jsonify({"msg": "Un utilisateur avec cet email existe déjà."}), 409  

    return jsonify({"msg": f"Utilisateur '{user.nom}' créé avec succès."}), 201  

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not all(key in data for key in ['email', 'password']):
        return jsonify({"msg": "Données manquantes : 'email' et 'password' sont requis."}), 400
    
    user = auth_service.authenticate_user(email=data['email'], password=data['password'])
    
    if not user:
        return jsonify({"msg": "Email ou mot de passe incorrect."}), 401  
        
    additional_claims = {
        "user_id": user.id,
        "nom": user.nom,
        "email": user.email,
        "role": user.role,
        "doit_changer_mdp": user.doit_changer_mdp
    }
    
    access_token = create_access_token(identity=user.email, additional_claims=additional_claims)
    
    return jsonify(access_token=access_token, user_info=additional_claims), 200


@auth_bp.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"msg": "Email manquant."}), 400

    print(f"--- DÉBUT DE LA DEMANDE DE RÉINITIALISATION POUR : {email} ---")
    
    user = db.session.execute(
        db.select(Users).filter(Users.email.ilike(email))
    ).scalar_one_or_none()
    
    if user:
        print(f"-> SUCCÈS : Utilisateur trouvé (ID: {user.id}, Email: {user.email}).")
        
        print("-> Génération du token de réinitialisation...")
        reset_token = create_access_token(identity=user.email, expires_delta=timedelta(minutes=30))
        
        print("-> Appel du service d'envoi d'e-mail...")
        email_service.send_password_reset_email(user, reset_token)

    else:
        print(f"-> ECHEC : Aucun utilisateur trouvé avec l'email '{email}'.")
    
    print("--- FIN DE LA DEMANDE. Envoi de la réponse générique au client. ---")
    return jsonify({"msg": "Si un compte est associé à cet email, les instructions de réinitialisation ont été envoyées."}), 200


@auth_bp.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')

    if not token or not new_password:
        return jsonify({"msg": "Token ou nouveau mot de passe manquant."}), 400

    try:
        # On décode le token pour récupérer l'identité (l'email)
        decoded_token = decode_token(token)
        user_email = decoded_token['sub']
        
        user = db.session.execute(db.select(Users).filter_by(email=user_email)).scalar_one_or_none()
        if not user:
            return jsonify({"msg": "Utilisateur non trouvé."}), 404
            
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({"msg": "Mot de passe mis à jour avec succès. Vous pouvez maintenant vous connecter."}), 200

    except Exception as e:
        print(f"Erreur de réinitialisation de mot de passe : {e}")
        return jsonify({"msg": "Le lien de réinitialisation est invalide ou a expiré."}), 401