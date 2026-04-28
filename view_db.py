#!/usr/bin/env python
import sqlite3

conn = sqlite3.connect('database/evalconnect.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Afficher les tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print("=" * 80)
print("TABLES DISPONIBLES:", [t[0] for t in tables])
print("=" * 80)

# 1. UTILISATEURS
print("\n1️⃣  TABLE UTILISATEUR")
print("-" * 80)
c.execute("SELECT id, nom, prenom, email, role, date_creation FROM utilisateur")
users = c.fetchall()
for u in users:
    print(f"ID: {u['id']:2} | {u['prenom']:10} {u['nom']:15} | {u['email']:30} | {u['role']:10} | {u['date_creation']}")

# 2. QUIZ
print("\n2️⃣  TABLE QUIZ")
print("-" * 80)
c.execute("SELECT id, titre, description, statut, id_createur, date_creation FROM quiz")
quizzes = c.fetchall()
for q in quizzes:
    print(f"ID: {q['id']} | {q['titre']:25} | {q['statut']:10} | Createur: {q['id_createur']} | {q['date_creation']}")

# 3. QUESTIONS
print("\n3️⃣  TABLE QUESTION")
print("-" * 80)
c.execute("SELECT id, id_quiz, texte, index_bonne_rep FROM question")
questions = c.fetchall()
for qu in questions:
    print(f"ID: {qu['id']:2} | Quiz: {qu['id_quiz']} | {qu['texte'][:50]:50} | Réponse: {qu['index_bonne_rep']}")

# 4. PARTICIPATIONS (SCORES)
print("\n4️⃣  TABLE PARTICIPATION (SCORES)")
print("-" * 80)
c.execute("""
    SELECT p.id, p.id_quiz, p.id_etudiant, p.score, p.date_passage,
           u.nom, u.prenom, q.titre
    FROM participation p
    JOIN utilisateur u ON u.id = p.id_etudiant
    JOIN quiz q ON q.id = p.id_quiz
    ORDER BY p.date_passage DESC
""")
participations = c.fetchall()
for p in participations:
    print(f"ID: {p['id']} | Quiz: {p['titre']:20} | Étudiant: {p['prenom']} {p['nom']:15} | Score: {p['score']}/10 | {p['date_passage']}")

# Résumé
print("\n" + "=" * 80)
print("RÉSUMÉ")
print("=" * 80)
print(f"Utilisateurs:    {len(users)}")
print(f"Quiz:            {len(quizzes)}")
print(f"Questions:       {len(questions)}")
print(f"Participations:  {len(participations)}")

conn.close()
