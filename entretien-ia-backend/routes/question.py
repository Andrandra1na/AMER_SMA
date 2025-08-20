from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from database.models import db, Questions, Users
from sqlalchemy import or_

question_bp = Blueprint('question_bp', __name__)

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

def admin_required():
    def wrapper(fn):
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') != 'admin': return jsonify({"msg": "Action réservée aux administrateurs."}), 403
            return fn(*args, **kwargs)
        decorator.__name__ = f"admin_wrapper_{fn.__name__}"
        return decorator
    return wrapper

@question_bp.route('/api/recruiter/questions', methods=['GET'])
@recruiter_or_admin_required()
def get_my_questions():
    claims = get_jwt()
    recruteur_id = claims.get('user_id')
    questions = db.session.execute(db.select(Questions).filter_by(recruteur_id=recruteur_id).order_by(Questions.id.desc())).scalars().all()
    return jsonify([{
        "id": q.id, "intitule": q.intitule, "category": q.category,
        "role_target": q.role_target, "difficulty": q.difficulty,
        "source_type": q.source_type, "ideal_answer": q.ideal_answer,
        "experience_level": q.experience_level, "keywords": q.keywords,
        "signalement_admin": q.signalement_admin,
        "commentaire_admin": q.commentaire_admin
    } for q in questions])

@question_bp.route('/api/recruiter/questions', methods=['POST'])
@recruiter_or_admin_required()
def create_question():
    claims = get_jwt()
    recruteur_id = claims.get('user_id')
    data = request.get_json()
    if not data or not data.get('intitule'):
        return jsonify({"msg": "L'intitulé de la question est requis."}), 400
    
    # On gère les keywords, qui arrivent comme une chaîne et doivent être une liste
    keywords = [k.strip() for k in data.get('keywords', '').split(',') if k.strip()]

    new_question = Questions(
        intitule=data['intitule'],
        category=data.get('category'),
        role_target=data.get('role_target'),
        difficulty=data.get('difficulty'),
        source_type=data.get('source_type'),
        ideal_answer=data.get('ideal_answer'),
        experience_level=data.get('experience_level'),
        keywords=keywords,
        recruteur_id=recruteur_id
    )
    db.session.add(new_question)
    db.session.commit()
    return jsonify({"msg": "Question créée avec succès."}), 201

@question_bp.route('/api/recruiter/questions/<int:question_id>', methods=['PUT'])
@recruiter_or_admin_required()
def update_question(question_id):
    claims = get_jwt()
    recruteur_id = claims.get('user_id')
    question = db.session.get(Questions, question_id)
    if not question or question.recruteur_id != recruteur_id:
        return jsonify({"msg": "Question non trouvée ou non autorisée."}), 404
        
    data = request.get_json()
    keywords = [k.strip() for k in data.get('keywords', '').split(',') if k.strip()]

    question.intitule = data.get('intitule', question.intitule)
    question.category = data.get('category', question.category)
    question.role_target = data.get('role_target', question.role_target)
    question.difficulty = data.get('difficulty', question.difficulty)
    question.source_type = data.get('source_type', question.source_type)
    question.ideal_answer = data.get('ideal_answer', question.ideal_answer)
    question.experience_level = data.get('experience_level', question.experience_level)
    question.keywords = keywords
    
    db.session.commit()
    return jsonify({"msg": "Question mise à jour avec succès."})

@question_bp.route('/api/recruiter/questions/<int:question_id>', methods=['DELETE'])
@recruiter_or_admin_required()
def delete_question(question_id):
    claims = get_jwt()
    recruteur_id = claims.get('user_id')
    question = db.session.get(Questions, question_id)
    if not question or question.recruteur_id != recruteur_id:
        return jsonify({"msg": "Question non trouvée ou non autorisée."}), 404

    db.session.delete(question)
    db.session.commit()
    return jsonify({"msg": "Question supprimée avec succès."})


