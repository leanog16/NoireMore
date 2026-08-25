# Deploying NoireMore on Proxmox + Cloudflare Tunnel

This app is two Docker containers (`backend` Flask/Groq API, `frontend` nginx serving the built React app and proxying `/submit` and `/api/*` to the backend), wired together by [docker-compose.yaml](docker-compose.yaml). Cloudflare Tunnel just needs to point at the frontend container's exposed port — no public inbound ports needed on your router/firewall.

## 1. Prerequisites

On the Proxmox host, create a VM or LXC container to run Docker in (an unprivileged LXC works fine for Docker on recent Proxmox; a small VM is the safer/simpler default if you haven't set up Docker-in-LXC before). Debian or Ubuntu recommended.

Inside that VM/container, install Docker + the Compose plugin:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

Log out/in (or `newgrp docker`) so your user can run `docker` without `sudo`. Confirm:

```bash
docker compose version
```

You'll also need:
- A [Groq API key](https://console.groq.com/keys)
- A Cloudflare account with your domain already added, and `cloudflared` available (installed on this same host, or wherever you run your tunnels)

## 2. Get the code onto the server

This project isn't currently pushed to a git remote. Easiest options:

```bash
# from your Mac, copy the project to the server
rsync -avz --exclude node_modules --exclude .git \
  /Users/gavin/ncsu/NoireMore-main/ user@proxmox-host:/opt/noiremore/
```

Or push it to a private GitHub repo first and `git clone` it on the server — preferable long-term since it makes updates a `git pull` away.

## 3. Configure environment

On the server, in the project root:

```bash
cd /opt/noiremore
cp .env.example .env
nano .env
```

Fill in:

```
GROQ_API_KEY=your-real-groq-key
GROQ_MODEL=openai/gpt-oss-120b
```

`.env` is gitignored — it never gets committed, and `docker-compose.yaml` reads it automatically via `${GROQ_API_KEY}`.

## 4. Build and start the stack

```bash
docker compose up -d --build
```

Verify both containers are healthy:

```bash
docker compose ps
curl -s http://localhost:5050/api/health   # backend directly
curl -s http://localhost:8080/             # frontend (nginx)
curl -s -X POST http://localhost:8080/submit \
  -H "Content-Type: application/json" \
  -d '{"message": "the sky is blue"}'
```

`docker compose ps` should show `noiremore-backend` as `(healthy)`. If it's not, check `docker compose logs backend` — the most common cause is a missing/invalid `GROQ_API_KEY`.

## 5. Expose it with a Cloudflare Tunnel

The frontend container publishes port `8080` on the host (`localhost:8080`), which is all the tunnel needs to reach — nginx inside that container already proxies `/submit` and `/api/*` to the backend over the internal Docker network, so the backend's port `5050` never needs to be exposed publicly.

### Install cloudflared (if not already)

```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb
```

### Create and configure the tunnel

```bash
cloudflared tunnel login
cloudflared tunnel create noiremore
```

This prints a tunnel ID and writes credentials to `~/.cloudflared/<TUNNEL_ID>.json`. Create `~/.cloudflared/config.yml`:

```yaml
tunnel: noiremore
credentials-file: /home/youruser/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: factcheck.yourdomain.com
    service: http://localhost:8080
  - service: http_status:404
```

Route DNS and run it:

```bash
cloudflared tunnel route dns noiremore factcheck.yourdomain.com
cloudflared tunnel run noiremore
```

### Make it persistent

```bash
sudo cloudflared service install
sudo systemctl enable --now cloudflared
```

Your site is now live at `https://factcheck.yourdomain.com` with no inbound ports opened on the network.

## 6. Updating after a code change

```bash
cd /opt/noiremore
git pull            # or re-rsync from your Mac
docker compose up -d --build
```

Compose only rebuilds/recreates the containers whose image actually changed, so this is safe to run any time.

## 7. Troubleshooting

| Symptom | Check |
|---|---|
| Backend unhealthy | `docker compose logs backend` — usually a missing/bad `GROQ_API_KEY` |
| `/submit` returns 500 | `docker compose logs backend` for the traceback |
| Site unreachable via domain | `cloudflared tunnel info noiremore`, `systemctl status cloudflared` |
| Works on `localhost:8080` but not via tunnel | Confirm the `ingress.hostname` in `config.yml` matches your DNS route exactly |
| Stale frontend after rebuild | `docker compose up -d --build frontend` (nginx serves a static build, so a rebuild is required to pick up changes) |

Useful commands:

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose restart backend
docker compose down          # stop everything (data isn't persisted anywhere, so this is safe)
```
