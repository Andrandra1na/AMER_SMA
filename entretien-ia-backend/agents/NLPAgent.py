import os
import language_tool_python
from faster_whisper import WhisperModel
from sentence_transformers import SentenceTransformer, util

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

def format_docs(docs):
    """
    Fonction simple pour extraire le contenu textuel d'une liste de documents.
    """
    return "\n\n".join(doc.page_content for doc in docs)


class NLPAgent:
    """
    Agent spécialisé dans le traitement du langage naturel.
    Gère la transcription, l'analyse grammaticale, la similarité sémantique (simple)
    et la pertinence factuelle (RAG).
    """
    def __init__(self, model_size="small"):
        print(f"Initialisation du NLPAgent avec le modèle Whisper '{model_size}'...")
        # 1. Modèle de transcription
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

        # 2. Modèles pour les autres analyses (initialisés de manière paresseuse)
        self.grammar_tool = None
        self.semantic_model = None
        self.rag_chain = None
        
        # 3. Noms des modèles et chemins de configuration
        self.grammar_tool_lang = 'fr-FR'
        self.semantic_model_name = 'paraphrase-multilingual-MiniLM-L12-v2'
        self.embedding_model_name_rag = 'paraphrase-multilingual-MiniLM-L12-v2'
        self.llm_model_name_rag = "google/flan-t5-base" # Utilisation du modèle 'base' plus performant
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.vector_db_path = os.path.join(base_dir, '..', 'data', 'vector_db')
        
        print("NLPAgent prêt (modèles annexes non encore chargés).")

    # --- MÉTHODES D'INITIALISATION PARESSEUSE ---

    def _initialize_grammar_tool(self):
        if self.grammar_tool: return
        print("Initialisation de LanguageTool (à la première demande)...")
        try:
            self.grammar_tool = language_tool_python.LanguageTool(self.grammar_tool_lang)
            print("LanguageTool prêt.")
        except Exception as e:
            print(f"AVERTISSEMENT: Échec de l'initialisation de LanguageTool: {e}")

    def _initialize_semantic_model(self):
        if self.semantic_model: return
        print(f"Chargement du modèle sémantique '{self.semantic_model_name}'...")
        try:
            self.semantic_model = SentenceTransformer(self.semantic_model_name)
            print("Modèle sémantique prêt.")
        except Exception as e:
            print(f"ERREUR: Impossible de charger le modèle sémantique: {e}")

    def _initialize_rag_chain(self):
        """Initialise le pipeline RAG complet à la première demande."""
        if self.rag_chain: return
        
        print(f"Initialisation du pipeline RAG avec le modèle '{self.llm_model_name_rag}'...")
        try:
            if not os.path.exists(self.vector_db_path):
                raise FileNotFoundError(f"Base de données vectorielle non trouvée. Veuillez lancer 'scripts/create_vector_db.py'.")
            
            embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model_name_rag)
            vector_db = FAISS.load_local(self.vector_db_path, embeddings, allow_dangerous_deserialization=True)
            retriever = vector_db.as_retriever(search_kwargs={"k": 2})

            tokenizer = AutoTokenizer.from_pretrained(self.llm_model_name_rag)
            model = AutoModelForSeq2SeqLM.from_pretrained(self.llm_model_name_rag)
            pipe = pipeline("text2text-generation", model=model, tokenizer=tokenizer, max_length=150)
            llm = HuggingFacePipeline(pipeline=pipe)

            template = """
           Contexte: {context}
            Question: {question}

            Réponse:
            """
            prompt = PromptTemplate.from_template(template)
            
            # La chaîne reste la même
            self.rag_chain = (
                {"context": retriever | format_docs, "question": RunnablePassthrough()}
                | prompt
                | llm
            )
            print("Pipeline RAG prêt.")
        except Exception as e:
            print(f"ERREUR FATALE lors de l'initialisation du RAG : {e}")


    def transcribe_media(self, media_path: str):
        if not os.path.exists(media_path):
            print(f"ERREUR: Fichier média non trouvé : {media_path}")
            return None, None
        try:
            segments, info = self.model.transcribe(media_path, word_timestamps=True)
            print(f"[INFO] Langue détectée : '{info.language}' avec une probabilité de {info.language_probability:.2f}")
            return segments, info
        except Exception as e:
            print(f"ERREUR lors de la transcription : {e}")
            return None, None
        
    def analyze_grammar(self, text: str) -> dict:
        self._initialize_grammar_tool()
        if not self.grammar_tool or not text.strip():
            return {"grammar_score": 0.0, "error_count": 0, "errors": []}
        try:
            matches = self.grammar_tool.check(text)
            word_count = len(text.split())
            if word_count == 0: return {"grammar_score": 1.0, "error_count": 0, "errors": []}
            score = max(0, 100 - (len(matches) * 5)) / 100.0
            detailed_errors = [
                {
                    "message": match.message,
                    "correction": match.replacements[0] if match.replacements else "N/A",
                    "context": match.context,
                    "offset": match.offset,
                    "length": match.errorLength
                }
                for match in matches
            ]
            return {"grammar_score": round(score, 2), "error_count": len(matches), "errors": detailed_errors}
        except Exception as e:
            print(f"ERREUR lors de l'analyse grammaticale : {e}")
            return {"grammar_score": 0.0, "error_count": -1, "errors": []}
    
    def analyze_relevance(self, text1: str, text2: str) -> float:
        self._initialize_semantic_model()
        if not self.semantic_model or not text1 or not text2:
            return 0.0
        try:
            embedding1 = self.semantic_model.encode(text1, convert_to_tensor=True)
            embedding2 = self.semantic_model.encode(text2, convert_to_tensor=True)
            cosine_score = util.pytorch_cos_sim(embedding1, embedding2)
            relevance_score = max(0, min(1, cosine_score.item()))
            return round(relevance_score, 2)
        except Exception as e:
            print(f"ERREUR lors de l'analyse de la pertinence : {e}")
            return 0.0

    def analyze_relevance_with_rag(self, question: str, response: str) -> dict:
        self._initialize_rag_chain()
        self._initialize_semantic_model()
        
        if not self.rag_chain or not self.semantic_model:
            return {"score_pertinence_factuelle": 0.0, "explication": "Le système RAG n'est pas disponible."}
        
        try:
            print(f"  -> RAG : Génération de la réponse idéale pour la question...")
            ideal_response_from_llm = self.rag_chain.invoke(question).strip()
            
            if not ideal_response_from_llm:
                print("  -> RAG AVERTISSEMENT: Le LLM n'a pas pu générer de réponse idéale. Basculement en mode sémantique simple.")
                score = self.analyze_relevance(question, response)
                explication = "L'IA n'a pas pu générer de réponse idéale à partir de la base de connaissances. Le score est basé sur la similarité sémantique générale."
                return {"score_pertinence_factuelle": score, "explication": explication}

            print(f"  -> RAG : Réponse idéale générée : '{ideal_response_from_llm}'")
            score = self.analyze_relevance(response, ideal_response_from_llm)
            
            explication = (
                f"L'IA a généré la réponse de référence suivante à partir de la base de connaissances : '{ideal_response_from_llm}'. "
                f"La réponse du candidat a été comparée sémantiquement à cette référence."
            )
            
            return {"score_pertinence_factuelle": score, "explication": explication}
        except Exception as e:
            print(f"ERREUR lors de l'invocation du RAG: {e}")
            return {"score_pertinence_factuelle": 0.0, "explication": "Une erreur technique est survenue lors de l'analyse RAG."}

