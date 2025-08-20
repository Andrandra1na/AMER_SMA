import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
KNOWLEDGE_BASE_PATH = os.path.join(BASE_DIR, 'data', 'knowledge_base.txt')
VECTOR_DB_PATH = os.path.join(BASE_DIR, 'data', 'vector_db')
EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2' 

def create_vector_database():
    """
    Lit la base de connaissances, la découpe, la vectorise et la sauvegarde
    dans un index FAISS local.
    """
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        print(f"ERREUR: Fichier de base de connaissances non trouvé : {KNOWLEDGE_BASE_PATH}")
        return

    print("Début de la création de la base de données vectorielle...")

    # 1. Charger le document
    loader = TextLoader(KNOWLEDGE_BASE_PATH, encoding='utf-8')
    documents = loader.load()
    print(f"-> Document chargé : {len(documents[0].page_content)} caractères.")

    # 2. Découper le document en plus petits morceaux (chunks)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = text_splitter.split_documents(documents)
    print(f"-> Document découpé en {len(docs)} chunks.")

    # 3. Charger le modèle d'embedding (celui qui transforme le texte en vecteurs)
    print(f"Chargement du modèle d'embedding : {EMBEDDING_MODEL}...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    print("-> Modèle d'embedding chargé.")

    # 4. Créer la base de données vectorielle FAISS à partir des chunks
    print("Création de l'index FAISS...")
    db = FAISS.from_documents(docs, embeddings)

    # 5. Sauvegarder l'index localement
    os.makedirs(VECTOR_DB_PATH, exist_ok=True)
    db.save_local(VECTOR_DB_PATH)

    print("-" * 50)
    print("✅ Base de données vectorielle créée avec succès !")
    print(f"Sauvegardée dans : {VECTOR_DB_PATH}")
    print("-" * 50)

if __name__ == '__main__':
    create_vector_database()