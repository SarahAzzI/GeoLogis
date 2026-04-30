## 1. Créer le réseau Docker
```bash
docker network create geologis-network
```

## 2. Récupérer l'image PostgreSQL sur DockerHub
```bash
docker pull postgres:15 ou Docker run postgres:15
```

## 3. Lancer PostgreSQL
```bash
docker run -d \
  --name geologis_postgres \
  --network geologis-network \
  -p 5433:5432 \
  -e POSTGRES_USER=geo \
  -e POSTGRES_PASSWORD=geo123 \
  -e POSTGRES_DB=geologis \
  -v geologis_pgdata:/var/lib/postgresql/data \
  postgres:15
```

## 4. Build et lancer FastAPI
```bash
# Build
docker build \
  -f src/ml_service/Dockerfile \
  -t geologis-ml \
  .

# Lancer
docker run -d \
  --name geologis-ml \
  --network geologis-network \
  -p 8001:8001 \
  -e DATABASE_URL=postgresql://geo:geo123@geologis_postgres:5432/geologis \
  -v $(pwd)/src/data_pipeline:/data_pipeline \
  geologis-ml
```

## 5. Build et lancer Django
```bash
# Build
docker build \
  -f src/django-app/Dockerfile \
  -t geologis-django \
  .

# Lancer
docker run -d \
  --name geologis-django \
  --network geologis-network \
  -p 8000:8000 \
  -e DJANGO_SETTINGS_MODULE=config.settings \
  -v $(pwd)/src/django-app/db.sqlite3:/app/db.sqlite3 \
  geologis-django
```

## 6. Vérifier que tout tourne
```bash
docker ps
```

## 7. Accéder aux services
- Django   → http://localhost:8000
- FastAPI  → http://localhost:8001
- Docs API → http://localhost:8001/docs

---

## Commandes optionnelles

### Arrêter les conteneurs
```bash
docker stop geologis-ml geologis-django geologis_postgres
```

### Supprimer les conteneurs
```bash
docker rm geologis-ml geologis-django geologis_postgres
```

### Voir les logs
```bash
docker logs geologis-ml
docker logs geologis-django
docker logs geologis_postgres
```
EOF