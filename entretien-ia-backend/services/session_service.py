import random
from sqlalchemy.sql.expression import func
from sqlalchemy import or_
from database.models import db, Sessions, Questions, Users

def get_competencies_for_poste(poste_vise: str) -> list:
    """
    Découvre les compétences (catégories) pertinentes pour un poste en interrogeant la BDD.
    """
    print(f"Découverte des compétences pour le poste : '{poste_vise}'")
    competencies_query = db.select(Questions.category).distinct().filter(
        Questions.role_target.ilike(f'%{poste_vise}%')
    )
    competences = db.session.execute(competencies_query).scalars().all()
    
    if not competences:
        print("-> Aucune compétence spécifique trouvée. Utilisation des compétences par défaut.")
        return ["Communication", "Résolution de problèmes", "Travail d'équipe", "Adaptabilité"]
        
    print(f"-> Compétences découvertes : {competences}")
    return competences


def select_questions_for_session(poste_vise: str) -> list:
    """
    Construit un questionnaire ordonné.
    Étape 1: Sélectionne les questions de catégories simples.
    Étape 2: Sélectionne les questions de compétences.
    Étape 3: Assemble le tout dans l'ordre.
    """
    interview_schema = [
        {'category': 'Introduction', 'count': 1},
        {'category': 'Motivation', 'count': 1},
        {'category': 'Compétences', 'count': 4},
        {'category': 'Connaissance de soi', 'count': 2},
        {'category': 'Curiosité', 'count': 1},
    ]
    
    print(f"Construction d'un entretien par catégories pour '{poste_vise}'")
    
    # On utilise un dictionnaire pour stocker les "paniers" de questions
    question_baskets = {step['category']: [] for step in interview_schema}
    used_question_ids = set()

    # --- ÉTAPE 1: ON REMPLIT LES PANIERS DES CATÉGORIES SIMPLES ---
    simple_categories = ['Introduction', 'Motivation', 'Connaissance de soi', 'Curiosité']
    
    for step in interview_schema:
        category = step['category']
        count = step['count']

        if category in simple_categories:
            print(f"--- Traitement Catégorie: {category} (Besoin de {count} question(s)) ---")
            
            query = db.select(Questions.id).filter(
                Questions.category == category,
                Questions.id.notin_(used_question_ids)
            ).order_by(func.random()).limit(count)
            
            ids_for_step = db.session.execute(query).scalars().all()
            
            # On met les IDs trouvés dans le bon panier
            question_baskets[category].extend(ids_for_step)
            used_question_ids.update(ids_for_step)

    # --- ÉTAPE 2: ON REMPLIT LE PANIER SPÉCIAL "COMPÉTENCES" ---
    print(f"\n--- Traitement Catégorie: Compétences (Besoin de 4 question(s)) ---")
    competencies_for_poste = get_competencies_for_poste(poste_vise)
    num_competences_needed = 4
    panier_competences = set()

    # Priorité 1: Spécifiques (poste + compétence)
    query_specific = db.select(Questions.id).filter(
        Questions.category.in_(competencies_for_poste),
        Questions.role_target.ilike(f'%{poste_vise}%'),
        Questions.id.notin_(used_question_ids)
    )
    specific_ids = db.session.execute(query_specific).scalars().all()
    panier_competences.update(specific_ids)
    
    # Priorité 2: Génériques de compétence
    needed = num_competences_needed - len(panier_competences)
    if needed > 0:
        query_generic = db.select(Questions.id).filter(
            Questions.category.in_(competencies_for_poste),
            or_(Questions.role_target.is_(None), Questions.role_target == ''),
            Questions.id.notin_(used_question_ids.union(panier_competences))
        ).order_by(func.random()).limit(needed)
        
        generic_ids = db.session.execute(query_generic).scalars().all()
        panier_competences.update(generic_ids)

    # On met le résultat dans le panier "Compétences"
    question_baskets['Compétences'] = list(panier_competences)[:num_competences_needed]
    used_question_ids.update(question_baskets['Compétences'])


    # --- ÉTAPE 3: ASSEMBLAGE FINAL ORDONNÉ ---
    final_ordered_list = []
    for step in interview_schema:
        category = step['category']
        final_ordered_list.extend(question_baskets[category])

    # On mélange uniquement les questions à l'intérieur du panier "Compétences"
    competence_part_start = len(question_baskets['Introduction']) + len(question_baskets['Motivation'])
    competence_part_end = competence_part_start + len(question_baskets['Compétences'])
    competence_sublist = final_ordered_list[competence_part_start:competence_part_end]
    random.shuffle(competence_sublist)
    final_ordered_list[competence_part_start:competence_part_end] = competence_sublist


    print(f"\nQuestionnaire final assemblé avec {len(final_ordered_list)} questions : {final_ordered_list}")
    return final_ordered_list


def create_session_for_recruiter(recruteur_id, user_id, poste_vise, profil_ponderation_id, competences):
    """
    Fonction principale qui valide et crée la session.
    """
    candidat = db.session.get(Users, user_id)
    if not candidat or candidat.role != 'candidat':
        raise ValueError("L'ID du candidat fourni n'est pas valide.")

    try:
        questions_ids = select_questions_for_session(poste_vise)
    except Exception as e:
        raise e

    new_session = Sessions(
        recruteur_id=recruteur_id, user_id=user_id, poste_vise=poste_vise,
        profil_ponderation_id=profil_ponderation_id,
        questions_ids=questions_ids, statut='pending'
    )
    db.session.add(new_session)
    db.session.commit()
    
    print(f"Session {new_session.id} créée avec succès pour le candidat {user_id} par le recruteur {recruteur_id}.")
    
    return new_session


