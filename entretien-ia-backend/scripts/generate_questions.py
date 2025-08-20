import json
import random
import os

NUM_QUESTIONS = 1000
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUTPUT_FILENAME = os.path.join(BASE_DIR, 'data', 'datasets', 'questions_1000.json')


CATEGORIES = {
    "Communication": ["communication", "présentation", "feedback"],
    "Résolution de problèmes": ["résolution", "problèmes", "analyse", "diagnostic"],
    "Leadership": ["leadership", "management", "décision", "vision"],
    "Travail d'équipe": ["équipe", "collaboration", "conflit", "synergie"],
    "Adaptabilité": ["adaptabilité", "changement", "flexibilité", "agilité"],
    "Gestion du stress": ["stress", "pression", "délai", "résilience"],
    "Culture d'entreprise": ["culture", "valeurs", "environnement", "éthique"],
    "Connaissances Techniques": ["technique", "compétences", "expertise", "architecture"],
    "Initiative & Proactivité": ["initiative", "proactivité", "autonomie", "innovation"],
    "Organisation": ["organisation", "planification", "priorisation", "gestion du temps"]
}

ROLES = [
    "Développeur Fullstack", "Développeur IA", "Développeur Mobile", "Ingénieur DevOps",
    "Data Scientist", "Chef de Projet Technique", "Product Owner", "Spécialiste SEO",
    "Commercial B2B", "Account Manager", "Responsable RH", "Contrôleur de Gestion",
    "Architecte Cloud", "Ingénieur QA", "Designer UX/UI", "Responsable Marketing"
]

EXPERIENCES = ["débutant", "intermédiaire", "expert", "junior", "senior"]
DIFFICULTIES = ["Facile", "Moyenne", "Difficile"]
SOURCE_TYPES = ["STAR", "Situationnelle", "Comportementale", "Technique"]

TOPICS_TECH = ["une dette technique", "une migration de base de données", "un bug critique en production", "l'intégration d'une API", "l'optimisation des performances", "la sécurité d'une application"]
TOPICS_MANAGEMENT = ["un conflit au sein de l'équipe", "un client mécontent", "un changement de périmètre", "un délai serré", "une baisse de motivation", "le budget d'un projet"]
ALL_TOPICS = list(set(TOPICS_TECH + TOPICS_MANAGEMENT))

QUESTION_TEMPLATES = [
    "En tant que {role}, comment aborderiez-vous le problème de {topic} ?",
    "Décrivez une expérience en tant que {role} où vous avez dû gérer {topic}.",
    "Parlez-moi d'un projet significatif en tant que {role} impliquant {topic}.",
    "Quelle serait votre stratégie en tant que {role} pour améliorer {topic} ?",
    "Imaginez que vous êtes un {role} et que vous êtes confronté à {topic}. Que faites-vous ?",
    "Comment votre expérience de {role} vous a-t-elle préparé à gérer {topic} ?",
    "Quels sont les plus grands défis pour un {role} lorsqu'il s'agit de {topic} ?",
    "Donnez un exemple concret de la manière dont un {role} peut avoir un impact positif sur {topic}."
]

def generate_questions():
    """
    Génère un fichier JSON de questions uniques en combinant rôle, topic et template.
    """
    questions = []
    unique_questions = set()

    print(f"Début de la génération de {NUM_QUESTIONS} questions...")

    max_attempts = NUM_QUESTIONS * 50 # On peut réduire la marge, car on a beaucoup plus de combinaisons
    attempts = 0

    while len(questions) < NUM_QUESTIONS and attempts < max_attempts:
        attempts += 1
        
        # On choisit aléatoirement chaque composant de la question
        category = random.choice(list(CATEGORIES.keys()))
        role = random.choice(ROLES)
        topic = random.choice(ALL_TOPICS)
        template = random.choice(QUESTION_TEMPLATES)

        # On construit la question
        question_text = template.format(role=role, topic=topic)

        if question_text in unique_questions:
            continue
        unique_questions.add(question_text)

        ideal_answer_text = (
            f"La question évalue la compétence '{category}'. Un bon {role} répondrait en structurant son propos "
            f"autour d'une expérience concrète liée à '{topic}', démontrant sa maîtrise du sujet."
        )

        questions.append({
            "question": question_text,
            "category": category, "role": role,
            "experience": random.choice(EXPERIENCES), "difficulty": random.choice(DIFFICULTIES),
            "source_type": random.choice(SOURCE_TYPES), "ideal_answer": ideal_answer_text,
            "keywords": CATEGORIES[category]
        })

    os.makedirs(os.path.dirname(OUTPUT_FILENAME), exist_ok=True)
    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
        
    print("-" * 50)
    if len(questions) < NUM_QUESTIONS:
        print(f"AVERTISSEMENT: La génération s'est arrêtée prématurément.")
        print(f"Seulement {len(questions)} questions uniques ont pu être générées.")
    else:
        print(f"Génération terminée avec succès !")
        print(f"{len(questions)} questions uniques ont été générées.")
    
    print(f"Fichier sauvegardé dans : {OUTPUT_FILENAME}")
    print("-" * 50)

if __name__ == '__main__':
    generate_questions()