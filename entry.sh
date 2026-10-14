#!/bin/bash

NGROK_TOKEN="3KfNFMyCkVcCqHB7lqXNeRfXmoh_5ifxc29fdeTsFe69XkjEP"
SSH_PASSWORD="1987"

echo "root:${SSH_PASSWORD}" | chpasswd

mkdir -p /data/ssh
[ -f /data/ssh/ssh_host_ed25519_key ] || ssh-keygen -t ed25519 -f /data/ssh/ssh_host_ed25519_key -N "" >/dev/null 2>&1
[ -f /data/ssh/ssh_host_rsa_key ] || ssh-keygen -t rsa -b 4096 -f /data/ssh/ssh_host_rsa_key -N "" >/dev/null 2>&1
cp /data/ssh/ssh_host_* /etc/ssh/ 2>/dev/null || true

mkdir -p /var/run/sshd
/usr/sbin/sshd -D -e &
echo "[entry] sshd up"

ngrok config add-authtoken "$NGROK_TOKEN" >/dev/null 2>&1 || true
ngrok tcp 22 --log=stdout --log-format=json &
echo "[entry] ngrok up"
sleep 6

ENDPOINT=$(curl -s http://127.0.0.1:4040/api/tunnels | grep -o 'tcp://[^"]*' | head -1 | sed 's|tcp://||')
if [ -n "$ENDPOINT" ]; then
    HOST="${ENDPOINT%%:*}"
    PORT="${ENDPOINT##*:}"
    echo ""
    echo "=========================================="
    echo "  SSH:  ssh -p ${PORT} root@${HOST}"
    echo "=========================================="
    echo ""
fi

exec ttyd \
    --port "${PORT:-8080}" \
    --interface 0.0.0.0 \
    --writable \
    --max-clients 100 \
    --client-option fontSize=14 \
    python3 /app/officialv3.py
