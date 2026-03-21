# Runbook Production — AO Copilot

## Health Checks

```bash
# API health
curl -s https://ao-copilot.fr/api/v1/health | jq

# Services Docker
docker compose -f docker-compose.production.yml ps

# Logs temps réel
docker compose -f docker-compose.production.yml logs -f --tail=50
```

## Monitoring Celery

```bash
# Workers actifs
docker compose -f docker-compose.production.yml exec api \
  celery -A app.worker.celery inspect active

# Tâches réservées
docker compose -f docker-compose.production.yml exec api \
  celery -A app.worker.celery inspect reserved

# Profondeur de la queue
docker compose -f docker-compose.production.yml exec redis redis-cli LLEN celery

# Tâches échouées (Redis)
docker compose -f docker-compose.production.yml exec redis redis-cli KEYS "celery-task-meta-*" | wc -l
```

## Monitoring PostgreSQL

```bash
# Connexions actives
docker compose -f docker-compose.production.yml exec postgres \
  psql -U aocopilot -c "SELECT count(*) as connexions FROM pg_stat_activity;"

# Taille de la base
docker compose -f docker-compose.production.yml exec postgres \
  psql -U aocopilot -c "SELECT pg_size_pretty(pg_database_size('aocopilot'));"

# Requêtes lentes (> 5s)
docker compose -f docker-compose.production.yml exec postgres \
  psql -U aocopilot -c "SELECT pid, now() - query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' AND now() - query_start > interval '5 seconds';"

# Tables les plus volumineuses
docker compose -f docker-compose.production.yml exec postgres \
  psql -U aocopilot -c "SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) AS size FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 10;"
```

## Maintenance Base de Données

### Hebdomadaire
```bash
# VACUUM ANALYZE (récupère l'espace, met à jour les statistiques)
docker compose -f docker-compose.production.yml exec postgres \
  psql -U aocopilot -c "VACUUM ANALYZE;"
```

### Mensuelle
```bash
# Reindex (optimise les index)
docker compose -f docker-compose.production.yml exec postgres \
  psql -U aocopilot -c "REINDEX DATABASE aocopilot;"

# Vérifier la fragmentation des index
docker compose -f docker-compose.production.yml exec postgres \
  psql -U aocopilot -c "SELECT schemaname, tablename, indexname, pg_size_pretty(pg_relation_size(indexrelid)) FROM pg_stat_user_indexes ORDER BY pg_relation_size(indexrelid) DESC LIMIT 20;"
```

## Sentry — Alertes Recommandées

| Alerte | Condition | Action |
|--------|-----------|--------|
| Erreur 500 spike | > 10 erreurs/min | Investiguer les logs API |
| LLM timeout | > 5 timeouts/heure | Vérifier Anthropic status |
| Queue saturée | > 100 tâches pending | Scale les workers |
| DB connexions | > 80% max_connections | Vérifier les leaks |
| Disque > 85% | df -h | Purger les backups/logs |

## Rotation des Clés API

### Anthropic / OpenAI
1. Générer une nouvelle clé sur la console du provider
2. Mettre à jour `.env.production` avec la nouvelle clé
3. Redémarrer les services : `docker compose -f docker-compose.production.yml restart api worker`
4. Vérifier les logs : pas d'erreur 401
5. Révoquer l'ancienne clé sur la console

### Stripe
1. Dashboard Stripe → Développeurs → Clés API
2. Régénérer la clé secrète (la publishable ne change pas)
3. Mettre à jour `STRIPE_SECRET_KEY` dans `.env.production`
4. Mettre à jour `STRIPE_WEBHOOK_SECRET` si le webhook est recréé
5. Redémarrer : `docker compose restart api`
6. Tester un paiement de 1€ puis rembourser

### JWT RS256
```bash
# Générer une nouvelle paire de clés
openssl genrsa -out private_new.pem 2048
openssl rsa -in private_new.pem -pubout -out public_new.pem

# Mettre à jour .env.production (JWT_PRIVATE_KEY, JWT_PUBLIC_KEY)
# Redémarrer l'API
# Note : les tokens existants avec l'ancienne clé seront invalides
# Les utilisateurs devront se reconnecter (durée max : 15 min)
```

## Disaster Recovery

### RTO / RPO
- **RPO** (Recovery Point Objective) : 24h (backup quotidien à 3h)
- **RTO** (Recovery Time Objective) : 2h (restore depuis S3 + redémarrage Docker)

### Procédure de restauration complète

```bash
# 1. Provisionner un nouveau VPS (Hostinger KVM 2)
# 2. Exécuter le setup initial
bash scripts/setup-vps.sh

# 3. Cloner le repo
git clone https://github.com/adama-sas/ao-copilot.git /opt/ao-copilot
cd /opt/ao-copilot

# 4. Restaurer le .env.production (depuis un backup sécurisé)
cp /path/to/backup/.env.production .env.production

# 5. Démarrer les services
bash scripts/deploy.sh

# 6. Restaurer la base de données
aws s3 cp s3://aocopilot-backups/db/DERNIER_BACKUP.sql.gz /tmp/restore.sql.gz \
  --endpoint-url https://s3.fr-par.scw.cloud
gunzip -c /tmp/restore.sql.gz | docker compose -f docker-compose.production.yml \
  exec -T postgres psql -U aocopilot aocopilot

# 7. Configurer SSL
bash scripts/setup-ssl.sh ao-copilot.fr

# 8. Vérifier
curl https://ao-copilot.fr/api/v1/health
```

## Rate Limits API

| Endpoint | Limite | Fenêtre |
|----------|--------|---------|
| `/api/v1/auth/login` | 5 requêtes | 1 minute |
| `/api/v1/auth/register` | 3 requêtes | 1 minute |
| `/api/v1/analysis/*` | 20 requêtes | 1 minute |
| `/api/v1/export/*` | 10 requêtes | 1 minute |
| `/api/v1/chat/*` | 30 requêtes | 1 minute |
| Autres endpoints | 60 requêtes | 1 minute |

## Load Testing

```bash
# Installer locust (si pas déjà fait)
pip install locust>=2.20.0

# Lancer le test de charge
locust -f scripts/load_test.py --host=https://ao-copilot.fr \
  --users=50 --spawn-rate=5 --run-time=5m --headless

# Seuils de performance attendus
# - P95 < 2s pour les endpoints standard
# - P95 < 30s pour les analyses IA
# - P99 < 5s pour les exports
# - 0% erreurs 5xx sous 50 users concurrents
```
