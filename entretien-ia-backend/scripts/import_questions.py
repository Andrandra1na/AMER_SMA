import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from database.models import Questions

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

JSON_FILENAME = "../data/datasets/Interview Questions Dataset/archive/questions_de_base.json" 
JSON_FILE_PATH = os.path.join(BASE_DIR, 'data', JSON_FILENAME)


def import_questions():
    app = create_app()
    with app.app_context():
        print("Début de l'importation des questions par défaut...")
        print(f"Tentative de lecture du fichier : {JSON_FILE_PATH}") 

        if not os.path.exists(JSON_FILE_PATH):
            print(f"--- ERREUR FATALE ---")
            print(f"Fichier JSON non trouvé à l'emplacement calculé.")
            print("--------------------")
            return

        try:
            with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"--- ERREUR FATALE ---")
            print(f"Le fichier JSON '{JSON_FILENAME}' est mal formaté.")
            print(f"Erreur de décodage : {e}")
            print("Veuillez vérifier que le JSON est un tableau valide (commence par [ et finit par ]).")
            print("--------------------")
            return
            
        questions_added = 0
        questions_skipped = 0

        for q_data in questions_data:
            if 'question' not in q_data:
                print(f"AVERTISSEMENT: Un objet dans le JSON n'a pas de clé 'question'. Ignoré : {q_data}")
                continue

            existing_question = db.session.execute(
                db.select(Questions).filter_by(intitule=q_data['question'])
            ).scalar_one_or_none()

            if existing_question:
                questions_skipped += 1
                continue

            new_question = Questions(
                intitule=q_data.get('question'),
                category=q_data.get('category'),
                role_target=q_data.get('role'),
                difficulty=q_data.get('difficulty'),
                source_type=q_data.get('source_type'),
                ideal_answer=q_data.get('ideal_answer'),
                phase=q_data.get('phase'),
                experience_level=q_data.get('experience'),
                keywords=q_data.get('keywords'),
                recruteur_id=None 
            )
            
            db.session.add(new_question)
            questions_added += 1

        if questions_added > 0:
            db.session.commit()
            print(f"Terminé. {questions_added} nouvelles questions importées avec succès.")
        else:
            print("Aucune nouvelle question à importer.")
            
        if questions_skipped > 0:
            print(f"{questions_skipped} questions déjà existantes ont été ignorées pour éviter les doublons.")


if __name__ == '__main__':
    import_questions()