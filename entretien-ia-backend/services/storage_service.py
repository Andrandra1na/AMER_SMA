import os
import uuid
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
UPLOAD_FOLDER_ABSOLUTE = os.path.join(BASE_DIR, 'data', 'uploads')

ALLOWED_EXTENSIONS = {'mp4', 'webm', 'mp3', 'wav', 'm4a'}

def _is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, user_id):
    if not file or not file.filename:
        return None
    if not _is_allowed_file(file.filename):
        return None

    original_filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
    
    # On crée le sous-dossier de l'utilisateur
    user_upload_folder_absolute = os.path.join(UPLOAD_FOLDER_ABSOLUTE, str(user_id))
    os.makedirs(user_upload_folder_absolute, exist_ok=True)

    absolute_file_path = os.path.join(user_upload_folder_absolute, unique_filename)
    
    try:
        file.save(absolute_file_path)
    except Exception as e:
        print(f"ERREUR: Échec de la sauvegarde du fichier {absolute_file_path}: {e}")
        return None

    # On retourne un chemin RELATIF, mais seulement à partir du dossier de l'utilisateur.
    # Ex: "3/xxxxxxxx_entretien.webm"
    # C'est ce qui sera stocké en BDD.
    path_to_store_in_db = os.path.join(str(user_id), unique_filename)
    
    return path_to_store_in_db

def delete_file(path_from_db):
    if not path_from_db:
        return True
        
    try:
        # On reconstruit le chemin absolu à partir de UPLOAD_FOLDER_ABSOLUTE
        absolute_path_to_delete = os.path.join(UPLOAD_FOLDER_ABSOLUTE, path_from_db)
        
        if os.path.exists(absolute_path_to_delete):
            os.remove(absolute_path_to_delete)
            print(f"INFO: Fichier supprimé : {absolute_path_to_delete}")
        return True
    except OSError as e:
        print(f"ERREUR: Échec de la suppression du fichier {path_from_db}: {e}")
        return False