import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import create_app
from database.models import db, Users, Sessions, ProfilsPonderation


@pytest.fixture(scope='session')
def app():
    params = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    }
    _app = create_app(params)

    with _app.app_context():
        yield _app

@pytest.fixture(scope='function')
def db_session(app):
    """
    Crée une base de données et une session de BDD pour chaque test.
    'scope=function' signifie que la BDD est recréée à chaque test,
    garantissant une isolation parfaite.
    """
    with app.app_context():
        db.create_all() # Crée les tables dans la BDD en mémoire
        yield db.session # Fournit la session de BDD au test
        db.session.remove() # Nettoie la session
        db.drop_all() # Supprime toutes les tables après le test


@pytest.fixture(scope='function')
def sample_user(db_session):
    """Crée un utilisateur de test."""
    user = Users(nom="Test User", email="test@example.com", role="recruteur")
    user.set_password("password")
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture(scope='function')
def sample_profile(db_session):
    """Crée un profil de pondération de test."""
    profile = ProfilsPonderation(
        nom_profil="Test Profile",
        poids={'relevance': 50, 'clarity': 30, 'fluency': 10, 'engagement': 10}
    )
    db_session.add(profile)
    db_session.commit()
    return profile

@pytest.fixture(scope='function')
def sample_session(db_session, sample_user, sample_profile):
    """Crée une session de test liée à un utilisateur et un profil."""
    session = Sessions(
        user_id=sample_user.id,
        recruteur_id=sample_user.id,
        poste_vise="Test Post",
        profil_ponderation_id=sample_profile.id
    )
    db_session.add(session)
    db_session.commit()
    return session