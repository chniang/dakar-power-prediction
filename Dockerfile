FROM python:3.12-slim

# Installer libgomp1 pour LightGBM
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements-hf.txt .
COPY streamlit_app ./streamlit_app
COPY models ./models
COPY data ./data
COPY src ./src
COPY .streamlit ./.streamlit

# Installer les dependances
RUN pip install --no-cache-dir -r requirements-hf.txt

# Déclarer la page en français et non traduisible : Streamlit sert <html lang="en">,
# ce qui pousse Chrome à « traduire » l'app (ex. « FAIBLE » → « ÉCHEC »).
# Le build échoue si le motif n'est plus trouvé (version de Streamlit changée).
RUN IDX="$(python -c 'import pathlib, streamlit; print(pathlib.Path(streamlit.__file__).parent / "static" / "index.html")')" \
 && sed -i 's#<html lang="en">#<html lang="fr" translate="no">#; s#<head>#<head><meta name="google" content="notranslate">#' "$IDX" \
 && grep -q '<html lang="fr" translate="no">' "$IDX" \
 && grep -q 'content="notranslate"' "$IDX"

# Port 7860 : port attendu par Hugging Face Spaces, identique à .streamlit/config.toml
EXPOSE 7860

# Lancer l'application
CMD ["streamlit", "run", "streamlit_app/app.py", "--server.port=7860", "--server.address=0.0.0.0"]
