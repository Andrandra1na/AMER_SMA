from flask_jwt_extended import JWTManager
from celery import Celery
from flask_mail import Mail


jwt = JWTManager()

celery = Celery(__name__)

mail = Mail()
