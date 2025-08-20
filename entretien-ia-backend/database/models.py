from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    CheckConstraint, ForeignKey, Integer, String, Text, Boolean, DateTime, Float, text, JSON
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from typing import List, Optional
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

db = SQLAlchemy()

# Pour les champs JSONB
JsonVariant = JSON().with_variant(JSONB, 'postgresql')

# Pour les tableaux d'ENTIERS (comme questions_ids)
IntArrayVariant = JSON().with_variant(ARRAY(Integer), 'postgresql')

# Pour les tableaux de TEXTE (comme keywords) ---
StringArrayVariant = JSON().with_variant(ARRAY(String), 'postgresql')


class Users(db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    mot_de_passe_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(20), CheckConstraint("role IN ('admin', 'candidat', 'recruteur')"), nullable=False)
    doit_changer_mdp: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    date_inscription: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=db.func.current_timestamp())
    
    # Relations (One-to-Many)
    questions_creees: Mapped[List['Questions']] = relationship('Questions', back_populates='recruteur', foreign_keys='[Questions.recruteur_id]')
    sessions_candidat: Mapped[List['Sessions']] = relationship('Sessions', back_populates='candidat', foreign_keys='[Sessions.user_id]')
    sessions_recruteur: Mapped[List['Sessions']] = relationship('Sessions', back_populates='recruteur', foreign_keys='[Sessions.recruteur_id]')
    exports: Mapped[List['Exports']] = relationship('Exports', back_populates='admin', foreign_keys='[Exports.admin_id]')

    def set_password(self, password): self.mot_de_passe_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.mot_de_passe_hash, password)

class Sessions(db.Model):
    __tablename__ = 'sessions'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    recruteur_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    poste_vise: Mapped[str] = mapped_column(String(255), nullable=False)
    statut: Mapped[str] = mapped_column(String(20), default='pending')
    nombre_tentatives: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('2'))
    tentatives_realisees: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    date_entretien: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=db.func.current_timestamp())
    fichier_video: Mapped[Optional[str]] = mapped_column(Text)
    fichier_audio: Mapped[Optional[str]] = mapped_column(Text)
    response_timestamps: Mapped[Optional[dict]] = mapped_column(JsonVariant, nullable=True)  # Dictionnaire des timestamps de réponses
    events_timeline: Mapped[Optional[dict]] = mapped_column(JsonVariant, nullable=True)
    questions_ids: Mapped[Optional[List[int]]] = mapped_column(IntArrayVariant)  # Liste d'IDs de questions posées
    
    profil_ponderation_id: Mapped[Optional[int]] = mapped_column(ForeignKey('profils_ponderation.id'))
    profil_ponderation = relationship("ProfilsPonderation", back_populates="sessions")

    
    # Relations (Many-to-One)
    candidat: Mapped['Users'] = relationship('Users', foreign_keys=[user_id], back_populates="sessions_candidat")
    recruteur: Mapped['Users'] = relationship('Users', foreign_keys=[recruteur_id], back_populates="sessions_recruteur")
    # Relations (One-to-Many / One-to-One)
    answers: Mapped[List['Answers']] = relationship('Answers', back_populates='session', cascade="all, delete-orphan")
    report: Mapped[Optional['Reports']] = relationship('Reports', back_populates='session', uselist=False, cascade="all, delete-orphan")
    audio_features: Mapped[Optional['AudioFeatures']] = relationship('AudioFeatures', uselist=False, back_populates='session', cascade="all, delete-orphan")
    emotion_scores: Mapped[Optional['EmotionScores']] = relationship('EmotionScores', uselist=False, back_populates='session', cascade="all, delete-orphan")
    facial_features: Mapped[Optional['FacialFeatures']] = relationship('FacialFeatures', uselist=False, back_populates='session', cascade="all, delete-orphan")

class Questions(db.Model):
    __tablename__ = 'questions'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recruteur_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'))
    intitule: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    role_target: Mapped[Optional[str]] = mapped_column(String(100))
    difficulty: Mapped[Optional[str]] = mapped_column(String(20))
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    ideal_answer: Mapped[Optional[str]] = mapped_column(Text)
    phase: Mapped[Optional[str]] = mapped_column(String(50))
    experience_level: Mapped[Optional[str]] = mapped_column(String(20))
    keywords: Mapped[Optional[List[str]]] = mapped_column(StringArrayVariant)  # Liste de mots-clés associés
    signalement_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    commentaire_admin: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relations
    recruteur: Mapped[Optional['Users']] = relationship('Users', back_populates='questions_creees')
    answers: Mapped[List['Answers']] = relationship('Answers', back_populates='question')

