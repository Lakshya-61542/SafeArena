# Deploy SafeArena Docker mode to a public VPS

This guide exposes the **Docker-mode** SafeArena dashboard to hackathon judges while keeping the Red, Blue, and LLM containers on separate Docker networks. It is separate from the existing Render demo, which is local simulation only.

## What you need

- A Linux VPS running Ubuntu 24.04 LTS (2 GB RAM minimum; 2 vCPU / 4 GB RAM is more comfortable for image builds).
- A public IPv4 address.
- A domain or subdomain whose DNS **A record** points to that IP. A free DuckDNS subdomain can be used if you do not own a domain.
- In the VPS firewall/security group, allow inbound TCP **22** (preferably only from your IP), **80**, and **443**. Do not open ports 8000, 8101, 8102, or 8103 to the Internet.

Caddy obtains and renews HTTPS certificates automatically. The domain must resolve to the VPS and ports 80/443 must be reachable from the public Internet. See the [Caddy HTTPS guide](https://caddyserver.com/docs/quick-starts/https).

## 1. Create the server and point DNS

1. Create an Ubuntu 24.04 VPS with a public IPv4 address.
2. Add an A record for your chosen subdomain pointing to the VPS IP. If using DuckDNS, create the subdomain and set its current IP in the DuckDNS dashboard.
3. Configure the VPS provider firewall to allow SSH, HTTP (80), and HTTPS (443). Keep all SafeArena container ports private. Prefer the provider firewall/security group; Docker-published ports can bypass UFW rules, so do not rely on UFW alone ([Docker firewall notes](https://docs.docker.com/engine/install/ubuntu/)).

## 2. Install Docker Engine and Compose

Follow Docker's official [Ubuntu installation guide](https://docs.docker.com/engine/install/ubuntu/) and install Docker Engine plus the Compose plugin. Verify:

```bash
docker --version
docker compose version
sudo systemctl enable --now docker
```

For the commands below, either prefix Docker commands with `sudo` or complete Docker's official post-install steps for your user.

## 3. Get the repository

```bash
git clone https://github.com/Lakshya-61542/SafeArena.git
cd SafeArena
cp .env.example .env
nano .env
```

Set these two values in `.env` (replace the example domain with the exact DNS name you configured):

```dotenv
SAFEARENA_DOMAIN=safearena.example.com
SAFEARENA_ALLOWED_HOSTS=safearena.example.com
```

Do not include `https://`, a port, a path, or a wildcard in either hostname. Keep `.env` private and never commit it.

## 4. Start the public Docker demo

Run these commands from the repository directory:

```bash
export COMPOSE_FILE=docker-compose.yml:docker-compose.public.yml
docker compose config --quiet
docker compose up -d --build --wait
docker compose ps
```

Caddy serves the public HTTPS URL and proxies to the gateway over the Docker `frontend` network. The gateway is still published to the host's loopback address only; the Red, Blue, and LLM service ports are not published. Red, Blue, and LLM remain on their separate `internal: true` networks.

Check the logs if startup fails:

```bash
docker compose logs --tail=150 gateway caddy red-service blue-service llm-service
```

## 5. Verify actual network isolation

Run the real connectivity test with the same Compose overlay and keep the containers running afterward:

```bash
COMPOSE_FILE=docker-compose.yml:docker-compose.public.yml python3 scripts/docker_isolation_test.py --keep
```

Only report real isolation if the result is **PASS**. If it says **FAIL** or **INCONCLUSIVE**, inspect the logs and fix the issue before presenting it to judges. The script writes `reports/docker_isolation_report.json`.

Then open `https://YOUR_DOMAIN` and check the dashboard's mode badge. The isolation probe should be available. The dashboard will label the deployment as Docker mode and show the probe result when run.

## Public-demo safety settings

- No judge username or password is required; anyone with the URL can access it.
- Public Docker mode forces the mock LLM and rate-limits POST requests.
- Audit rotation, the audit tamper test, and audit export are disabled. The real Docker isolation probe remains enabled so judges can inspect its result.
- Persistent audit/event data lives in the `safearena_data` Docker volume. Back up that volume if you need to preserve evidence.
- Do not add private documents, credentials, or sensitive data to this public demo.
- The demo demonstrates prototype controls, not a production security boundary. Keep the VPS OS, Docker Engine, and images updated.

## Updating after a GitHub change

```bash
git pull
COMPOSE_FILE=docker-compose.yml:docker-compose.public.yml docker compose up -d --build --wait
```

Keep `COMPOSE_FILE` set in your shell for other `docker compose` commands on the public server. The base-only command may omit the Caddy/public settings, so use the overlay consistently.
