import ijson
from collections import defaultdict
import json

input_file = "./data/datasets/Interview Questions Dataset/archive/hr_interview_questions_dataset.json"
output_file = "./data/datasets/Interview Questions Dataset/archive/interview_balanced.json"

target_per_category = 200
max_total = 2000

category_buckets = defaultdict(list)

with open(input_file, "r", encoding="utf-8") as f:
    # ijson.items(f, 'item') itère sur chaque objet dans le tableau JSON principal
    parser = ijson.items(f, 'item')

    for q in parser:
        if not isinstance(q, dict):
            continue
        
        category = q.get("category", "Unknown")
        if len(category_buckets[category]) < target_per_category:
            category_buckets[category].append(q)

        total = sum(len(v) for v in category_buckets.values())
        if total >= max_total:
            break

# Fusionner toutes les questions sélectionnées
selected_questions = []
for cat, questions in category_buckets.items():
    selected_questions.extend(questions)

with open(output_file, "w", encoding="utf-8") as f_out:
    json.dump(selected_questions, f_out, indent=2, ensure_ascii=False)

print(f"Fichier généré : {output_file} avec {len(selected_questions)} questions.")
