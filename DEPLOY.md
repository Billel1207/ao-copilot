# Guide de déploiement — AO Copilot sur Hostinger VPS

## Prérequis avant de commencer

- [ ] Compte Hostinger créé sur [hostinger.fr](https://www.hostinger.fr)
- [ ] VPS acheté (recommandé : **KVM 2** ou supérieur — 2 vCPU, 8 Go RAM, Ubuntu 22.04)
- [ ] Domaine acheté (ex: `ao-copilot.fr`) et pointé vers l'IP du VPS
- [ ] Toutes les clés API disponibles (Stripe live, Anthropic, OpenAI, Scaleway S3)

---

## Étape 1 — Achat du VPS Hostinger

1. Va sur **hostinger.fr → VPS Hosting**
2. Choisis le plan **KVM 2** (8 Go RAM) minimum — l'IA consomme de la mémoire
3. Sélectionne **Ubuntu 22.04** comme OS
4. Note l'**adresse IP** du VPS (ex: `123.45.67.89`)

---

## Étape 2 — Pointer le domaine vers le VPS

Dans le panneau DNS Hostinger (ou ton registrar) :

| Type | Nom | Valeur | TTL |
|------|-----|--------|-----|
| A | `@` | `123.45.67.89` (IP du VPS) | 300 |
| A | `www` | `123.45.67.89` | 300 |

> Attends 5-30 min que le DNS se propage avant de continuer.

---

## Étape 3 — Connexion SSH et configuration initiale

```bash
# Connexion en root
ssh root@123.45.67.89

# Télécharger et exécuter le script de configuration
curl -O https://raw.githubusercontent.com/TON-REPO/ao-copilot/main/scripts/setup-vps.sh
bash setup-vps.sh
```

Ce script installe automatiquement :
- Docker + Docker Compose
- L'utilisateur `deploy` avec accès Docker
- Firewall UFW (SSH + HTTP + HTTPS uniquement)
- Fail2Ban (protection brute-force)

---

## Étape 4 — Cloner le dépôt Git

```bash
# Se connecter en tant que deploy
su - deploy

# Cloner le repo
git clone https://github.com/TON-COMPTE/ao-copilot.git /opt/ao-copilot
cd /opt/ao-copilot
```

> Si le repo est privé, ajoute une clé SSH deploy :
> ```bash
> ssh-keygen -t ed25519 -C "deploy@ao-copilot" -f ~/.ssh/deploy_key -N ""
> cat ~/.ssh/deploy_key.pub
> # Ajouter cette clé dans GitHub → Settings → Deploy Keys
> ```

---

## Étape 5 — Créer le fichier .env.production

```bash
cp .env.production.example .env.production
nano .env.production
```

**Variables OBLIGATOIRES à remplir :**

```env
# Domaine
DOMAIN=ao-copilot.fr

# Générer : python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=GENERER_UNE_CLE_SECRETE_ICI

# Base de données
POSTGRES_PASSWORD=MOT_DE_PASSE_SECURISE

# Redis
REDIS_PASSWORD=MOT_DE_PASSE_REDIS

# IA
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...

# Stockage S3 (Scaleway Paris)
S3_ENDPOINT_URL=https://s3.fr-par.scw.cloud
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_BUCKET_NAME=aocopilot-documents

# Stripe LIVE
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_STARTER=price_1T91pk01CSvduw4lL6SWbVbY
STRIPE_PRICE_PRO=price_1T91sX01CSvduw4lZmn5tDEd
STRIPE_PRICE_EUROPE=price_1T91vb01CSvduw4lFd3RvNL6

# Email (Resend)
RESEND_API_KEY=re_...
EMAIL_FROM=noreply@ao-copilot.fr
```

---

## Étape 6 — Configurer Nginx (HTTP d'abord)

Le fichier `nginx/conf.d/ao-copilot.conf` est déjà préconfiguré.
Remplace `votre-domaine.com` par ton vrai domaine :

```bash
sed -i 's/votre-domaine.com/ao-copilot.fr/g' nginx/conf.d/ao-copilot.conf
```

---

## Étape 7 — Premier déploiement

```bash
cd /opt/ao-copilot
bash scripts/deploy.sh
```

Ce script :
1. Pull le code (git)
2. Build les images Docker
3. Lance PostgreSQL + Redis
4. Applique les migrations Alembic
5. Lance tous les services

> ⏱ Le premier build prend **10-15 min** (téléchargement des images Docker)

---

## Étape 8 — Activer le SSL (HTTPS)

Une fois le site accessible en HTTP (`http://ao-copilot.fr`) :

```bash
# 1. Dans nginx/conf.d/ao-copilot.conf, activer le bloc HTTPS :
nano nginx/conf.d/ao-copilot.conf
# → Décommenter le bloc "server { listen 443 ssl ... }" en bas du fichier

# 2. Obtenir le certificat Let's Encrypt
docker compose -f docker-compose.production.yml --env-file .env.production \
  run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d ao-copilot.fr -d www.ao-copilot.fr \
  --email contact@ao-copilot.fr --agree-tos --no-eff-email

# 3. Redémarrer Nginx
docker compose -f docker-compose.production.yml --env-file .env.production \
  restart nginx
```

---

## Étape 9 — Configurer le webhook Stripe

Dans le Dashboard Stripe → Développeurs → Webhooks :
- URL : `https://ao-copilot.fr/api/v1/billing/webhook`
- Événements : `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`

---

## Mises à jour (déploiements suivants)

```bash
ssh deploy@ao-copilot.fr
cd /opt/ao-copilot
bash scripts/deploy.sh
```

Pour mettre à jour sans reconstruire (`--no-migrate` si pas de migration) :
```bash
bash scripts/deploy.sh --no-migrate
```

---

## Commandes utiles

```bash
# Voir tous les services
docker compose -f docker-compose.production.yml ps

# Logs en temps réel
docker compose -f docker-compose.production.yml logs -f

# Logs d'un service spécifique
docker compose -f docker-compose.production.yml logs api -f --tail=100

# Redémarrer un service
docker compose -f docker-compose.production.yml restart api

# Accéder à la DB
docker compose -f docker-compose.production.yml exec postgres \
  psql -U aocopilot -d aocopilot

# Sauvegarde manuelle de la DB
docker compose -f docker-compose.production.yml exec postgres \
  pg_dump -U aocopilot aocopilot > backup_$(date +%Y%m%d).sql
```

---

## Architecture de production

```
Internet
    │
    ▼
Nginx :80/:443  (SSL + reverse proxy)
    ├── /api/*  → FastAPI :8000
    └── /*      → Next.js :3000

FastAPI  → PostgreSQL :5432
         → Redis :6379
         → S3 Scaleway (fichiers)
         → Anthropic API (IA)

Celery Worker → Redis (queue)
              → PostgreSQL
```

---

## Checklist finale avant mise en production

- [ ] Domaine pointé sur le VPS et DNS propagé
- [ ] `.env.production` rempli avec les vraies clés (Stripe LIVE, pas TEST)
- [ ] SSL activé (https://)
- [ ] Webhook Stripe configuré avec l'URL de production
- [ ] Bucket S3 Scaleway créé et accessible
- [ ] Email Resend configuré (domaine vérifié)
- [ ] Premier compte admin créé manuellement
- [ ] Test d'un vrai paiement Stripe (puis remboursé)