class Answers(db.Model):
    __tablename__ = 'answers'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey('sessions.id'), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey('questions.id'), nullable=False)
    transcription: Mapped[Optional[str]] = mapped_column(Text)
    score_pertinence: Mapped[Optional[float]] = mapped_column(Float)
    score_grammaire: Mapped[Optional[float]] = mapped_column(Float)
    erreurs_grammaire: Mapped[Optional[dict]] = mapped_column(JsonVariant)
    speech_rate: Mapped[Optional[float]] = mapped_column(Float)
    pause_count: Mapped[Optional[int]] = mapped_column(Integer)
    pertinence_explication: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relations
    session: Mapped['Sessions'] = relationship('Sessions', back_populates='answers')
    question: Mapped['Questions'] = relationship('Questions', back_populates='answers')

class Reports(db.Model):
    __tablename__ = 'reports'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey('sessions.id'), unique=True, nullable=False)
    transcription_complete: Mapped[Optional[str]] = mapped_column(Text)
    score_grammaire: Mapped[Optional[float]] = mapped_column(Float)
    note_globale: Mapped[Optional[float]] = mapped_column(Float)
    commentaire_rh: Mapped[Optional[str]] = mapped_column(Text)
    validated: Mapped[bool] = mapped_column(Boolean, default=False)
    fichier_pdf_path: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relations
    session: Mapped['Sessions'] = relationship('Sessions', back_populates='report')

class AudioFeatures(db.Model):
    __tablename__ = 'audio_features'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey('sessions.id'), unique=True)
    speech_rate: Mapped[Optional[float]] = mapped_column(Float)
    pause_count: Mapped[Optional[int]] = mapped_column(Integer)
    average_pause_duration: Mapped[Optional[float]] = mapped_column(Float)
    pitch_mean: Mapped[Optional[float]] = mapped_column(Float)
    pitch_std: Mapped[Optional[float]] = mapped_column(Float)
    fluency_score: Mapped[Optional[float]] = mapped_column(Float)

    # Relation inverse dans la classe Sessions
    session = relationship("Sessions", back_populates="audio_features")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class EmotionScores(db.Model):
    __tablename__ = 'emotion_scores'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey('sessions.id'), unique=True, nullable=False)
    dominant_emotion: Mapped[Optional[str]] = mapped_column(String(50))
    scores: Mapped[Optional[dict]] = mapped_column(JsonVariant)
    
    session: Mapped['Sessions'] = relationship('Sessions', back_populates='emotion_scores')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class FacialFeatures(db.Model):
    __tablename__ = 'facial_features'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey('sessions.id'), unique=True)
    
    gaze_global_distribution: Mapped[Optional[dict]] = mapped_column(JsonVariant)
    gaze_by_question: Mapped[Optional[dict]] = mapped_column(JsonVariant)
    smile_frequency: Mapped[Optional[float]] = mapped_column(Float)
    head_pose_analysis: Mapped[Optional[dict]] = mapped_column(JsonVariant)
    
    session = relationship("Sessions", back_populates="facial_features")

class Exports(db.Model):
    __tablename__ = 'exports'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'))
    date_export: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=db.func.current_timestamp())
    type_export: Mapped[str] = mapped_column(String(10), CheckConstraint("type_export IN ('csv', 'pdf', 'json')"))
    
    admin: Mapped[Optional['Users']] = relationship('Users', back_populates='exports')
    
class Configurations(db.Model):
    __tablename__ = 'configurations'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cle: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    valeur: Mapped[Optional[str]] = mapped_column(Text)

class ProfilsPonderation(db.Model):
    __tablename__ = 'profils_ponderation'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom_profil: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    poids: Mapped[dict] = mapped_column(JsonVariant, nullable=False)
    
    sessions = relationship("Sessions", back_populates="profil_ponderation")
    

