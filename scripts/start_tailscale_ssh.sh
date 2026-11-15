#!/usr/bin/env bash
# ==============================================================================
# Ultra-lightweight Tailscale SSH Starter for Google Colab
# Usage:
#   bash start_tailscale_ssh.sh [AUTH_KEY] [HOSTNAME]
# ==============================================================================

set -eo pipefail

AUTH_KEY="${1:-${TAILSCALE_AUTHKEY:-}}"
HOSTNAME="${2:-${TAILSCALE_HOSTNAME:-dervgen-colab-gpu}}"

echo "🚀 [Tailscale] Initializing network devices..."
mkdir -p /dev/net /var/run/tailscale /var/lib/tailscale
[ ! -c /dev/net/tun ] && mknod /dev/net/tun c 10 200 2>/dev/null && chmod 600 /dev/net/tun 2>/dev/null || true

# 安装 Tailscale
if ! command -v tailscale >/dev/null; then
    echo "📦 [Tailscale] Installing Tailscale package..."
    curl -fsSL https://tailscale.com/install.sh | sh
fi

# 启动后台守护进程
if ! pgrep -x tailscaled >/dev/null; then
    echo "⚙️ [Tailscale] Starting tailscaled daemon..."
    tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/var/run/tailscale/tailscaled.sock >/tmp/tailscaled.log 2>&1 &
    sleep 2
    # 容错降级至 userspace-networking
    if ! pgrep -x tailscaled >/dev/null; then
        echo "⚠️ [Tailscale] Falling back to userspace-networking..."
        tailscaled --tun=userspace-networking --socks5-server=localhost:1055 \
                   --state=/var/lib/tailscale/tailscaled.state \
                   --socket=/var/run/tailscale/tailscaled.sock >/tmp/tailscaled.log 2>&1 &
        sleep 2
    fi
fi

# 等待 Socket
for i in {1..10}; do
    [ -S /var/run/tailscale/tailscaled.sock ] && break
    sleep 1
done

# 启动入网与 SSH
echo "🔗 [Tailscale] Connecting node: ${HOSTNAME} with Tailscale SSH..."
if [ -n "${AUTH_KEY}" ]; then
    tailscale up --ssh --hostname="${HOSTNAME}" --accept-routes --authkey="${AUTH_KEY}"
else
    echo "👉 No Auth Key provided. Click the login URL below to authenticate:"
    tailscale up --ssh --hostname="${HOSTNAME}" --accept-routes
fi

echo "=========================================================="
echo "🎉 Tailscale SSH is ready!"
echo "Node IP: $(tailscale ip -4 2>/dev/null || echo 'unknown')"
echo "To connect from local terminal: ssh root@${HOSTNAME}"
echo "=========================================================="