@question_bp.route('/api/admin/questions/all', methods=['GET'])
@admin_required()
def get_all_questions():
    query_results = db.session.execute(
        db.select(Questions, Users.nom.label("nom_recruteur"))
        .outerjoin(Users, Questions.recruteur_id == Users.id)
        .order_by(Questions.id.desc())
    ).all()

    questions_data = []
    for question, nom_recruteur in query_results:
        questions_data.append({
            "id": question.id,
            "intitule": question.intitule,
            "category": question.category,
            "recruteur_id": question.recruteur_id,
            "auteur": nom_recruteur or "Par Défaut (Admin)",
            "signalement_admin": question.signalement_admin,
            "commentaire_admin": question.commentaire_admin,
            "phase": question.phase,
            "role_target": question.role_target,
            "difficulty": question.difficulty,
            "experience_level": question.experience_level
        })
    return jsonify(questions_data)

@question_bp.route('/api/admin/questions/signal/<int:question_id>', methods=['POST'])
@admin_required()
def signal_question(question_id):
    question = db.session.get(Questions, question_id)
    if not question:
        return jsonify({"msg": "Question non trouvée."}), 404
        
    data = request.get_json()
    signalement = data.get('signalement') 
    commentaire = data.get('commentaire', '')

    if signalement is None:
        return jsonify({"msg": "Le statut de signalement (true/false) est requis."}), 400

    question.signalement_admin = signalement
    question.commentaire_admin = commentaire if signalement else None 
    
    db.session.commit()
    return jsonify({"msg": "Statut de la question mis à jour avec succès."})


@question_bp.route('/api/questions/all', methods=['GET'])
@recruiter_or_admin_required() # Accessible par les recruteurs et les admins
def get_all_questions_for_inspiration():
    """
    Retourne TOUTES les questions de la plateforme en lecture seule,
    avec le nom de l'auteur.
    """
    query_results = db.session.execute(
        db.select(Questions, Users.nom.label("nom_recruteur"))
        .outerjoin(Users, Questions.recruteur_id == Users.id)
        .order_by(Questions.id.desc())
    ).all()

    questions_data = []
    for question, nom_recruteur in query_results:
        questions_data.append({
            "id": question.id,
            "intitule": question.intitule,
            "category": question.category,
            "auteur": nom_recruteur or "Par Défaut",
            "signalement_admin": question.signalement_admin,
            "role_target": question.role_target,
            "difficulty": question.difficulty,
            "source_type": question.source_type,
            "experience_level": question.experience_level
        })
    return jsonify(questions_data)

# --- NOUVELLES ROUTES POUR L'ADMIN (pour gérer les questions par défaut) ---

@question_bp.route('/api/admin/questions/default', methods=['POST'])
@admin_required()
def create_default_question():
    """[Admin] Crée une nouvelle question par défaut (sans recruteur_id)."""
    data = request.get_json()
    # ... (logique pour créer une question avec recruteur_id = NULL)
    new_question = Questions(
        intitule=data['intitule'],
        category=data['category'],
        # ... autres champs
        recruteur_id=None # La clé est ici
    )
    db.session.add(new_question)
    db.session.commit()
    return jsonify({"msg": "Question par défaut créée."}), 201

@question_bp.route('/api/admin/questions/default/<int:question_id>', methods=['PUT', 'DELETE'])
@admin_required()
def handle_single_default_question(question_id):
    """[Admin] Modifie ou supprime une question par défaut."""
    question = db.session.get(Questions, question_id)
    if not question:
        return jsonify({"msg": "Question non trouvée."}), 404
    
    # Sécurité : on vérifie que c'est bien une question par défaut
    if question.recruteur_id is not None:
        return jsonify({"msg": "Action non autorisée : cette question appartient à un recruteur."}), 403

    if request.method == 'PUT':
        data = request.get_json()
        # ... (logique de mise à jour)
        question.intitule = data.get('intitule', question.intitule)
        question.category = data.get('category', question.category)
        db.session.commit()
        return jsonify({"msg": "Question par défaut mise à jour."})

    if request.method == 'DELETE':
        db.session.delete(question)
        db.session.commit()
        return jsonify({"msg": "Question par défaut supprimée."})