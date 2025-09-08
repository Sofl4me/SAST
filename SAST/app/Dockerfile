FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
# On installe aussi gunicorn SANS modifier ton requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 5000

# Healthcheck HTTP interne au conteneur
HEALTHCHECK --interval=5s --timeout=3s --retries=12 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/', timeout=2)" || exit 1

# IMPORTANT : on ne lance PAS python app.py ; on sert l'app Flask via Gunicorn
# Module:Objet => app:app (fichier app.py, objet Flask 'app')
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
