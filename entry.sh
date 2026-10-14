#!/bin/bash

NGROK_TOKEN="${NGROK_AUTHTOKEN}"
SSH_PASSWORD="${SSH_ROOT_PASSWORD:-1987}"

echo "root:${SSH_PASSWORD}" | chpasswd

echo "/bin/bash" > /etc/shells
echo "/bin/sh" >> /etc/shells
echo "/usr/bin/bash" >> /etc/shells
echo "/usr/bin/sh" >> /etc/shells
echo "/bin/dash" >> /etc/shells
usermod -s /bin/bash root >/dev/null 2>&1 || true

mkdir -p /data/ssh
[ -f /data/ssh/ssh_host_ed25519_key ] || ssh-keygen -t ed25519 -f /data/ssh/ssh_host_ed25519_key -N "" >/dev/null 2>&1
[ -f /data/ssh/ssh_host_rsa_key ] || ssh-keygen -t rsa -b 4096 -f /data/ssh/ssh_host_rsa_key -N "" >/dev/null 2>&1
cp /data/ssh/ssh_host_* /etc/ssh/ 2>/dev/null || true

mkdir -p /var/run/sshd /run/sshd
rm -f /etc/nologin 2>/dev/null || true

/usr/sbin/sshd -D -e &
echo "[entry] sshd up"

if [ -n "$NGROK_TOKEN" ]; then
    ngrok config add-authtoken "$NGROK_TOKEN" >/dev/null 2>&1 || true
    ngrok tcp 22 --log=stdout --log-format=json &
    echo "[entry] ngrok up"
    sleep 6
    ENDPOINT=$(curl -s http://127.0.0.1:4040/api/tunnels | grep -o 'tcp://[^"]*' | head -1 | sed 's|tcp://||')
    if [ -n "$ENDPOINT" ]; then
        NHOST="${ENDPOINT%%:*}"
        NPORT="${ENDPOINT##*:}"
        echo ""
        echo "=========================================="
        echo "  SSH:  ssh -p ${NPORT} root@${NHOST}"
        echo "=========================================="
        echo ""
    fi
fi

exec ttyd \
    --port "${PORT:-8080}" \
    --interface 0.0.0.0 \
    --writable \
    --max-clients 100 \
    --client-option fontSize=14 \
    python3 /app/officialv3.py
