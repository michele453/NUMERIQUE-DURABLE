-- EvalConnect — Données de test
-- Mots de passe : tous "password123" hashés avec bcrypt
-- NE PAS utiliser en production

INSERT INTO utilisateur (nom, prenom, email, mot_de_passe, role, actif) VALUES
  ('Simo',    'michel',  'admin@evalconnect.fr',   '$2b$12$XF2gm4eGRq3GaYgNDQvYXeJRTf/Yge0WrdttgH94t5e3YYsxSzTlG', 'admin', 1),
  ('Temgoua',  'igor',    'Temgoua@evalconnect.fr',  '$2b$12$B0iJJZHhPXY1/ViL9rw2wO.j.FD.gqae5ZYYHfVlhuOmZsXi0KxVW', 'enseignant', 1),
  ('Souza',   'manoel',  'm.souza@evalconnect.fr',  '$2b$12$AD1jlmCmzxVM3AtpTSo9.edAUTpBSGq4ox6A.PEfCPeheBO7sUL1e', 'etudiant', 1),
  ('Regad', 'Assirem',  'a.regad@evalconnect.fr',  '$2b$12$ITbFLJX9HB.sOAh6sjSA7ekts1z57Bhg47DNb9/zoSPqc6u2zWNeS', 'etudiant', 1);

-- Créer des classes
INSERT INTO classe (nom, description, id_enseignant) VALUES
  ('Informatique L1', 'Licence informatique 1ère année', 2),
  ('Informatique L2', 'Licence informatique 2ème année', 2),
  ('Mathématiques L1', 'Licence mathématiques 1ère année', 2);

-- Ajouter les étudiants aux classes
INSERT INTO classe_etudiant (id_classe, id_etudiant) VALUES
  (1, 3),
  (1, 4),
  (2, 3);

-- Créer les quiz avec durée
INSERT INTO quiz (titre, description, duree_minutes, statut, id_createur) VALUES
  ('Quiz Math 1',  'Bases du calcul différentiel', 45, 'actif',   2),
  ('Quiz Phys 2',  'Mécanique newtonienne',        60, 'actif',   2),
  ('Quiz Info 3',  'Algorithmique de base',        90, 'actif',   2),
  ('Quiz Maths 0', 'Version archivée',             30, 'archive', 2);

-- Lier les quiz aux classes (contrôle d'accès)
INSERT INTO quiz_classe (id_quiz, id_classe) VALUES
  (1, 1),  -- Quiz Math 1 pour la classe Informatique L1
  (3, 1),  -- Quiz Info 3 pour la classe Informatique L1
  (3, 2);  -- Quiz Info 3 aussi pour Informatique L2

-- Insérer les questions
INSERT INTO question (id_quiz, texte, options, index_bonne_rep) VALUES
  (1, 'Quelle est la dérivée de f(x) = x² ?',
      '["f(x) = x","f(x) = 2x","f(x) = x²","f(x) = 2"]', 1),
  (1, 'Quelle est la dérivée de f(x) = sin(x) ?',
      '["cos(x)","-sin(x)","tan(x)","1"]', 0),
  (1, 'Que vaut la dérivée d une constante ?',
      '["1","La constante","0","Indéfini"]', 2),
  (2, 'Quelle est la formule de la force ?',
      '["F = m/a","F = m+a","F = m*a","F = a/m"]', 2),
  (2, 'Unité de la force dans le SI ?',
      '["Joule","Pascal","Newton","Watt"]', 2);

-- Insérer les scores
INSERT INTO participation (id_quiz, id_etudiant, score) VALUES
  (1, 3, 9.0),
  (1, 4, 8.0),
  (2, 3, 7.0);
