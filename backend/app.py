import os
import json
from functools import wraps
from datetime import date, datetime

import bcrypt
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, g, abort, make_response
)

from config import Config
DATABASE_URL = os.environ.get("DATABASE_URL")
app = Flask(__name__)
app.config.from_object(Config)

PER_PAGE = app.config["PER_PAGE"]

# Flag pour initialiser la DB une seule fois
_db_initialized = False


# ─────────────────────────────────────────────
# BASE DE DONNÉES : SQLite (local) ou PostgreSQL (Render)
# ─────────────────────────────────────────────

def _table_exists():
    """Vérifie si la table utilisateur existe."""
    try:
        if DATABASE_URL:
            print("[TABLE CHECK] Vérification sur PostgreSQL...")
            import psycopg2
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'utilisateur'
                );
            """)
            result = cur.fetchone()[0]
            print(f"[TABLE CHECK] PostgreSQL - Table existe: {result}")
            cur.close()
            conn.close()
            return result
        else:
            print("[TABLE CHECK] Vérification sur SQLite...")
            import sqlite3
            db_path = app.config["DATABASE"]
            print(f"[TABLE CHECK] Chemin DB: {db_path}")
            print(f"[TABLE CHECK] DB existe: {os.path.exists(db_path)}")
            
            if not os.path.exists(db_path):
                print("[TABLE CHECK] DB n'existe pas")
                return False
            
            conn = sqlite3.connect(db_path)
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='utilisateur'"
            )
            result = cur.fetchone() is not None
            print(f"[TABLE CHECK] SQLite - Table existe: {result}")
            conn.close()
            return result
    except Exception as e:
        import traceback
        print(f"[TABLE CHECK ERROR] Erreur: {e}")
        print(traceback.format_exc())
        return False


def get_db():
    """Retourne la connexion BDD pour la requête en cours."""
    if "db" not in g:
        if DATABASE_URL:
            import psycopg2
            import psycopg2.extras
            g.db = psycopg2.connect(
                DATABASE_URL,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            g._db_type = "postgres"
        else:
            import sqlite3
            g.db = sqlite3.connect(
                app.config["DATABASE"],
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
            g._db_type = "sqlite"
    return g.db


def query(sql, params=()):
    """
    Exécute une requête compatible SQLite ET PostgreSQL.
    Remplace automatiquement ? par %s pour PostgreSQL.
    Retourne un curseur avec .fetchone() et .fetchall().
    """
    db = get_db()
    if getattr(g, "_db_type", "sqlite") == "postgres":
        sql = sql.replace("?", "%s")
        cur = db.cursor()
        cur.execute(sql, params)
        return cur
    else:
        return db.execute(sql, params)


def query_many(sql, params_list):
    """executemany compatible SQLite ET PostgreSQL."""
    db = get_db()
    if getattr(g, "_db_type", "sqlite") == "postgres":
        sql = sql.replace("?", "%s")
        cur = db.cursor()
        cur.executemany(sql, params_list)
        return cur
    else:
        return db.executemany(sql, params_list)


def last_insert_id(cur):
    """Récupère le dernier ID inséré (SQLite = lastrowid, PG = RETURNING)."""
    if getattr(g, "_db_type", "sqlite") == "postgres":
        return cur.fetchone()["id"]
    else:
        return cur.lastrowid


def commit():
    get_db().commit()


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ─────────────────────────────────────────────
# INITIALISATION DE LA BASE
# ─────────────────────────────────────────────

def init_db():
    """Initialise la base depuis schema.sql."""
    db = get_db()
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    if getattr(g, "_db_type", "sqlite") == "postgres":
        cur = db.cursor()
        cur.execute(sql)
        db.commit()
    else:
        db.executescript(sql)
        db.commit()


@app.cli.command("init-db")
def init_db_command():
    init_db()
    print("Base de données initialisée.")


@app.cli.command("seed-db")
def seed_db_command():
    seed_db()
    print("Données de test insérées.")


def seed_db():
    """Insère les données de test dans la base de données."""
    try:
        db = get_db()
        seed_path = os.path.join(os.path.dirname(__file__), "..", "database", "seed.sql")
        print(f"[SEED] Lecture du fichier seed: {seed_path}")
        
        with open(seed_path, "r", encoding="utf-8") as f:
            sql = f.read()
        
        print(f"[SEED] SQL length: {len(sql)} caractères")

        if getattr(g, "_db_type", "sqlite") == "postgres":
            print("[SEED] Exécution sur PostgreSQL")
            cur = db.cursor()
            cur.execute(sql)
            db.commit()
        else:
            print("[SEED] Exécution sur SQLite")
            db.executescript(sql)
            db.commit()
        
        print("[SEED] Seed exécutée avec succès")
    except Exception as e:
        import traceback
        print(f"[SEED ERROR] Erreur: {e}")
        print(traceback.format_exc())
        raise


def ensure_db_initialized():
    """Initialise manuellement la base de données (via CLI)."""
    with app.app_context():
        init_db()
        seed_db()


# ─────────────────────────────────────────────
# DÉCORATEURS
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Connectez-vous pour accéder à cette page.", "error")
            return redirect(url_for("auth_login"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth_login"))
            if session.get("role") not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_current_user():
    if "user_id" not in session:
        return None
    return query(
        "SELECT id, nom, prenom, email, role FROM utilisateur WHERE id = ?",
        (session["user_id"],)
    ).fetchone()


@app.context_processor
def inject_user():
    return {"current_user": get_current_user()}


# ─────────────────────────────────────────────
# INITIALISATION AU DÉMARRAGE
# ─────────────────────────────────────────────

@app.before_request
def initialize_db():
    """Initialise la base de données au premier appel HTTP si nécessaire."""
    global _db_initialized
    
    if not _db_initialized:
        table_exists = _table_exists()
        print(f"[DB CHECK] Table utilisateur existe: {table_exists}")
        
        if not table_exists:
            try:
                print("[DB INIT] Initialisation de la base de données au premier appel...")
                init_db()
                print("[DB INIT] Schéma créé")
                seed_db()
                print("[DB INIT] Données de test insérées")
            except Exception as e:
                import traceback
                print(f"[DB ERROR] Erreur lors de l'initialisation: {e}")
                print(traceback.format_exc())
        else:
            # La table existe, vérifier si elle a des données
            try:
                count_result = query("SELECT COUNT(*) as cnt FROM utilisateur").fetchone()
                user_count = count_result['cnt']
                print(f"[DB CHECK] Nombre d'utilisateurs: {user_count}")
                
                if user_count == 0:
                    print("[DB INIT] Table vide, insertion des données de test...")
                    seed_db()
                    print("[DB INIT] Données de test insérées")
            except Exception as e:
                import traceback
                print(f"[DB ERROR] Erreur lors de la vérification du contenu: {e}")
                print(traceback.format_exc())
        
        _db_initialized = True


# ─────────────────────────────────────────────
# ROUTES — AUTH
# ─────────────────────────────────────────────

@app.route("/debug")
def debug():
    """Endpoint de debug pour vérifier l'état de la base de données."""
    try:
        info = {}
        info["_db_initialized"] = _db_initialized
        info["_table_exists"] = _table_exists()
        
        # Compter les utilisateurs
        try:
            count = query("SELECT COUNT(*) as cnt FROM utilisateur").fetchone()
            info["user_count"] = count['cnt']
        except Exception as e:
            info["user_count_error"] = str(e)
        
        # Lister les utilisateurs
        try:
            users = query("SELECT id, email, role, actif FROM utilisateur").fetchall()
            info["users"] = [dict(u) for u in users]
        except Exception as e:
            info["users_error"] = str(e)
        
        return {
            "status": "ok",
            "db_type": getattr(g, "_db_type", "unknown"),
            "info": info
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.route("/force-init")
def force_init():
    """Force l'initialisation de la base de données."""
    global _db_initialized
    
    try:
        print("[FORCE INIT] Forçage de l'initialisation...")
        _db_initialized = False  # Reset le flag
        
        # Forcer la vérification et l'initialisation
        initialize_db()
        
        return {
            "status": "ok",
            "message": "Initialisation forcée terminée"
        }
    except Exception as e:
        import traceback
        print(f"[FORCE INIT ERROR] {e}")
        print(traceback.format_exc())
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/auth/register", methods=["GET", "POST"])
def auth_register():
    if request.method == "POST":
        nom    = request.form.get("nom",    "").strip()
        prenom = request.form.get("prenom", "").strip()
        email  = request.form.get("email",  "").strip().lower()
        role   = request.form.get("role",   "etudiant")
        pwd    = request.form.get("password", "")
        pwd2   = request.form.get("password2", "")

        errors = []
        if not nom:    errors.append("Le nom est requis.")
        if not prenom: errors.append("Le prénom est requis.")
        if not email or "@" not in email: errors.append("Email invalide.")
        if len(pwd) < 8: errors.append("Mot de passe trop court (8 caractères min).")
        if pwd != pwd2:  errors.append("Les mots de passe ne correspondent pas.")
        if role not in ("etudiant", "enseignant"): errors.append("Rôle invalide.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("register.html")

        if query("SELECT id FROM utilisateur WHERE email = ?", (email,)).fetchone():
            flash("Cet email est déjà utilisé.", "error")
            return render_template("register.html")

        hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
        query(
            "INSERT INTO utilisateur (nom, prenom, email, mot_de_passe, role, actif) VALUES (?,?,?,?,?,?)",
            (nom, prenom, email, hashed, role, 0)
        )
        commit()
        flash("Compte créé ! En attente de validation par l'administrateur.", "info")
        return redirect(url_for("auth_login"))

    return render_template("register.html")


@app.route("/auth/login", methods=["GET", "POST"])
def auth_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pwd   = request.form.get("password", "")

        print(f"[LOGIN] Tentative de connexion avec email: {email}")

        if not email or not pwd:
            print(f"[LOGIN] Email ou mot de passe vide")
            flash("Email et mot de passe requis.", "error")
            return render_template("login.html")

        user = query(
            "SELECT id, nom, prenom, mot_de_passe, role, actif FROM utilisateur WHERE email = ?",
            (email,)
        ).fetchone()

        print(f"[LOGIN] Utilisateur trouvé: {user is not None}")
        if user:
            print(f"[LOGIN] Actif: {user['actif']}, Rôle: {user['role']}")

        pwd_ok = user and bcrypt.checkpw(pwd.encode(), user["mot_de_passe"].encode())
        print(f"[LOGIN] Mot de passe correct: {pwd_ok}")

        if not pwd_ok:
            print(f"[LOGIN] Identifiants invalides")
            flash("Email ou mot de passe incorrect.", "error")
            return render_template("login.html")

        if not user["actif"]:
            print(f"[LOGIN] Compte inactif")
            flash("Votre compte est en attente de validation par l'administrateur.", "warning")
            return render_template("login.html")

        print(f"[LOGIN] Connexion réussie pour {user['prenom']} {user['nom']}")
        session.clear()
        session["user_id"] = user["id"]
        session["role"]    = user["role"]
        session["prenom"]  = user["prenom"]

        if user["role"] == "admin":
            return redirect(url_for("admin_users"))
        elif user["role"] == "enseignant":
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("quiz_list"))

    return render_template("login.html")


@app.route("/auth/logout")
def auth_logout():
    session.clear()
    flash("Vous êtes déconnecté.", "success")
    return redirect(url_for("index"))


# ─────────────────────────────────────────────
# ROUTES — CLASSES
# ─────────────────────────────────────────────

def can_student_take_quiz(student_id, quiz_id):
    quiz_classes = query(
        "SELECT id_classe FROM quiz_classe WHERE id_quiz = ?", (quiz_id,)
    ).fetchall()

    if not quiz_classes:
        return True

    for qc in quiz_classes:
        is_in_class = query(
            "SELECT id FROM classe_etudiant WHERE id_classe = ? AND id_etudiant = ?",
            (qc["id_classe"], student_id)
        ).fetchone()
        if is_in_class:
            return True

    return False


@app.route("/classes")
@role_required("enseignant")
def classes_list():
    classes = query(
        "SELECT id, nom, description, date_creation FROM classe WHERE id_enseignant = ? ORDER BY date_creation DESC",
        (session["user_id"],)
    ).fetchall()
    return render_template("classes.html", classes=classes)


@app.route("/classes/create", methods=["GET", "POST"])
@role_required("enseignant")
def classes_create():
    if request.method == "POST":
        nom         = request.form.get("nom", "").strip()
        description = request.form.get("description", "").strip()

        if not nom:
            flash("Nom de classe requis.", "error")
            return render_template("classes-create.html")

        query(
            "INSERT INTO classe (nom, description, id_enseignant) VALUES (?, ?, ?)",
            (nom, description, session["user_id"])
        )
        commit()
        flash("Classe créée.", "success")
        return redirect(url_for("classes_list"))

    return render_template("classes-create.html")


@app.route("/classes/<int:class_id>/edit", methods=["GET", "POST"])
@role_required("enseignant")
def classes_edit(class_id):
    classe = query(
        "SELECT * FROM classe WHERE id = ? AND id_enseignant = ?",
        (class_id, session["user_id"])
    ).fetchone()

    if not classe:
        abort(404)

    if request.method == "POST":
        nom         = request.form.get("nom", "").strip()
        description = request.form.get("description", "").strip()

        if not nom:
            flash("Nom de classe requis.", "error")
            return render_template("classes-edit.html", classe=classe)

        query(
            "UPDATE classe SET nom = ?, description = ? WHERE id = ?",
            (nom, description, class_id)
        )
        commit()
        flash("Classe mise à jour.", "success")
        return redirect(url_for("classes_list"))

    return render_template("classes-edit.html", classe=classe)


@app.route("/classes/<int:class_id>/students")
@role_required("enseignant")
def classes_students(class_id):
    classe = query(
        "SELECT * FROM classe WHERE id = ? AND id_enseignant = ?",
        (class_id, session["user_id"])
    ).fetchone()

    if not classe:
        abort(404)

    students = query(
        """SELECT u.id, u.nom, u.prenom, u.email, u.date_creation
           FROM classe_etudiant ce
           JOIN utilisateur u ON u.id = ce.id_etudiant
           WHERE ce.id_classe = ?
           ORDER BY u.nom, u.prenom""",
        (class_id,)
    ).fetchall()

    all_students = query(
        """SELECT id, nom, prenom, email
           FROM utilisateur
           WHERE role = 'etudiant' AND actif = 1 AND id NOT IN (
               SELECT id_etudiant FROM classe_etudiant WHERE id_classe = ?
           )
           ORDER BY nom, prenom""",
        (class_id,)
    ).fetchall()

    return render_template("classes-students.html", classe=classe,
                           students=students, all_students=all_students)


@app.route("/classes/<int:class_id>/add-student", methods=["POST"])
@role_required("enseignant")
def classes_add_student(class_id):
    classe = query(
        "SELECT id FROM classe WHERE id = ? AND id_enseignant = ?",
        (class_id, session["user_id"])
    ).fetchone()

    if not classe:
        abort(403)

    student_id = request.form.get("student_id", type=int)
    if not student_id:
        abort(400)

    try:
        query(
            "INSERT INTO classe_etudiant (id_classe, id_etudiant) VALUES (?, ?)",
            (class_id, student_id)
        )
        commit()
        flash("Étudiant ajouté.", "success")
    except Exception:
        flash("Étudiant déjà dans la classe.", "error")

    return redirect(url_for("classes_students", class_id=class_id))


@app.route("/classes/<int:class_id>/remove-student/<int:student_id>", methods=["POST"])
@role_required("enseignant")
def classes_remove_student(class_id, student_id):
    classe = query(
        "SELECT id FROM classe WHERE id = ? AND id_enseignant = ?",
        (class_id, session["user_id"])
    ).fetchone()

    if not classe:
        abort(403)

    query(
        "DELETE FROM classe_etudiant WHERE id_classe = ? AND id_etudiant = ?",
        (class_id, student_id)
    )
    commit()
    flash("Étudiant retiré.", "success")
    return redirect(url_for("classes_students", class_id=class_id))


# ─────────────────────────────────────────────
# ROUTES — DASHBOARD
# ─────────────────────────────────────────────

@app.route("/dashboard")
@role_required("enseignant", "admin")
def dashboard():
    page   = request.args.get("page", 1, type=int)
    statut = request.args.get("statut", "all")
    offset = (page - 1) * PER_PAGE

    if statut in ("actif", "archive"):
        quiz_list = query(
            """SELECT q.id, q.titre, q.statut, q.date_creation,
                      COUNT(DISTINCT qst.id) AS nb_questions,
                      COUNT(DISTINCT p.id)   AS nb_participations
               FROM quiz q
               LEFT JOIN question    qst ON qst.id_quiz = q.id
               LEFT JOIN participation p ON p.id_quiz  = q.id
               WHERE q.id_createur = ? AND q.statut = ?
               GROUP BY q.id
               ORDER BY q.date_creation DESC
               LIMIT ? OFFSET ?""",
            (session["user_id"], statut, PER_PAGE, offset)
        ).fetchall()
    else:
        quiz_list = query(
            """SELECT q.id, q.titre, q.statut, q.date_creation,
                      COUNT(DISTINCT qst.id) AS nb_questions,
                      COUNT(DISTINCT p.id)   AS nb_participations
               FROM quiz q
               LEFT JOIN question    qst ON qst.id_quiz = q.id
               LEFT JOIN participation p ON p.id_quiz  = q.id
               WHERE q.id_createur = ?
               GROUP BY q.id
               ORDER BY q.date_creation DESC
               LIMIT ? OFFSET ?""",
            (session["user_id"], PER_PAGE, offset)
        ).fetchall()

    stats = query(
        """SELECT
             SUM(CASE WHEN q.statut='actif'   THEN 1 ELSE 0 END) AS actifs,
             SUM(CASE WHEN q.statut='archive' THEN 1 ELSE 0 END) AS archives,
             COUNT(DISTINCT p.id)                                  AS total_participations,
             ROUND(AVG(p.score), 1)                               AS score_moyen
           FROM quiz q
           LEFT JOIN participation p ON p.id_quiz = q.id
           WHERE q.id_createur = ?""",
        (session["user_id"],)
    ).fetchone()

    return render_template("dashboard.html",
                           quiz_list=quiz_list,
                           stats=stats,
                           page=page,
                           statut=statut)


# ─────────────────────────────────────────────
# ROUTES — QUIZ
# ─────────────────────────────────────────────

@app.route("/quiz")
@login_required
def quiz_list():
    page   = request.args.get("page", 1, type=int)
    offset = (page - 1) * PER_PAGE

    quizzes = query(
        """SELECT q.id, q.titre, q.description,
                  COUNT(DISTINCT qst.id) AS nb_questions,
                  u.prenom || ' ' || u.nom AS createur
           FROM quiz q
           JOIN utilisateur u ON u.id = q.id_createur
           LEFT JOIN question qst ON qst.id_quiz = q.id
           WHERE q.statut = 'actif'
           GROUP BY q.id
           ORDER BY q.date_creation DESC
           LIMIT ? OFFSET ?""",
        (PER_PAGE, offset)
    ).fetchall()

    return render_template("quiz-list.html", quizzes=quizzes, page=page)


@app.route("/quiz/create", methods=["GET", "POST"])
@role_required("enseignant", "admin")
def quiz_create():
    if request.method == "POST":
        titre       = request.form.get("titre", "").strip()
        description = request.form.get("description", "").strip()
        duree       = request.form.get("duree_minutes", "60", type=int)
        statut      = request.form.get("statut", "actif")

        if not titre:
            flash("Le titre est requis.", "error")
            return render_template("quiz-create.html")

        if duree < 1:
            duree = 60

        questions = []
        i = 0
        while f"questions[{i}][texte]" in request.form:
            texte = request.form.get(f"questions[{i}][texte]", "").strip()
            opts  = [request.form.get(f"questions[{i}][options][{j}]", "") for j in range(4)]
            rep   = request.form.get(f"questions[{i}][index_bonne_rep]", "")
            if texte and all(opts) and rep.isdigit():
                questions.append((texte, json.dumps(opts), int(rep)))
            i += 1

        if len(questions) < 2:
            flash("Ajoutez au moins 2 questions.", "error")
            return render_template("quiz-create.html")

        # INSERT avec récupération de l'ID (compatible SQLite et PostgreSQL)
        if getattr(g, "_db_type", "sqlite") == "postgres":
            cur = query(
                "INSERT INTO quiz (titre, description, duree_minutes, statut, id_createur) VALUES (?,?,?,?,?) RETURNING id",
                (titre, description, duree, statut, session["user_id"])
            )
            quiz_id = cur.fetchone()["id"]
        else:
            cur = query(
                "INSERT INTO quiz (titre, description, duree_minutes, statut, id_createur) VALUES (?,?,?,?,?)",
                (titre, description, duree, statut, session["user_id"])
            )
            quiz_id = cur.lastrowid

        query_many(
            "INSERT INTO question (id_quiz, texte, options, index_bonne_rep) VALUES (?,?,?,?)",
            [(quiz_id, t, o, r) for t, o, r in questions]
        )
        commit()
        flash("Quiz créé avec succès !", "success")
        return redirect(url_for("dashboard"))

    return render_template("quiz-create.html")


@app.route("/quiz/<int:quiz_id>/edit", methods=["GET", "POST"])
@role_required("enseignant", "admin")
def quiz_edit(quiz_id):
    quiz = query("SELECT * FROM quiz WHERE id = ?", (quiz_id,)).fetchone()

    if not quiz:
        abort(404)
    if quiz["id_createur"] != session["user_id"] and session["role"] != "admin":
        abort(403)

    if request.method == "POST":
        titre       = request.form.get("titre", "").strip()
        description = request.form.get("description", "").strip()
        statut      = request.form.get("statut", "actif")

        if not titre:
            flash("Le titre est requis.", "error")
        else:
            query(
                "UPDATE quiz SET titre=?, description=?, statut=? WHERE id=?",
                (titre, description, statut, quiz_id)
            )
            commit()
            flash("Quiz mis à jour.", "success")
            return redirect(url_for("dashboard"))

    questions = query(
        "SELECT * FROM question WHERE id_quiz = ? ORDER BY id", (quiz_id,)
    ).fetchall()
    return render_template("quiz-edit.html", quiz=quiz, questions=questions)


@app.route("/quiz/<int:quiz_id>/archive", methods=["POST"])
@role_required("enseignant", "admin")
def quiz_archive(quiz_id):
    quiz = query("SELECT id_createur FROM quiz WHERE id = ?", (quiz_id,)).fetchone()
    if not quiz or (quiz["id_createur"] != session["user_id"] and session["role"] != "admin"):
        abort(403)
    query("UPDATE quiz SET statut='archive' WHERE id=?", (quiz_id,))
    commit()
    flash("Quiz archivé.", "success")
    return redirect(url_for("dashboard"))


@app.route("/quiz/<int:quiz_id>/activate", methods=["POST"])
@role_required("enseignant", "admin")
def quiz_activate(quiz_id):
    quiz = query("SELECT id_createur FROM quiz WHERE id = ?", (quiz_id,)).fetchone()
    if not quiz or (quiz["id_createur"] != session["user_id"] and session["role"] != "admin"):
        abort(403)
    query("UPDATE quiz SET statut='actif' WHERE id=?", (quiz_id,))
    commit()
    flash("Quiz réactivé.", "success")
    return redirect(url_for("dashboard"))


@app.route("/quiz/<int:quiz_id>/delete", methods=["POST"])
@role_required("enseignant", "admin")
def quiz_delete(quiz_id):
    quiz = query("SELECT id_createur FROM quiz WHERE id = ?", (quiz_id,)).fetchone()
    if not quiz or (quiz["id_createur"] != session["user_id"] and session["role"] != "admin"):
        abort(403)
    query("DELETE FROM quiz WHERE id=?", (quiz_id,))
    commit()
    flash("Quiz supprimé.", "success")
    return redirect(url_for("dashboard"))


@app.route("/quiz/<int:quiz_id>/take")
@role_required("etudiant")
def quiz_take(quiz_id):
    quiz = query(
        "SELECT * FROM quiz WHERE id = ? AND statut = 'actif'", (quiz_id,)
    ).fetchone()
    if not quiz:
        abort(404)

    if not can_student_take_quiz(session["user_id"], quiz_id):
        flash("Vous n'avez pas accès à ce quiz.", "error")
        return redirect(url_for("quiz_list"))

    already = query(
        "SELECT id FROM participation WHERE id_quiz=? AND id_etudiant=?",
        (quiz_id, session["user_id"])
    ).fetchone()
    if already:
        flash("Vous avez déjà passé ce quiz.", "error")
        return redirect(url_for("scores"))

    questions = query(
        "SELECT id, texte, options FROM question WHERE id_quiz=? ORDER BY id",
        (quiz_id,)
    ).fetchall()

    questions_parsed = []
    for q in questions:
        questions_parsed.append({
            "id":      q["id"],
            "texte":   q["texte"],
            "options": json.loads(q["options"])
        })

    return render_template("quiz-take.html", quiz=quiz, questions=questions_parsed)


@app.route("/quiz/<int:quiz_id>/submit", methods=["POST"])
@role_required("etudiant")
def quiz_submit(quiz_id):
    quiz = query("SELECT * FROM quiz WHERE id=? AND statut='actif'", (quiz_id,)).fetchone()
    if not quiz:
        abort(404)

    if not can_student_take_quiz(session["user_id"], quiz_id):
        abort(403)

    questions = query(
        "SELECT id, index_bonne_rep FROM question WHERE id_quiz=?", (quiz_id,)
    ).fetchall()

    score = 0
    for q in questions:
        answer = request.form.get(f"q[{q['id']}]", "")
        if answer.isdigit() and int(answer) == q["index_bonne_rep"]:
            score += 1

    score_sur_10 = round((score / len(questions)) * 10, 1) if questions else 0

    try:
        query(
            "INSERT INTO participation (id_quiz, id_etudiant, score) VALUES (?,?,?)",
            (quiz_id, session["user_id"], score_sur_10)
        )
        commit()
    except Exception:
        flash("Vous avez déjà soumis ce quiz.", "error")
        return redirect(url_for("scores"))

    flash(f"Quiz soumis ! Votre score : {score_sur_10}/10", "success")
    return redirect(url_for("scores"))


# ─────────────────────────────────────────────
# ROUTES — SCORES
# ─────────────────────────────────────────────

@app.route("/scores")
@login_required
def scores():
    role   = session.get("role")
    page   = request.args.get("page", 1, type=int)
    offset = (page - 1) * PER_PAGE

    if role == "etudiant":
        rows = query(
            """SELECT p.score, p.date_passage, q.titre
               FROM participation p
               JOIN quiz q ON q.id = p.id_quiz
               WHERE p.id_etudiant = ?
               ORDER BY p.date_passage DESC
               LIMIT ? OFFSET ?""",
            (session["user_id"], PER_PAGE, offset)
        ).fetchall()
        return render_template("scores.html", rows=rows, role=role, page=page)

    quiz_id    = request.args.get("quiz_id", type=int)
    my_quizzes = query(
        "SELECT id, titre FROM quiz WHERE id_createur=? ORDER BY date_creation DESC",
        (session["user_id"],)
    ).fetchall()

    if not quiz_id and my_quizzes:
        quiz_id = my_quizzes[0]["id"]

    rows  = []
    stats = None
    if quiz_id:
        rows = query(
            """SELECT u.nom, u.prenom, p.score, p.date_passage
               FROM participation p
               JOIN utilisateur u ON u.id = p.id_etudiant
               WHERE p.id_quiz = ?
               ORDER BY p.score DESC
               LIMIT ? OFFSET ?""",
            (quiz_id, PER_PAGE, offset)
        ).fetchall()

        stats = query(
            """SELECT COUNT(*) AS nb, ROUND(AVG(score),1) AS moyenne,
                      MAX(score) AS max, MIN(score) AS min
               FROM participation WHERE id_quiz=?""",
            (quiz_id,)
        ).fetchone()

    return render_template("scores.html",
                           rows=rows, role=role,
                           my_quizzes=my_quizzes,
                           selected_quiz=quiz_id,
                           stats=stats, page=page)


@app.route("/quiz/<int:quiz_id>/export-csv")
@role_required("enseignant", "admin")
def export_csv(quiz_id):
    quiz = query("SELECT titre, id_createur FROM quiz WHERE id=?", (quiz_id,)).fetchone()
    if not quiz or (quiz["id_createur"] != session["user_id"] and session["role"] != "admin"):
        abort(403)

    rows = query(
        """SELECT u.nom, u.prenom, u.email, p.score, p.date_passage
           FROM participation p JOIN utilisateur u ON u.id=p.id_etudiant
           WHERE p.id_quiz=? ORDER BY p.score DESC""",
        (quiz_id,)
    ).fetchall()

    lines = ["Nom,Prénom,Email,Score,Date"]
    for r in rows:
        lines.append(f"{r['nom']},{r['prenom']},{r['email']},{r['score']},{r['date_passage']}")

    resp = make_response("\n".join(lines))
    resp.headers["Content-Type"]        = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = f"attachment; filename=scores-quiz-{quiz_id}.csv"
    return resp


# ─────────────────────────────────────────────
# ROUTES — ADMIN UTILISATEURS (CRUD)
# ─────────────────────────────────────────────

@app.route("/admin/users")
@role_required("admin")
def admin_users():
    page   = request.args.get("page", 1, type=int)
    role_f = request.args.get("role", "")
    search = request.args.get("q", "").strip()
    offset = (page - 1) * PER_PAGE

    sql    = "SELECT id, nom, prenom, email, role, actif, date_creation FROM utilisateur WHERE 1=1"
    params = []

    if role_f in ("etudiant", "enseignant", "admin"):
        sql += " AND role = ?"
        params.append(role_f)
    if search:
        sql += " AND (nom LIKE ? OR prenom LIKE ? OR email LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like])

    sql += " ORDER BY date_creation DESC LIMIT ? OFFSET ?"
    params.extend([PER_PAGE, offset])

    users = query(sql, params).fetchall()
    return render_template("admin-users.html", users=users, page=page,
                           role_f=role_f, search=search)


@app.route("/admin/users/create", methods=["GET", "POST"])
@role_required("admin")
def admin_user_create():
    if request.method == "POST":
        nom    = request.form.get("nom", "").strip()
        prenom = request.form.get("prenom", "").strip()
        email  = request.form.get("email", "").strip().lower()
        role   = request.form.get("role", "etudiant")
        pwd    = request.form.get("password", "")

        errors = []
        if not nom:    errors.append("Nom requis.")
        if not prenom: errors.append("Prénom requis.")
        if not email or "@" not in email: errors.append("Email invalide.")
        if len(pwd) < 8: errors.append("Mot de passe trop court.")
        if role not in ("etudiant", "enseignant", "admin"): errors.append("Rôle invalide.")

        if not errors and query("SELECT id FROM utilisateur WHERE email=?", (email,)).fetchone():
            errors.append("Email déjà utilisé.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("admin-user-create.html")

        hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
        query(
            "INSERT INTO utilisateur (nom,prenom,email,mot_de_passe,role,actif) VALUES (?,?,?,?,?,?)",
            (nom, prenom, email, hashed, role, 1)
        )
        commit()
        flash(f"Utilisateur {prenom} {nom} créé.", "success")
        return redirect(url_for("admin_users"))

    return render_template("admin-user-create.html")


@app.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def admin_user_edit(user_id):
    user = query(
        "SELECT id, nom, prenom, email, role FROM utilisateur WHERE id=?", (user_id,)
    ).fetchone()
    if not user:
        abort(404)

    if request.method == "POST":
        nom    = request.form.get("nom", "").strip()
        prenom = request.form.get("prenom", "").strip()
        email  = request.form.get("email", "").strip().lower()
        role   = request.form.get("role", "etudiant")

        errors = []
        if not nom:    errors.append("Nom requis.")
        if not prenom: errors.append("Prénom requis.")
        if not email or "@" not in email: errors.append("Email invalide.")

        conflict = query(
            "SELECT id FROM utilisateur WHERE email=? AND id!=?", (email, user_id)
        ).fetchone()
        if conflict:
            errors.append("Email déjà utilisé.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("admin-user-edit.html", user=user)

        query(
            "UPDATE utilisateur SET nom=?, prenom=?, email=?, role=? WHERE id=?",
            (nom, prenom, email, role, user_id)
        )
        commit()
        flash("Utilisateur mis à jour.", "success")
        return redirect(url_for("admin_users"))

    return render_template("admin-user-edit.html", user=user)


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@role_required("admin")
def admin_user_delete(user_id):
    if user_id == session["user_id"]:
        flash("Vous ne pouvez pas supprimer votre propre compte.", "error")
        return redirect(url_for("admin_users"))

    query("DELETE FROM utilisateur WHERE id=?", (user_id,))
    commit()
    flash("Utilisateur supprimé.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
@role_required("admin")
def admin_user_toggle(user_id):
    user = query("SELECT actif FROM utilisateur WHERE id=?", (user_id,)).fetchone()
    if not user:
        abort(404)

    new_actif = 1 if not user["actif"] else 0
    query("UPDATE utilisateur SET actif=? WHERE id=?", (new_actif, user_id))
    commit()

    status = "activé" if new_actif else "désactivé"
    flash(f"Compte utilisateur {status}.", "success")
    return redirect(url_for("admin_users"))


# ─────────────────────────────────────────────
# ERREURS
# ─────────────────────────────────────────────

@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403, msg="Accès interdit."), 403

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, msg="Page introuvable."), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, msg="Erreur serveur."), 500


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_ENV") == "development")