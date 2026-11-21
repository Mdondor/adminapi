# Image de base : Python 3.12 en version allégée
FROM python:3.12-slim

# Dossier de travail dans le conteneur ; les commandes suivantes s'y exécutent
WORKDIR /app

# Copie de la liste des dépendances seule, pour que Docker réutilise son cache si elle ne change pas
COPY requirements.txt .

# Installation des dépendances, sans garder le cache de pip pour alléger l'image
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code de l'API uniquement : ni .env, ni .venv, ni les autres fichiers du projet
COPY app/ app/

# Démarrage d'uvicorn ; --host 0.0.0.0 rend l'API joignable depuis l'extérieur du conteneur
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
