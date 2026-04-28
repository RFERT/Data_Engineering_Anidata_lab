# Data Engineering 101 — AniData Lab

Ce projet est un mini-pipeline ETL de traitement de données pour un dataset anime/manga.
Il combine Airflow, Python, Elasticsearch et Grafana pour transformer, indexer et visualiser les données.

## Contenu du projet

- `airflow/dags/` : définitions des DAGs Airflow
- `airflow/scripts/` : scripts Python de traitement (`extract`, `transform`, `load`, `anomaly`)
- `data/` : jeux de données sources et fichiers générés
- `tests/` : tests unitaires pytest
- `.github/workflows/ci.yml` : workflow CI pour lint et tests
- `docker-compose.yml` : orchestration des services Docker
- `grafana/` : dashboards et provisioning Grafana
- `elk/` : configuration Logstash pour ingestion Elasticsearch

## Objectif

Le pipeline vise à :

1. Extraire des CSV bruts
2. Nettoyer et enrichir les données
3. Indexer le jeu de données final dans Elasticsearch
4. Détecter des anomalies sur les notes et les comportements utilisateurs
5. Automatiser avec Airflow et CI

## Prérequis

- Python 3.10+
- Docker et Docker Compose
- Git

## Installation rapide

1. Ouvrir le projet dans VS Code
2. Installer les dépendances de développement :

```bash
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

3. Placer les fichiers sources dans `data/` :

- `anime.csv`
- `anime_with_synopsis.csv`
- `rating_complete.csv`

4. Lancer les services Docker :

```bash
docker compose up -d
```

## Exécution locale

### Tester le code

```bash
pytest tests -q
```

### Lancer Airflow

```bash
docker compose up -d
```

Puis ouvrir :

- Airflow : http://localhost:8080
- Grafana : http://localhost:3000
- Elasticsearch : http://localhost:9200

## Structure du pipeline

- `extract` : lit les CSV, crée des fichiers intermédiaires propres
- `transform` : nettoie `anime`, `synopsis`, `ratings`, fusionne les sources et calcule des features
- `load` : indexe le dataset final dans Elasticsearch
- `anomaly` : détecte spam users, mono-raters et review bombing

## Workflow CI

Le fichier `.github/workflows/ci.yml` exécute :

- lint `ruff` sur `airflow/` et `tests/`
- tests pytest sur Python 3.10 et 3.11
- génération d’un rapport de couverture

## Commandes utiles

```bash
pytest tests -q

docker compose up -d
docker compose down
```

## Notes

- Les données brutes doivent être fournies dans `data/`, elles ne sont pas incluses dans le repo.
- GitHub utilise le workflow actif dans `.github/workflows/ci.yml`.
