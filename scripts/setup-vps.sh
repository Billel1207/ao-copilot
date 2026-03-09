#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# AO Copilot — Setup VPS Hostinger (Ubuntu 22.04)
# À exécuter UNE SEULE FOIS en root sur le VPS après l'achat
# Usage : bash setup-vps.sh
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[WARN] $1${NC}"; }
err()  { echo -e "${RED}[ERREUR] $1${NC}"; exit 1; }

[[ $EUID -ne 0 ]] && err "Ce script doit être exécuté en root (sudo bash setup-vps.sh)"

log "=== AO Copilot — Configuration VPS ==="

# ─── 1. Mise à jour système ───────────────────────────────────────────────────
log "1/7 — Mise à jour du système..."
apt-get update -qq && apt-get upgrade -y -qq

# ─── 2. Paquets essentiels ───────────────────────────────────────────────────
log "2/7 — Installation des paquets essentiels..."
apt-get install -y -qq \
  curl wget git unzip htop ufw fail2ban \
  ca-certificates gnupg lsb-release

# ─── 3. Docker ───────────────────────────────────────────────────────────────
log "3/7 — Installation de Docker..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin

systemctl enable docker
systemctl start docker
log "Docker $(docker --version | cut -d' ' -f3) installé"

# ─── 4. Utilisateur deploy ────────────────────────────────────────────────────
log "4/7 — Création de l'utilisateur 'deploy'..."
if ! id "deploy" &>/dev/null; then
  useradd -m -s /bin/bash deploy
  usermod -aG docker deploy
  log "Utilisateur 'deploy' créé et ajouté au groupe docker"
else
  warn "Utilisateur 'deploy' existe déjà"
  usermod -aG docker deploy
fi

# Clé SSH pour deploy (même que root)
mkdir -p /home/deploy/.ssh
if [[ -f /root/.ssh/authorized_keys ]]; then
  cp /root/.ssh/authorized_keys /home/deploy/.ssh/
  chown -R deploy:deploy /home/deploy/.ssh
  chmod 700 /home/deploy/.ssh
  chmod 600 /home/deploy/.ssh/authorized_keys
fi

# ─── 5. Dossier application ───────────────────────────────────────────────────
log "5/7 — Préparation du dossier application..."
APP_DIR="/opt/ao-copilot"
mkdir -p "$APP_DIR"
chown deploy:deploy "$APP_DIR"

# ─── 6. Firewall UFW ──────────────────────────────────────────────────────────
log "6/7 — Configuration du firewall UFW..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh        # 22
ufw allow http       # 80
ufw allow https      # 443
ufw --force enable
log "Firewall activé : SSH + HTTP + HTTPS"

# ─── 7. Fail2Ban ──────────────────────────────────────────────────────────────
log "7/7 — Configuration de Fail2Ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port    = ssh
logpath = %(sshd_log)s
backend = %(sshd_backend)s
EOF
systemctl enable fail2ban
systemctl restart fail2ban

# ─── Résumé ───────────────────────────────────────────────────────────────────
echo ""
log "══════════════════════════════════════════════"
log " VPS configuré avec succès !"
log "══════════════════════════════════════════════"
echo ""
echo "  Prochaines étapes :"
echo "  1. Connecte-toi en tant que 'deploy' : ssh deploy@$(hostname -I | awk '{print $1}')"
echo "  2. Clone le repo : git clone <URL> /opt/ao-copilot"
echo "  3. Copie .env.production dans /opt/ao-copilot/"
echo "  4. Lance le déploiement : bash scripts/deploy.sh"
echo ""
