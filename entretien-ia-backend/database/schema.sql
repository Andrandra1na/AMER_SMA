-- Suppression des tables dans l'ordre inverse des dépendances pour éviter les erreurs
DROP TABLE IF EXISTS facial_features, emotion_scores, audio_features, reports, answers, questions, sessions, exports, configurations, users CASCADE;

-- =================================================================
-- TABLE: users
-- Stocke les informations de tous les utilisateurs de la plateforme.
-- =================================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    mot_de_passe_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'candidat', 'recruteur')),
    doit_changer_mdp BOOLEAN NOT NULL DEFAULT TRUE,
    date_inscription TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc')
);

-- =================================================================
-- TABLE: questions
-- Bibliothèque de toutes les questions possibles pour les entretiens.
-- =================================================================
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    recruteur_id INTEGER REFERENCES users(id) ON DELETE SET NULL, -- NULL pour les questions par défaut
    intitule TEXT NOT NULL,
    category VARCHAR(100),
    role_target VARCHAR(100),
    difficulty VARCHAR(20),
    source_type VARCHAR(50),
    ideal_answer TEXT,
    phase VARCHAR(50),
    experience_level VARCHAR(20),
    keywords TEXT[],
    signalement_admin BOOLEAN DEFAULT FALSE,
    commentaire_admin TEXT
);

-- =================================================================
-- TABLE: sessions
-- Représente une session d'entretien, liant un candidat et un recruteur.
-- =================================================================
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recruteur_id INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    poste_vise VARCHAR(255) NOT NULL,
    statut VARCHAR(20) DEFAULT 'pending',
    date_entretien TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
    tentatives_realisees INTEGER NOT NULL DEFAULT 0,
    nombre_tentatives INTEGER NOT NULL DEFAULT 2,
    fichier_video TEXT,
    fichier_audio TEXT,
    response_timestamps JSONB,
    events_timeline JSONB,
    questions_ids INTEGER[]
);

-- =================================================================
-- TABLE: answers
-- Stocke chaque réponse d'un candidat pour une question spécifique d'une session.
-- =================================================================
CREATE TABLE answers (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    transcription TEXT,
    score_pertinence REAL, -- 'REAL' est un alias pour 'float4'
    score_grammaire REAL,
    erreurs_grammaire JSONB,
    speech_rate FLOAT,
    pause_count INTEGER,
    pertinence_explication TEXT
);


-- =================================================================
-- TABLE: reports
-- Stocke le rapport global final pour une session, après analyse.
-- =================================================================
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
    transcription_complete TEXT,
    score_grammaire REAL,
    note_globale REAL,
    commentaire_rh TEXT,
    validated BOOLEAN DEFAULT FALSE,
    fichier_pdf_path TEXT
);

-- =================================================================
-- TABLES POUR LES FEATURES IA (une ligne par session)
-- =================================================================
CREATE TABLE audio_features (
    id SERIAL PRIMARY KEY,
    session_id INTEGER UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
    speech_rate FLOAT, -- Débit de parole en mots par minute
    pause_count INTEGER, -- Nombre de pauses significatives
    average_pause_duration FLOAT, -- Durée moyenne des pauses en secondes
    pitch_mean FLOAT, -- Hauteur moyenne de la voix (en Hz)
    pitch_std FLOAT,-- Écart-type de la hauteur (variabilité de la voix)
    fluency_score FLOAT 
);

CREATE TABLE emotion_scores (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
    dominant_emotion VARCHAR(50),
    scores JSONB
);

-- TABLE: facial_features (pour les analyses visuelles)
CREATE TABLE facial_features (
    id SERIAL PRIMARY KEY,
    session_id INTEGER UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
    gaze_global_distribution JSONB, -- Ex: {"centre_percent": 80, "gauche_percent": 15, ...}
    gaze_by_question JSONB, -- Ex: {"71": {"centre_percent": 75, ...}, "105": {...}}
    smile_frequency FLOAT, -- Nombre de sourires détectés par minute
    head_pose_analysis JSONB -- Analyse de la posture de la tête
);

-- =================================================================
-- TABLES UTILITAIRES
-- =================================================================
CREATE TABLE exports (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    date_export TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
    type_export VARCHAR(10) CHECK (type_export IN ('csv', 'pdf', 'json'))
);

CREATE TABLE configurations (
    id SERIAL PRIMARY KEY,
    cle VARCHAR(100) UNIQUE NOT NULL,
    valeur TEXT
);


-- NOUVELLE TABLE POUR LES PROFILS DE PONDÉRATION
CREATE TABLE profils_ponderation (
    id SERIAL PRIMARY KEY,
    nom_profil VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    poids JSONB NOT NULL -- ex: {"relevance": 0.6, "clarity": 0.2, ...}
);

-- MODIFICATION DE LA TABLE sessions
-- Supprimez d'abord la contrainte si elle existe, puis ajoutez la colonne
ALTER TABLE sessions ADD COLUMN profil_ponderation_id INTEGER REFERENCES profils_ponderation(id);

-- Création d'index pour améliorer les performances des recherches fréquentes
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_recruteur_id ON sessions(recruteur_id);
CREATE INDEX idx_answers_session_id ON answers(session_id);