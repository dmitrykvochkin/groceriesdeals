# Deploy the MCP server to AWS Lightsail

This guide deploys the database-free Groceries Deals MCP server as an immutable
container on an Ubuntu Lightsail instance. Docker Compose runs the MCP server
and Caddy, while usage events are delivered to PostHog.

```text
Internet -> Caddy :443 -> MCP :8438 -> PostHog HTTPS API
```

Only Caddy publishes host ports. The MCP service is reachable only on the
private Compose network.

> [!NOTE]
> v1 is intentionally open: the deals tools do not authenticate callers.
> HTTPS via Caddy protects transport. `openai/subject` is optional client
> metadata used only for PostHog analytics when present. Add rate limits or
> auth later if abuse becomes a problem.

## What the repository provides

- `Dockerfile`: a non-root production image with the locked Python environment.
- `compose.production.yaml`: MCP and Caddy services.
- `Caddyfile`: automatic HTTPS and reverse proxy configuration.
- `.github/workflows/publish-container.yaml`: tests and publishes commit-SHA and
  `latest` images to GHCR.
- `scripts/deploy-production.sh`: pulls an exact image and replaces the MCP
  container.

The workflow publishes `linux/amd64` images. Select an x86-64 Lightsail
instance, or add an arm64 platform before choosing AWS Graviton.

## 1. Create PostHog configuration

Create or select a PostHog project and record its project token and ingestion
host. The server requires both values at startup. The token is intended for
event ingestion, but the environment file should still be protected.

The server sends sanitized events, including bounded and redacted tool
arguments. Delivery failures after startup are logged and do not interrupt MCP
requests.

## 2. Publish the first image

Push the repository to GitHub's `main` branch. The **Test and publish
container** workflow runs unit tests, builds the production image with
provenance and an SBOM, then publishes:

- `ghcr.io/dmitrykvochkin/groceriesdeals:<full-git-commit-sha>`
- `ghcr.io/dmitrykvochkin/groceriesdeals:latest`

Use the immutable commit-SHA tag for deployments and rollbacks. If the GHCR
package is private, create a token with `read:packages` for the host.

## 3. Create the Lightsail instance and DNS

Create an **OS only > Ubuntu 24.04 LTS** x86-64 instance with at least 2 GB RAM.
Attach a static IPv4 address. In both IPv4 and IPv6 firewalls allow TCP 22 only
from administrator addresses, TCP 80 and 443 publicly, and optionally UDP 443
for HTTP/3. Do not open port 8438.

Point an `A` record such as `mcp.example.com` at the static IPv4 address. Add an
`AAAA` record if IPv6 is enabled. Caddy obtains a certificate after DNS resolves
and ports 80 and 443 are reachable.

## 4. Install Docker

Install Docker Engine and the Compose plugin by following Docker's
[Ubuntu installation guide](https://docs.docker.com/engine/install/ubuntu/).
Allow the deployment user to run Docker, understanding that membership in the
`docker` group is effectively root access.

## 5. Install deployment configuration

GitHub SSH always requires a key, including for a public repository. On the
instance, as the `ubuntu` user, create a read-only deploy key and trust
GitHub's published Ed25519 host key
(`SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU`):

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
ssh-keygen -t ed25519 -C "lightsail-groceriesdeals" -f ~/.ssh/id_ed25519 -N ""
printf '%s\n' \
  'github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl' \
  >> ~/.ssh/known_hosts
cat ~/.ssh/id_ed25519.pub
```

In the GitHub repository, open **Settings > Deploy keys**, add that public key,
and leave **Allow write access** unchecked. Confirm the key works:

```bash
ssh -T git@github.com
```

GitHub answers with a successful authentication line and a shell exit code of
1. That is expected, because the account has no interactive shell.

Clone the deployment files:

```bash
sudo mkdir -p /opt/groceriesdeals
sudo chown ubuntu:ubuntu /opt/groceriesdeals
git clone git@github.com:dmitrykvochkin/groceriesdeals.git \
  /opt/groceriesdeals
```

Create the protected environment file:

```bash
sudo mkdir -p /etc/groceriesdeals
sudo cp /opt/groceriesdeals/deploy/production.env.example \
  /etc/groceriesdeals/groceriesdeals.env
sudo editor /etc/groceriesdeals/groceriesdeals.env
```

Set these values:

```dotenv
MCP_DOMAIN=mcp.example.com
GROCERIES_IMAGE=ghcr.io/dmitrykvochkin/groceriesdeals
IMAGE_TAG=latest
ANONYMOUS_KEY_SECRET=PASTE_A_RANDOM_SECRET
POSTHOG_PROJECT_TOKEN=phc_YOUR_PROJECT_TOKEN
POSTHOG_HOST=https://eu.i.posthog.com
```

Generate the identity secret with `openssl rand -hex 32`, and keep it stable so
the same OpenAI subject continues to derive the same distinct ID.

```bash
sudo chown root:docker /etc/groceriesdeals/groceriesdeals.env
sudo chmod 640 /etc/groceriesdeals/groceriesdeals.env
```

If GHCR is private, authenticate interactively using a token with
`read:packages`.

## 6. Deploy and verify

Deploy the full commit SHA from a successful workflow run:

```bash
cd /opt/groceriesdeals
./scripts/deploy-production.sh 526c670d30cb540d1e8097f971f65e31650f501e
```

The script validates Compose, pulls the exact application image and pinned
Caddy image, replaces the services, waits for the MCP health check, and prints
status.

```bash
docker compose \
  --env-file /etc/groceriesdeals/groceriesdeals.env \
  -f /opt/groceriesdeals/compose.production.yaml ps

docker compose \
  --env-file /etc/groceriesdeals/groceriesdeals.env \
  -f /opt/groceriesdeals/compose.production.yaml logs --tail=100 mcp caddy

dig +short mcp.kortingzoeker.com

curl -I https://mcp.kortingzoeker.com/mcp
```

An HTTP method or MCP protocol error from `curl` only confirms basic network
reachability, not a working MCP deployment. From your local repository checkout
(with `uv` installed), run the end-to-end smoke check:

```bash
uv run scripts/check-live-deployment.py https://mcp.kortingzoeker.com/mcp
```

The script verifies TLS for HTTPS URLs, initializes MCP, discovers the `greet`
tool, and checks its response. It exits with status 0 on success or nonzero on
failure, with a 30-second overall timeout (override with `--timeout 60`). Use
your own domain if different. No production environment file is needed locally.

This makes a real tool call using the subject `v1/deployment-smoke-check`, so it
can generate analytics events. Confirm delivery separately in PostHog: a passing
check does not verify analytics ingestion or which image revision is running.

## Updates and rollback

To compare the running image's commit with the current remote `main`, run **on
the Lightsail instance**:

```bash
cd /opt/groceriesdeals
./scripts/check-deployed-revision.sh
```

This read-only check needs Git access to `origin` and Docker access, but does not
need the production environment file. It finds the running MCP container using
Compose labels and reads its embedded revision, rather than trusting a mutable
image tag. Exit codes: `0` = match, `1` = mismatch, `2` = unable to check. If you
overrode the Compose project name, set `COMPOSE_PROJECT_NAME` to that name.
It checks the commit at the time of the query, not application health; use the
live smoke check above for that.

For a release, wait for the workflow, update the deployment checkout when its
files changed, and run the deployment script with the new full commit SHA. To
roll back, run it with the previous known-good SHA. No schema migration or data
rollback is involved.

Monitor container health, MCP/Caddy logs, PostHog delivery warnings, instance
resources, HTTPS uptime, and operating-system updates. Caddy certificate state
is stored in named volumes and survives container replacement.
