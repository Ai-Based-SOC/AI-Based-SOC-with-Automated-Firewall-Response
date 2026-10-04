#!/usr/bin/env bash
set -euo pipefail

# ====== REQUIRED (edit these for your environment) ======
DOMAIN="api.naga.ac"
APP_USER="www-data"
APP_DIR="/var/www/ai-soc"
APP_EXEC="/var/www/ai-soc/.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --workers 4"
APP_PORT=8000
SERVICE_NAME="ai-soc"
NGINX_CONF_PATH="/etc/nginx/sites-available/${DOMAIN}.conf"
# ====== END required edits ======

echo "Starting automated 502 remediation & hardening for ${DOMAIN}"
echo "Make sure DNS for ${DOMAIN} points to this server (or temporarily disable Cloudflare proxy)."
read -p "Continue? (y/N) " confirm && [[ "$confirm" =~ ^[Yy]$ ]] || { echo "Cancelled"; exit 1; }

# 1) Quick diagnostics
echo; echo "=== Diagnostics: DNS + connectivity + current HTTP response ==="
echo "Resolved IPs:"
dig +short "${DOMAIN}" || true

echo; echo "curl -v ${DOMAIN} (via Cloudflare):"
curl -I --max-time 20 "https://${DOMAIN}" || true

echo; echo "Listening services (first 200 lines):"
sudo ss -tulpn | sed -n '1,200p' || true
# 2) Create systemd service
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
if [ ! -f "${SERVICE_FILE}" ]; then
  echo; echo "=== Creating systemd service at ${SERVICE_FILE} ==="
  sudo tee "${SERVICE_FILE}" > /dev/null <<'SVC_EOF'
[Unit]
Description=ai-soc - AI SOC Platform
After=network.target mongod.service
Wants=mongod.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/ai-soc
ExecStart=/var/www/ai-soc/.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5
Environment=ENV=production
Environment=PYTHONPATH=/var/www/ai-soc
LimitNOFILE=65536
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/www/ai-soc /var/log/ai-soc
CapabilityBoundingSet=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
SVC_EOF
  sudo systemctl daemon-reload
  sudo systemctl enable --now "${SERVICE_NAME}.service"
  echo "Started and enabled ${SERVICE_NAME}.service"
else
# 3) Ensure nginx installed and write reverse-proxy config
if ! command -v nginx >/dev/null 2>&1; then
  echo; echo "nginx not found, installing nginx..."
  sudo apt-get update
  sudo apt-get install -y nginx
fi

echo; echo "Writing nginx reverse-proxy config to ${NGINX_CONF_PATH} (backing up existing file if present)"
if [ -f "${NGINX_CONF_PATH}" ]; then
  sudo cp "${NGINX_CONF_PATH}" "${NGINX_CONF_PATH}.bak.$(date +%s)"
fi

sudo tee "${NGINX_CONF_PATH}" > /dev/null <<'NGINX_EOF'
upstream ai-soc_upstream {
    server 127.0.0.1:8000 fail_timeout=5s;
    keepalive 32;
}

server {
    listen 80;
    listen 443 ssl http2;
    server_name api.naga.ac;

    ssl_certificate /etc/letsencrypt/live/api.naga.ac/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.naga.ac/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://ai-soc_upstream;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
        proxy_buffer_size 8k;
        proxy_buffers 4 32k;
        proxy_busy_buffers_size 64k;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_cache off;
        proxy_buffering off;
    }

    location /api/v1/health {
        proxy_pass http://ai-soc_upstream;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        access_log off;
    }

    location /api/v1/metrics {
        proxy_pass http://ai-soc_upstream;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    access_log /var/log/nginx/api.naga.ac.access.log;
    error_log /var/log/nginx/api.naga.ac.error.log;
}
NGINX_EOF

sudo ln -sf "${NGINX_CONF_PATH}" /etc/nginx/sites-enabled/"${DOMAIN}.conf"
echo; echo "Testing nginx config..."
sudo nginx -t
echo "Reloading nginx..."
sudo systemctl reload nginx || sudo systemctl restart nginx
  echo "Systemd service ${SERVICE_FILE} already exists -- will restart it."
  sudo systemctl restart "${SERVICE_NAME}.service" || true
fi