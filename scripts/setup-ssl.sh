#!/bin/bash
# ══════════════════════════════════════════════════════════════════
# AO Copilot — Setup SSL automatique (Let's Encrypt)
# Usage : bash scripts/setup-ssl.sh [domaine] [email]
# Ex    : bash scripts/setup-ssl.sh ao-copilot.fr contact@ao-copilot.fr
# ══════════════════════════════════════════════════════════════════
set -euo pipefail

DOMAIN="${1:-ao-copilot.fr}"
EMAIL="${2:-contact@${DOMAIN}}"
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"

echo "══════════════════════════════════════════════════"
echo "  AO Copilot — Configuration SSL"
echo "  Domaine : ${DOMAIN}"
echo "  Email   : ${EMAIL}"
echo "══════════════════════════════════════════════════"

# 1. Vérifier que le domaine pointe bien vers ce serveur
echo ""
echo "→ Vérification DNS..."
RESOLVED_IP=$(dig +short "${DOMAIN}" A 2>/dev/null | head -1 || echo "")
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "unknown")

if [ -z "${RESOLVED_IP}" ]; then
    echo "⚠  DNS : ${DOMAIN} ne résout pas encore. Vérifiez vos enregistrements DNS."
    echo "   IP du serveur : ${SERVER_IP}"
    read -p "Continuer quand même ? (y/N) " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]] || exit 1
elif [ "${RESOLVED_IP}" != "${SERVER_IP}" ]; then
    echo "⚠  DNS : ${DOMAIN} pointe vers ${RESOLVED_IP} mais ce serveur est ${SERVER_IP}"
    read -p "Continuer quand même ? (y/N) " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]] || exit 1
else
    echo "✓  DNS OK : ${DOMAIN} → ${RESOLVED_IP}"
fi

# 2. Mettre à jour la config nginx avec le bon domaine
echo ""
echo "→ Configuration nginx pour ${DOMAIN}..."
sed -i "s/ao-copilot\.fr/${DOMAIN}/g" nginx/conf.d/ao-copilot.conf
echo "✓  nginx configuré"

# 3. S'assurer que nginx tourne (en HTTP pour le challenge ACME)
echo ""
echo "→ Démarrage nginx (HTTP)..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d nginx
sleep 3

# 4. Obtenir le certificat Let's Encrypt
echo ""
echo "→ Obtention du certificat SSL via Let's Encrypt..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" \
    run --rm certbot certonly \
    --webroot -w /var/www/certbot \
    -d "${DOMAIN}" -d "www.${DOMAIN}" \
    --email "${EMAIL}" \
    --agree-tos --no-eff-email \
    --force-renewal

# 5. Redémarrer nginx avec HTTPS
echo ""
echo "→ Redémarrage nginx avec HTTPS..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" restart nginx
sleep 2

# 6. Vérifier
echo ""
echo "→ Vérification HTTPS..."
HTTP_CODE=$(curl -sSo /dev/null -w "%{http_code}" "https://${DOMAIN}/api/v1/health" 2>/dev/null || echo "000")

if [ "${HTTP_CODE}" = "200" ]; then
    echo "✓  HTTPS opérationnel ! https://${DOMAIN}"
else
    echo "⚠  Code HTTP ${HTTP_CODE} — vérifiez les logs : docker compose -f ${COMPOSE_FILE} logs nginx"
fi

# 7. Rappel renouvellement automatique
echo ""
echo "══════════════════════════════════════════════════"
echo "  SSL configuré avec succès !"
echo ""
echo "  Renouvellement automatique (ajouter au crontab) :"
echo "  0 3 * * 1 cd /opt/ao-copilot && docker compose -f ${COMPOSE_FILE} --env-file ${ENV_FILE} run --rm certbot renew && docker compose -f ${COMPOSE_FILE} --env-file ${ENV_FILE} restart nginx"
echo "══════════════════════════════════════════════════"
