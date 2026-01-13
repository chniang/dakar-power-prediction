FROM python:3.11-slim

# Installer libgomp1 pour LightGBM
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt .
COPY streamlit_app ./streamlit_app
COPY models ./models
COPY data ./data
COPY src ./src
COPY .streamlit ./.streamlit

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port
EXPOSE 8501

# Lancer l'application
CMD ["streamlit", "run", "streamlit_app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
