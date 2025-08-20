from datetime import timedelta
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    print("Fichier .env trouvé et chargé.")
else:
    print("AVERTISSEMENT : Le fichier .env n'a pas été trouvé. Les variables de configuration doivent être définies dans l'environnement.")

class Config:
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_TOKEN_LOCATION = ["headers", "cookies", "query_string"]
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    SQLALCHEMY_DATABASE_URI = os.getenv('DB_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    if not JWT_SECRET_KEY:
        raise ValueError("Erreur fatale: La variable d'environnement 'JWT_SECRET_KEY' n'est pas définie. Veuillez la définir dans le fichier .env.")
    
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("Erreur fatale: La variable d'environnement 'DB_URL' n'est pas définie. Veuillez la définir dans le fichier .env.")
    
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    