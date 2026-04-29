-- EvalConnect — Schéma de base de données
-- Compatible PostgreSQL (Render) et SQLite (local via script séparé)

-- Suppression dans l'ordre inverse des dépendances
DROP TABLE IF EXISTS quiz_classe CASCADE;
DROP TABLE IF EXISTS classe_etudiant CASCADE;
DROP TABLE IF EXISTS participation CASCADE;
DROP TABLE IF EXISTS question CASCADE;
DROP TABLE IF EXISTS quiz CASCADE;
DROP TABLE IF EXISTS classe CASCADE;
DROP TABLE IF EXISTS utilisateur CASCADE;

-- ── Table utilisateur ──────────────────────────────────────────
CREATE TABLE utilisateur (
    id             SERIAL PRIMARY KEY,
    nom            VARCHAR(50)  NOT NULL,
    prenom         VARCHAR(50)  NOT NULL,
    email          VARCHAR(150) NOT NULL UNIQUE,
    mot_de_passe   CHAR(60)     NOT NULL,
    role           VARCHAR(20)  NOT NULL DEFAULT 'etudiant'
                   CHECK(role IN ('etudiant','enseignant','admin')),
    actif          SMALLINT     NOT NULL DEFAULT 0,
    date_creation  DATE         NOT NULL DEFAULT CURRENT_DATE
);

CREATE INDEX idx_utilisateur_email ON utilisateur(email);

-- ── Table classe ──────────────────────────────────────────────
CREATE TABLE classe (
    id             SERIAL PRIMARY KEY,
    nom            VARCHAR(100) NOT NULL,
    description    TEXT,
    id_enseignant  INTEGER      NOT NULL,
    date_creation  DATE         NOT NULL DEFAULT CURRENT_DATE,
    FOREIGN KEY (id_enseignant) REFERENCES utilisateur(id) ON DELETE CASCADE
);

CREATE INDEX idx_classe_enseignant ON classe(id_enseignant);

-- ── Table classe_etudiant ─────────────────────────────────────
CREATE TABLE classe_etudiant (
    id          SERIAL PRIMARY KEY,
    id_classe   INTEGER NOT NULL,
    id_etudiant INTEGER NOT NULL,
    date_ajout  DATE    NOT NULL DEFAULT CURRENT_DATE,
    FOREIGN KEY (id_classe)   REFERENCES classe(id)      ON DELETE CASCADE,
    FOREIGN KEY (id_etudiant) REFERENCES utilisateur(id) ON DELETE CASCADE,
    UNIQUE(id_classe, id_etudiant)
);

CREATE INDEX idx_classe_etudiant_classe    ON classe_etudiant(id_classe);
CREATE INDEX idx_classe_etudiant_etudiant  ON classe_etudiant(id_etudiant);

-- ── Table quiz ─────────────────────────────────────────────────
CREATE TABLE quiz (
    id             SERIAL PRIMARY KEY,
    titre          VARCHAR(100) NOT NULL,
    description    TEXT,
    duree_minutes  INTEGER      NOT NULL DEFAULT 60,
    statut         VARCHAR(10)  NOT NULL DEFAULT 'actif'
                   CHECK(statut IN ('actif','archive')),
    date_creation  DATE         NOT NULL DEFAULT CURRENT_DATE,
    id_createur    INTEGER      NOT NULL,
    FOREIGN KEY (id_createur) REFERENCES utilisateur(id) ON DELETE CASCADE
);

CREATE INDEX idx_quiz_createur ON quiz(id_createur);
CREATE INDEX idx_quiz_statut   ON quiz(statut);

-- ── Table quiz_classe ─────────────────────────────────────────
CREATE TABLE quiz_classe (
    id         SERIAL PRIMARY KEY,
    id_quiz    INTEGER NOT NULL,
    id_classe  INTEGER NOT NULL,
    date_ajout DATE    NOT NULL DEFAULT CURRENT_DATE,
    FOREIGN KEY (id_quiz)   REFERENCES quiz(id)   ON DELETE CASCADE,
    FOREIGN KEY (id_classe) REFERENCES classe(id) ON DELETE CASCADE,
    UNIQUE(id_quiz, id_classe)
);

CREATE INDEX idx_quiz_classe_quiz   ON quiz_classe(id_quiz);
CREATE INDEX idx_quiz_classe_classe ON quiz_classe(id_classe);

-- ── Table question ─────────────────────────────────────────────
CREATE TABLE question (
    id               SERIAL PRIMARY KEY,
    id_quiz          INTEGER NOT NULL,
    texte            TEXT    NOT NULL,
    options          TEXT    NOT NULL,
    index_bonne_rep  INTEGER NOT NULL CHECK(index_bonne_rep BETWEEN 0 AND 3),
    FOREIGN KEY (id_quiz) REFERENCES quiz(id) ON DELETE CASCADE
);

CREATE INDEX idx_question_quiz ON question(id_quiz);

-- ── Table participation ────────────────────────────────────────
CREATE TABLE participation (
    id            SERIAL PRIMARY KEY,
    id_quiz       INTEGER          NOT NULL,
    id_etudiant   INTEGER          NOT NULL,
    score         REAL             NOT NULL,
    date_passage  TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_quiz)     REFERENCES quiz(id)        ON DELETE CASCADE,
    FOREIGN KEY (id_etudiant) REFERENCES utilisateur(id) ON DELETE CASCADE,
    UNIQUE(id_quiz, id_etudiant)
);

CREATE INDEX idx_participation_quiz      ON participation(id_quiz);
CREATE INDEX idx_participation_etudiant  ON participation(id_etudiant);