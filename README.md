EvalConnect est une application d'évaluation en ligne construite avec Flask et SQLite. Elle permet aux enseignants et aux administrateurs de créer des quiz, gérer des classes et consulter les scores, tandis que les étudiants peuvent se connecter, répondre aux quiz et voir leurs résultats.

## Fonctionnalités principales

- Gestion des utilisateurs : étudiants, enseignants et administrateurs
- Inscription et connexion sécurisées avec hash bcrypt
- Création, mise à jour, archivage et suppression de quiz
- Ajout dynamique de questions et options pour chaque quiz
- Passage de quiz par les étudiants avec score calculé et stockage en base
- Dashboard enseignant avec statistiques et liste des quiz
- Page d'administration des utilisateurs pour CRUD et activation/désactivation
- Export CSV des scores d'un quiz

## Architecture

- `backend/app.py` : application Flask principale
- `backend/config.py` : configuration de l'application et chargement des variables d'environnement
- `backend/static/` : fichiers CSS et JavaScript
- `backend/templates/` : pages HTML Jinja2
- `database/schema.sql` : schéma SQLite
- `database/seed.sql` : données de test initiales

## Installation

1. Créez et activez un environnement virtuel (PowerShell) :

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Installez les dépendances :

   ```powershell
   pip install -r requirements.txt
   ```

3. Copiez le fichier d'exemple d'environnement :

   ```powershell
   copy .env.example .env
   ```

4. Vérifiez que `SECRET_KEY` est défini dans `.env`.

## Initialisation de la base de données

Depuis la racine du projet, lancez :

```powershell
$env:FLASK_APP = 'backend.app'
$env:FLASK_ENV = 'development'
flask init-db
flask seed-db
```

Le fichier de base de données SQLite est créé dans `database/evalconnect.db`.

## Lancement de l'application

Depuis la racine du projet :

```powershell
$env:FLASK_APP = 'backend.app'
$env:FLASK_ENV = 'development'
flask run
```

L'application sera accessible sur `http://127.0.0.1:5000`.

## Utilisation

- `/auth/register` : inscription
- `/auth/login` : connexion
- `/quiz` : liste des quiz disponibles
- `/dashboard` : tableau de bord enseignant
- `/admin/users` : administration des utilisateurs

## Notes

- Le projet utilise SQLite pour le stockage des données.
- Le mot de passe utilisateur est haché avec bcrypt.
- Le fichier `.env.example` contient une base pour la configuration.

## Améliorations possibles

- Ajout de tests automatisés
- Envoi d'emails de validation
- Gestion des permissions plus fine et rôles supplémentaires
- Interface plus riche pour l'édition de quiz