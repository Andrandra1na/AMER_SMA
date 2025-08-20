import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.models import db, ProfilsPonderation

PROFILES_DATA = [
    # --- PÔLE TECHNIQUE & EXPERTISE ---
    {
        "nom_profil": "Profil \"Expert Technique\"",
        "description": "Pour Développeurs, Ingénieurs, Data Scientists. La précision et la profondeur des connaissances sont reines.",
        "poids": {'relevance': 50, 'clarity': 30, 'fluency': 10, 'engagement': 10}
    },
    {
        "nom_profil": "Profil \"Support Technique & Fiabilité\"",
        "description": "Pour les techniciens de support, les administrateurs système. Calme, clarté et précision sous pression.",
        "poids": {'clarity': 40, 'engagement': 30, 'relevance': 20, 'fluency': 10}
    },
    {
        "nom_profil": "Profil \"Recherche & Développement\"",
        "description": "Pour les chercheurs et innovateurs. Valorise la capacité à structurer une pensée complexe.",
        "poids": {'relevance': 40, 'clarity': 40, 'engagement': 10, 'fluency': 10}
    },
    
    # --- PÔLE MANAGEMENT & STRATÉGIE ---
    {
        "nom_profil": "Profil \"Manager de Proximité\"",
        "description": "Pour les Team Leaders, Chefs de projet. Met l'accent sur la clarté des instructions et la motivation.",
        "poids": {'clarity': 40, 'engagement': 35, 'relevance': 15, 'fluency': 10}
    },
    {
        "nom_profil": "Profil \"Leader Stratégique\"",
        "description": "Pour les Directeurs, C-Levels. Capacité à communiquer une vision et à inspirer confiance.",
        "poids": {'engagement': 40, 'clarity': 30, 'relevance': 20, 'fluency': 10}
    },

    # --- PÔLE RELATION CLIENT & CROISSANCE ---
    {
        "nom_profil": "Profil \"Commercial / Vente\"",
        "description": "Pour les commerciaux. Le dynamisme, la persuasion et l'énergie sont clés.",
        "poids": {'engagement': 45, 'fluency': 30, 'clarity': 15, 'relevance': 10}
    },
    {
        "nom_profil": "Profil \"Gestionnaire de Comptes\"",
        "description": "Pour la gestion de comptes existants. L'écoute, le calme et la clarté sont essentiels.",
        "poids": {'clarity': 35, 'engagement': 30, 'relevance': 20, 'fluency': 15}
    },
    {
        "nom_profil": "Profil \"Marketing & Communication\"",
        "description": "Pour les créatifs et communicants. On cherche de l'énergie, de la clarté et du storytelling.",
        "poids": {'engagement': 40, 'clarity': 30, 'fluency': 20, 'relevance': 10}
    },

    # --- PÔLE OPÉRATIONS & SUPPORT ---
    {
        "nom_profil": "Profil \"Opérationnel & Process\"",
        "description": "Pour les fonctions support (RH, Finance). La rigueur, la clarté et la fiabilité sont primordiales.",
        "poids": {'clarity': 45, 'relevance': 30, 'engagement': 15, 'fluency': 10}
    },
    {
        "nom_profil": "Profil \"Formateur / Pédagogue\"",
        "description": "Pour les formateurs. La capacité à simplifier le complexe et à engager est essentielle.",
        "poids": {'clarity': 50, 'engagement': 30, 'fluency': 10, 'relevance': 10}
    },
    
    # --- PÔLE JUNIOR & POTENTIEL ---
    {
        "nom_profil": "Profil \"Jeune Potentiel\"",
        "description": "Pour les juniors, stagiaires. On cherche avant tout la motivation et la capacité à structurer une pensée.",
        "poids": {'engagement': 40, 'relevance': 30, 'clarity': 20, 'fluency': 10}
    },
    {
        "nom_profil": "Profil \"Polyvalent\" (Par défaut)",
        "description": "Un profil équilibré pour les postes non spécialisés ou comme point de départ.",
        "poids": {'relevance': 25, 'clarity': 25, 'fluency': 25, 'engagement': 25}
    }
]

def populate_profiles():
    app = create_app()
    with app.app_context():
        print("Début du peuplement de la table 'profils_ponderation'...")
        
        profiles_added = 0
        for profile_data in PROFILES_DATA:
            existing_profile = db.session.execute(
                db.select(ProfilsPonderation).filter_by(nom_profil=profile_data["nom_profil"])
            ).scalar_one_or_none()
            
            if existing_profile:
                print(f"Mise à jour du profil : '{profile_data['nom_profil']}'")
                existing_profile.description = profile_data["description"]
                existing_profile.poids = profile_data["poids"]
            else:
                print(f"Création du profil : '{profile_data['nom_profil']}'")
                new_profile = ProfilsPonderation(
                    nom_profil=profile_data["nom_profil"],
                    description=profile_data["description"],
                    poids=profile_data["poids"]
                )
                db.session.add(new_profile)
                profiles_added += 1
        
        db.session.commit()
        
        print("-" * 50)
        if profiles_added > 0:
            print(f"{profiles_added} nouveaux profils ont été ajoutés.")
        print("Le peuplement de la table des profils est terminé.")
        print("-" * 50)


if __name__ == '__main__':
    populate_profiles()