if __name__ == '__main__':
    print("\n" + "="*50)
    print("--- DÉBUT DU TEST DE L'AGENT NLP COMPLET ---")
    
    nlp_agent = NLPAgent(model_size="small")

    # --- TEST RAG ---
    print("\n" + "="*20 + " TEST RAG " + "="*20)
    question_specifique = "Quelles sont les valeurs de l'entreprise Innovatech Solutions ?"
    reponse_correcte = "Vos valeurs sont l'Innovation, la Collaboration et l'Intégrité."
    reponse_partielle = "Je crois que vos valeurs sont l'innovation et le travail d'équipe."
    reponse_fausse = "Votre entreprise vend des voitures électriques."
    
    print(f"\n[SCÉNARIO 1] Réponse Correcte: '{reponse_correcte}'")
    resultat_correct = nlp_agent.analyze_relevance_with_rag(question_specifique, reponse_correcte)
    print("-> Résultat RAG:", resultat_correct)

    print(f"\n[SCÉNARIO 2] Réponse Partielle: '{reponse_partielle}'")
    resultat_partiel = nlp_agent.analyze_relevance_with_rag(question_specifique, reponse_partielle)
    print("-> Résultat RAG:", resultat_partiel)
    
    print(f"\n[SCÉNARIO 3] Réponse Fausse: '{reponse_fausse}'")
    resultat_faux = nlp_agent.analyze_relevance_with_rag(question_specifique, reponse_fausse)
    print("-> Résultat RAG:", resultat_faux)

    # --- TEST SÉMANTIQUE SIMPLE ---
    print("\n" + "="*20 + " TEST SÉMANTIQUE SIMPLE " + "="*20)
    question_comportementale = "Décrivez une situation de conflit au travail."
    reponse_pertinente_sem = "Une fois, j'ai eu un désaccord avec un collègue sur une approche technique."
    reponse_non_pertinente_sem = "Je suis très ponctuel."
    
    print(f"\n[SCÉNARIO 4] Comparaison sémantique pertinente")
    score_pertinent = nlp_agent.analyze_relevance(question_comportementale, reponse_pertinente_sem)
    print(f"-> Score: {score_pertinent}")

    print(f"\n[SCÉNARIO 5] Comparaison sémantique non-pertinente")
    score_non_pertinent = nlp_agent.analyze_relevance(question_comportementale, reponse_non_pertinente_sem)
    print(f"-> Score: {score_non_pertinent}")
    
    # 1- TEST Transcription Audio → Texte 

    print("--- DÉBUT DU TEST DE L'AGENT NLP ---")
    
    files_to_test = {
        "Anglais": "data/datasets/CommonVoice (fr&en)/cv-corpus-en/en/clips/common_voice_en_42696072.mp3",
        "Français": "data/datasets/CommonVoice (fr&en)/cv-corpus-fr/fr/clips/common_voice_fr_42697572.mp3"
    }
    
    print("\n--- TEST DE TRANSCRIPTION ---")
    for language, file_path in files_to_test.items():
        if os.path.exists(file_path):
            print(f"\nTraitement de : {language} ({file_path})")
            
            segments, info = nlp_agent.transcribe_media(file_path)
            
            if segments:
                full_transcription = " ".join([segment.text.strip() for segment in segments])
                print("\n--- RÉSULTAT DE LA TRANSCRIPTION ---")
                print(full_transcription)
            else:
                print("--- LA TRANSCRIPTION A ÉCHOUÉ ---")
        else:
            print(f"\n!!! ATTENTION : Fichier de test non trouvé : {file_path}")
    
    
    #2. Test de la grammaire
    test_text_fr = "Je suis aller au marcher et j'ai acheter des pomme. C'est des bon fruits."
    print("\n" + "="*50)
    print(f"TESTANT L'ANALYSE GRAMMATICALE SUR LE TEXTE : '{test_text_fr}'")
    
    grammar_results = nlp_agent.analyze_grammar(test_text_fr)
    
    if grammar_results and grammar_results.get('errors'):
        print("\n--- RÉSULTAT DE L'ANALYSE GRAMMATICALE ---")
        print(f"Score: {grammar_results['grammar_score']}, Erreurs: {grammar_results['error_count']}")
        print("Détail des erreurs :")
        for error in grammar_results['errors']:
            # On utilise .get() pour un affichage robuste
            context_text = error.get('context', 'N/A')
            print(f"- {error.get('message', 'N/A')} -> Suggestion: '{error.get('correction', 'N/A')}' (Contexte: ...{context_text}...)")
            
    
    # 3. Test de Pertinence Sémantique
    question = "Quelles sont vos expériences avec les bases de données SQL et NoSQL ?"
    reponse_pertinente = "J'ai beaucoup travaillé avec PostgreSQL pour des applications web, et j'ai utilisé MongoDB pour des projets nécessitant plus de flexibilité."
    reponse_non_pertinente = "J'aime beaucoup travailler en équipe et je suis très motivé."
    
    print("\n" + "="*50)
    print(f"TEST SÉMANTIQUE")
    print(f"Question : {question}")
    
    score_pertinent = nlp_agent.analyze_relevance(question, reponse_pertinente)
    print(f"\nRéponse pertinente : '{reponse_pertinente}'")
    print(f"-> Score de Pertinence : {score_pertinent}") # Attendu > 0.6

    score_non_pertinent = nlp_agent.analyze_relevance(question, reponse_non_pertinente)
    print(f"\nRéponse non pertinente : '{reponse_non_pertinente}'")
    print(f"-> Score de Pertinence : {score_non_pertinent}") # Attendu < 0.3

    print("\n" + "="*50)
    print("--- FIN DU TEST ---")

    print("\nNLPAgent prêt à l'emploi !")