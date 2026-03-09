#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# AO Copilot — Script de déploiement (à lancer sur le VPS)
# Usage : bash scripts/deploy.sh [--no-migrate] [--build-only]
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓ $1${NC}"; }
info() { echo -e "${BLUE}[$(date '+%H:%M:%S')] → $1${NC}"; }
warn() { echo -e "${YELLOW}[WARN] $1${NC}"; }
err()  { echo -e "${RED}[ERREUR] $1${NC}"; exit 1; }

APP_DIR="/opt/ao-copilot"
ENV_FILE="$APP_DIR/.env.production"
COMPOSE="docker compose -f $APP_DIR/docker-compose.production.yml --env-file $ENV_FILE"

NO_MIGRATE=false
BUILD_ONLY=false
for arg in "$@"; do
  [[ "$arg" == "--no-migrate" ]] && NO_MIGRATE=true
  [[ "$arg" == "--build-only" ]] && BUILD_ONLY=true
done

# ─── Vérifications préalables ─────────────────────────────────────────────────
[[ ! -d "$APP_DIR" ]] && err "Dossier $APP_DIR introuvable. Clone le repo d'abord."
[[ ! -f "$ENV_FILE" ]] && err "Fichier $ENV_FILE manquant. Copie .env.production.example et remplis-le."
[[ ! -f "$APP_DIR/docker-compose.production.yml" ]] && err "docker-compose.production.yml manquant dans $APP_DIR"

cd "$APP_DIR"

echo ""
info "══════════════════════════════════════════════"
info " AO Copilot — Déploiement"
info " $(date '+%d/%m/%Y %H:%M:%S')"
info "══════════════════════════════════════════════"
echo ""

# ─── 1. Pull du code ──────────────────────────────────────────────────────────
info "1/6 — Récupération du code (git pull)..."
git fetch --all
git reset --hard origin/main
log "Code mis à jour : $(git log --oneline -1)"

[[ "$BUILD_ONLY" == "true" ]] && { info "Mode --build-only : skip pull effectué"; }

# ─── 2. Charger les variables d'env pour le build frontend ───────────────────
info "2/6 — Chargement des variables d'environnement..."
set -a
source "$ENV_FILE"
set +a

NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-https://${DOMAIN}/api/v1}"
log "API URL frontend : $NEXT_PUBLIC_API_URL"

# ─── 3. Build des images Docker ───────────────────────────────────────────────
info "3/6 — Build des images Docker (peut prendre 5-10 min)..."
$COMPOSE build \
  --build-arg NEXT_PUBLIC_API_URL="$NEXT_PUBLIC_API_URL" \
  --no-cache \
  api worker frontend

log "Images Docker construites"

# ─── 4. Démarrage des services infrastructure ─────────────────────────────────
info "4/6 — Démarrage PostgreSQL + Redis..."
$COMPOSE up -d postgres redis

info "Attente que PostgreSQL soit prêt..."
for i in $(seq 1 30); do
  if $COMPOSE exec -T postgres pg_isready -U "${POSTGRES_USER:-aocopilot}" -d "${POSTGRES_DB:-aocopilot}" &>/dev/null; then
    log "PostgreSQL prêt"
    break
  fi
  sleep 2
  [[ $i -eq 30 ]] && err "PostgreSQL n'a pas démarré après 60s"
done

# ─── 5. Migrations Alembic ────────────────────────────────────────────────────
if [[ "$NO_MIGRATE" == "false" ]]; then
  info "5/6 — Exécution des migrations Alembic..."
  $COMPOSE run --rm api alembic upgrade head
  log "Migrations appliquées"
else
  warn "5/6 — Migrations ignorées (--no-migrate)"
fi

# ─── 6. Déploiement complet ───────────────────────────────────────────────────
info "6/6 — Déploiement de tous les services..."
$COMPOSE up -d --remove-orphans

# Attendre que l'API réponde
info "Vérification santé de l'API..."
API_URL="http://localhost:8000/api/v1/health"
for i in $(seq 1 30); do
  if curl -sf "$API_URL" &>/dev/null; then
    log "API opérationnelle"
    break
  fi
  sleep 3
  [[ $i -eq 30 ]] && warn "API pas encore prête (vérifier les logs : docker compose logs api)"
done

# ─── Résumé ───────────────────────────────────────────────────────────────────
echo ""
log "══════════════════════════════════════════════"
log " Déploiement terminé avec succès !"
log "══════════════════════════════════════════════"
echo ""
echo "  Services actifs :"
$COMPOSE ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || $COMPOSE ps
echo ""
echo "  Logs en temps réel : docker compose -f docker-compose.production.yml logs -f"
echo "  Logs API           : docker compose -f docker-compose.production.yml logs api -f"
echo ""
DOMAIN_VAL="${DOMAIN:-votre-domaine.com}"
echo "  Site disponible sur : https://$DOMAIN_VAL"
echo ""
