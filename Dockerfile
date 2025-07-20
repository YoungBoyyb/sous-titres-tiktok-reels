FROM python:3.9-slim

# Installer ffmpeg système
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Création utilisateur non root
RUN useradd -m -u 1000 user
USER user

ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copier requirements et installer dépendances
COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copier le code source
COPY --chown=user . /app

# Commande pour démarrer l'app FastAPI avec uvicorn sur le port 8080 (Render utilise 8080)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
