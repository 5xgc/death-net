#!/bin/bash
set -e

# ---------- root password ----------
if [ -n "$SSH_ROOT_PASSWORD" ]; then
    echo "root:${SSH_ROOT_PASSWORD}" | chpasswd
else
    echo "root:changeme" | chpasswd
    echo "[entry] WARNING: SSH_ROOT_PASSWORD not set — using 'changeme'"
fi

# ---------- persistent ssh host keys ----------
mkdir -p /data/ssh
if [ ! -f /data/ssh/ssh_host_ed25519_key ]; then
    ssh-keygen -t ed25519 -f /data/ssh/ssh_host_ed25519_key -N "" >/dev/null 2>&1
fi
if [ ! -f /data/ssh/ssh_host_rsa_key ]; then
    ssh-keygen -t rsa -b 4096 -f /data/ssh/ssh_host_rsa_key -N "" >/dev/null 2>&1
fi
cp /data/ssh/ssh_host_* /etc/ssh/ 2>/dev/null || true

# ---------- start sshd ----------
mkdir -p /var/run/sshd
/usr/sbin/sshd -D -e &
echo "[entry] sshd started on port 22"

# ---------- ngrok tunnel on 22 ----------
if [ -n "$NGROK_AUTHTOKEN" ]; then
    ngrok config add-authtoken "$NGROK_AUTHTOKEN" >/dev/null 2>&1 || true
    ngrok tcp 22 --log=stdout --log-format=json &
    echo "[entry] ngrok agent started"
    sleep 5
    ENDPOINT=$(curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null \
        | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tunnels'][0]['public_url'])" 2>/dev/null || true)
    if [ -n "$ENDPOINT" ]; then
        CLEAN="${ENDPOINT#tcp://}"
        echo ""
        echo "================================================================"
        echo "  SSH ENDPOINT  ->  ${CLEAN}"
        echo "  connect with  ->  ssh -p ${CLEAN##*:} root@${CLEAN%:*}"
        echo "================================================================"
        echo ""
    else
        echo "[entry] ngrok started but endpoint lookup failed — check logs"
    fi
else
    echo "[entry] NGROK_AUTHTOKEN not set — skipping ngrok, web terminal only"
fi

# ---------- web terminal on $PORT ----------
exec ttyd \
    --port "${PORT:-8080}" \
    --interface 0.0.0.0 \
    --writable \
    --max-clients 100 \
    --check-origin \
    --client-option fontSize=14 \
    --client-option fontFamily="JetBrains Mono,Menlo,Consolas,monospace" \
    --client-option theme='{"background":"#08060c","foreground":"#dcd0ff","cursor":"#a83cff"}' \
    python3 /app/officialv3.py