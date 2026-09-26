# Deployment Guide

How to get the bot running locally, in Docker, and on Railway, and how to keep it locked down.

---

## Contents

1. [Prerequisites](#1-prerequisites)
2. [Local setup](#2-local-setup)
3. [Windows and Git Bash notes](#3-windows-and-git-bash-notes)
4. [Docker](#4-docker)
5. [Deploy to Railway](#5-deploy-to-railway)
6. [Models and providers](#6-models-and-providers)
7. [Security](#7-security)
8. [Monitoring and maintenance](#8-monitoring-and-maintenance)
9. [Troubleshooting](#9-troubleshooting)
10. [Quick reference](#10-quick-reference)

---

## 1. Prerequisites

### A Telegram bot token

Everything goes through [@BotFather](https://t.me/BotFather) on Telegram.

**New bot:**
1. Send `/newbot` to @BotFather
2. Pick a display name, then a username ending in `bot`
3. BotFather replies with a token. Keep it somewhere safe; it is the bot's password.

**Existing bot:** send `/mybots`, pick the bot, then **API Token**. If the token has ever been exposed (committed to code, pasted somewhere, visible in a log or screenshot), choose **Revoke current token**. The old token stops working immediately and BotFather issues a new one.

**Check the token works** by opening this in a browser, with your token in place of `YOUR_TOKEN`:

```
https://api.telegram.org/botYOUR_TOKEN/getMe
```

A JSON reply with your bot's username means the token is valid.

**Command menu (optional).** Send `/setcommands` to BotFather, pick the bot, and paste:

```
help - Show all commands
chart - Stock chart: /chart MSFT 3d 1m
chartv - Chart with volume
markets - Major index overview
img - Image search: /img query or /imge4 query
web - Web search: /web query
news - News search: /news query
vid - Video search: /vid query
ask - Ask AI: /ask question or /ask:grok question
search - Web-grounded AI search: /search query
models - Show available AI providers and models
usage - Show monthly API usage and limits
gp - Xbox Game Pass news
flip - Flip a coin: /flip or /flip 5
teams - Random team split
```

### API keys

None of these are required. Each one switches a feature on, and the bot turns that feature off cleanly when its key is missing.

| Key | Where to get it | Enables |
|---|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com), Settings, API Keys | `/ask:claude` |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com), API Keys | `/ask:gpt` |
| `GROK_API_KEY` | [console.x.ai](https://console.x.ai), API Keys | `/ask:grok`, including `/ask:grok:web` |
| `PERPLEXITY_API_KEY` | [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api) | `/search` |
| `BRAVE_API_KEY` | [api-dashboard.search.brave.com](https://api-dashboard.search.brave.com/), choose the **Search** plan, not Answers | `/img`, `/web`, `/news`, `/vid` through Brave's API, with full safe search control |
| `FINNHUB_API_KEY` | [finnhub.io/register](https://finnhub.io/register) | Real-time US quotes for `$SYMBOL` |
| `SONGLINK_API_KEY` | [odesli.co](https://odesli.co/), by request | Lifts Songlink rate limits (works without it) |

The LLM providers bill per token, so set a monthly limit per provider before sharing the bot (see [cost controls](#cost-controls)). **Perplexity also charges per search on top of tokens**, which makes it the easiest one to overspend on; start with the basic `sonar` model and a low limit.

### Software

- **Git**: [git-scm.com](https://git-scm.com/downloads)
- **Conda** (Anaconda or Miniconda), or plain Python 3.12 with venv
- **Docker Desktop** (optional, for container runs): [docker.com](https://www.docker.com/products/docker-desktop/)

---

## 2. Local setup

```bash
git clone https://github.com/rglynch/switchboard-bot.git
cd switchboard-bot

# Create and activate the environment (name comes from environment.yml)
conda env create -f environment.yml
conda activate switchboard-bot
```

Plain venv works too: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.

### Configuration

Copy the template and fill in at least `TELEGRAM_BOT_TOKEN`:

```bash
cp .env.example .env
```

`config.py` calls `load_dotenv()` with no path. That searches for a file named `.env` starting in `bot/` and walking up through parent folders, so a `.env` in the repo root is found automatically. It is gitignored.

**Keeping the file outside the repo instead.** If you store your keys elsewhere, `load_dotenv()` will not find them. Export them into your shell before running:

```bash
set -a; source "/path/to/your.env"; set +a
```

`set -a` marks every variable the file defines for export. Two things to know:
- **Re-sourcing never unsets anything.** Commenting a line out of the file and sourcing again leaves the old value in your shell. Use `unset VAR_NAME`, or open a new terminal.
- **Save the file with LF line endings.** With Windows (CRLF) endings every value picks up an invisible `\r`, and Telegram rejects the token as if it were wrong.

### Run it

```bash
python -m bot.main
```

The startup log lists every feature as on (✅) or off (⬜), then a `Bot started` line. Message the bot `/help`. `Ctrl+C` stops it.

---

## 3. Windows and Git Bash notes

Everything above works in Git Bash on Windows once conda is wired in. These are the problems a fresh Windows machine hits, in the order you will meet them.

**`conda: command not found` in Git Bash.** Conda is installed but not hooked into bash. Add its hook to `~/.bashrc` once, using your install location:

```bash
echo '. /c/ProgramData/anaconda3/etc/profile.d/conda.sh' >> ~/.bashrc
```

(For a per-user Miniconda install the path is usually under `~/miniconda3/`.) Open a new terminal afterwards. For PowerShell, run `conda init powershell` once instead (by its full path, such as `C:\ProgramData\anaconda3\Scripts\conda.exe`, if conda is not on PATH).

**`EnvironmentNameNotFound: C:Users...`** Bash treats a backslash as an escape character, so a Windows path loses its backslashes. Activate by name (`conda activate switchboard-bot`), or use forward slashes.

**VS Code types that broken command for you.** The Python extension auto-activates the selected interpreter in new terminals and sends a Windows-style path into Git Bash. Either switch the default terminal to PowerShell, or turn auto-activation off in `.vscode/settings.json` and activate by name:

```json
"python.terminal.activateEnvironment": false,
"python-envs.terminal.autoActivationType": "off"
```

**`FileNotFoundError` from `ssl.create_default_context(cafile=os.environ["SSL_CERT_FILE"])`.** The environment's `openssl` package ships an activation script per shell. The PowerShell and cmd versions point `SSL_CERT_FILE` at the Windows certificate location (`Library\ssl\cacert.pem`); the bash version points at the Linux location (`ssl/cacert.pem`), which does not exist on Windows. Set it once for the environment:

```bash
conda env config vars set SSL_CERT_FILE="C:/Users/<you>/.conda/envs/switchboard-bot/Library/ssl/cacert.pem" -n switchboard-bot
```

Then deactivate and reactivate. Use the path `conda env list` shows for your environment. A one-off `unset SSL_CERT_FILE` also works for the current terminal.

**A newly installed tool is "not found" in VS Code's terminal.** Terminals inherit PATH from the VS Code window. After installing something that edits PATH, restart VS Code completely; a new terminal tab is not enough.

---

## 4. Docker

Docker packages the bot, Python and every dependency into one image that runs the same everywhere. Conda plays no part inside the container; the `Dockerfile` installs from `requirements.txt` with pip.

### Build and run

`docker-compose.yml` passes the variables it lists through from your shell, so export them first:

```bash
set -a; source .env; set +a
docker compose up -d --build     # build the image and start the container
docker compose ps                # is it running?
docker compose logs -f           # follow the logs
docker compose down              # stop it
```

**Only the variables listed under `environment:` in `docker-compose.yml` reach the container.** If you use one that is not listed (a model override, `ALLOWED_MODELS_*`, `MONTHLY_LIMIT_*`, `LLM_DEFAULT`, `SONGLINK_API_KEY`), add it to that list or the container silently runs on the default.

The compose file sets `restart: unless-stopped`, so the container comes back after a crash or a reboot of the Docker host.

### What the Dockerfile does

```dockerfile
FROM python:3.12-slim                  # small official Python base
ENV MPLBACKEND=Agg ...                 # matplotlib renders without a display
WORKDIR /app
RUN apt-get install ... libfreetype6 libpng16-16   # C libraries for chart rendering
COPY requirements.txt .                # copied first so Docker caches the pip layer
RUN pip install --no-cache-dir -r requirements.txt
COPY bot/ bot/
RUN useradd --create-home appuser      # run as a non-root user
USER appuser
CMD ["python", "-m", "bot.main"]
```

---

## 5. Deploy to Railway

An earlier version of this bot runs on Railway. Railway builds from the `Dockerfile` (as set in `railway.toml`) every time you push to the connected branch.

1. Push the repo to GitHub.
2. In [Railway](https://railway.app/dashboard): **New Project**, then **Deploy from GitHub Repo**, and pick the repo. Railway detects the `Dockerfile` and starts building.
3. Open the service's **Variables** tab and add your variables, one at a time or all at once through **RAW Editor** in `KEY=VALUE` form. Railway injects these directly, so the `docker-compose.yml` list does not apply here.
4. Railway redeploys after the variables change. Watch the **Deployments** tab for build logs.
5. Message the bot. If it answers, it is live.

**Updates:** every push to the connected branch triggers a rebuild and redeploy. `railway.toml` sets `restartPolicyType = "on_failure"` with `restartPolicyMaxRetries = 5`, so a crashing bot is restarted automatically, up to 5 times.

**Networking:** a polling bot needs no public URL. In the service **Settings**, leave **Public Networking** off.

---

## 6. Models and providers

### Default provider and model

`LLM_DEFAULT` picks the provider `/ask` uses (`claude`, `gpt`, `grok` or `perplexity`; default `grok`). Each provider's default model comes from its `*_MODEL` variable and can be changed without touching code:

| Provider | Variable | Default |
|---|---|---|
| Claude | `ANTHROPIC_MODEL` | `claude-haiku-4-5` |
| GPT | `OPENAI_MODEL` | `gpt-5.4-mini` |
| Grok | `GROK_MODEL` | `grok-4.1-fast` |
| Perplexity | `PERPLEXITY_MODEL` | `sonar` |

### Per-message models

Users can pick a model per message with a shortcut or a full model string: `/ask:claude:sonnet question` or `/ask:gpt:gpt-5.4 question`. Anything that is not a known shortcut is passed through to the provider as-is, so a newly released model works without a code change.

Shortcuts defined in the provider files:

| Provider | Shortcut → model |
|---|---|
| Claude (`claude.py`) | `haiku` → `claude-haiku-4-5` · `sonnet` → `claude-sonnet-4-6` · `opus` → `claude-opus-4-6` |
| GPT (`openai.py`) | `5.4` → `gpt-5.4` · `mini` / `5.4-mini` → `gpt-5.4-mini` · `nano` / `5.4-nano` → `gpt-5.4-nano` · `4.1` → `gpt-4.1` · `4.1-mini` → `gpt-4.1-mini` |
| Grok (`grok.py`) | `fast` → `grok-4-1-fast` · `fast-noreason` → `grok-4-1-fast-non-reasoning` · `4` → `grok-4` · `3` → `grok-3` |
| Perplexity (`perplexity.py`) | `sonar` → `sonar` · `pro` → `sonar-pro` · `reasoning` → `sonar-reasoning-pro` |

To add a shortcut, add an entry to that provider's `model_aliases` dict.

### Restricting models

`ALLOWED_MODELS_<PROVIDER>` limits which models users may pick, by shortcut or full string. `.env.example` restricts each provider to its cheapest model out of the box:

```
ALLOWED_MODELS_CLAUDE=haiku
ALLOWED_MODELS_GPT=mini
ALLOWED_MODELS_GROK=fast
ALLOWED_MODELS_PERPLEXITY=sonar
```

Open one up with a comma-separated list, for example `ALLOWED_MODELS_CLAUDE=haiku,sonnet`. Unset means every model is allowed.

---

## 7. Security

### Secrets

- Every secret is an environment variable read in `config.py`. None are in code or in Git.
- `.env` is gitignored. On Railway, variables live in the dashboard and are injected at runtime.
- **Telegram puts the bot token in the request URL** (`api.telegram.org/bot<TOKEN>/...`), and `httpx` logs full URLs at INFO. `main.py` raises the `httpx` logger to WARNING so the token never reaches the logs. Keep that line.
- If a token or key is ever exposed, revoke and regenerate it. For Telegram, that is `/revoke` in @BotFather.

### Container

- **Non-root:** the bot runs as `appuser`, so code execution inside the container does not mean root.
- **Slim base image:** `python:3.12-slim` keeps the installed surface small.

### Network

The bot **polls** Telegram (outbound requests only) instead of receiving webhooks. It listens on no port, so there is no inbound attack surface and nothing to expose publicly.

### Group chats

1. Add the bot to the group by its username.
2. By default a bot in a group only sees commands and messages that mention it. For `$SYMBOL` quotes and music-link detection to work, send `/setprivacy` to @BotFather, pick the bot, and choose **Disable**. (Disabling privacy mode is what lets it read every message.)

### Chat allowlist

Lock the bot to specific chats with `ALLOWED_CHAT_IDS` (comma-separated). Messages from any other chat are ignored silently. Leave it unset to allow every chat.

To find a chat ID, use any one of these:
- Send a message in the chat and look in the bot's logs for the chat ID.
- After the bot has received a message, open `https://api.telegram.org/botYOUR_TOKEN/getUpdates` and find `"chat":{"id": ...}`. Group IDs are negative; direct-message IDs are positive.
- Add [@userinfobot](https://t.me/userinfobot) to the group, read the ID, remove it.

### Dependencies

`python-telegram-bot` is pinned to an exact version; the other dependencies set minimum versions (`>=`), so a fresh install gets the newest release. Run `pip audit` now and then.

### What is out of scope

No database (no SQL injection), no web interface (no XSS or CSRF), no open port (nothing to flood), and every API call uses HTTPS. The realistic risks are a leaked key (handled by environment variables and rotation) and hostile user input (the bot never evaluates user input as code).

---

## 8. Monitoring and maintenance

### Logs

- **Local:** the terminal.
- **Docker:** `docker compose logs -f`.
- **Railway:** the service's **Deployments** tab, then the active deployment, then **View Logs**.

### What the logs tell you

- `Bot started`: healthy.
- `Brave: image '<query>' → N results`: search went through Brave's API.
- `Error in engine duckduckgo: ...` from `ddgs`: normal on the keyless fallback. `ddgs` tries its engines in random order and moves on when one fails.
- A chat reply of ``Provider `X` not available``: that provider's key is not set.

### Restarting

Railway: **Deployments**, the three-dot menu, **Restart**, or push an empty commit (`git commit --allow-empty -m "Redeploy"` then `git push`). Docker: `docker compose restart`.

### Cost controls

The bot counts requests per LLM provider and enforces a monthly cap:

```
MONTHLY_LIMIT_CLAUDE=200
MONTHLY_LIMIT_GPT=200
MONTHLY_LIMIT_GROK=500
MONTHLY_LIMIT_PERPLEXITY=100
USAGE_WARN_PCT=80
```

- Every `/ask` and `/search` counts against its provider's limit. A provider with no limit set is unlimited.
- At `USAGE_WARN_PCT` percent, replies include a warning with the count remaining.
- At 100%, the bot refuses further requests to that provider with a joke message until the month resets.
- `/usage` shows each provider's count with a progress bar.
- Search commands (`/img`, `/web`, `/news`, `/vid`) are not counted. Brave's usage shows in its own dashboard.

**Limitation:** the counts are stored in `/tmp/bot_usage.json` inside the container. On Railway, a redeploy or restart starts a fresh container, so the counts reset then too, not only at the start of the month.

---

## 9. Troubleshooting

**The bot does not answer.**
1. Is it running? Check the logs.
2. Is `TELEGRAM_BOT_TOKEN` set and valid? (`getMe`, section 1.)
3. Are you messaging the right bot?
4. Is `ALLOWED_CHAT_IDS` set, and is this chat in it?

**`TELEGRAM_BOT_TOKEN is not set.`** The variable never reached the process. See [Configuration](#configuration): either a `.env` in the repo root, or `set -a; source` in the same terminal you run from.

**`/img` or `/web` returns an error.**
- With a Brave key: check Brave's dashboard for exhausted credits, and the logs for a Brave error. The bot falls back to `ddgs` when Brave fails.
- Without a key: `ddgs` scrapes public search engines, and an engine can refuse a request. Try again, and keep `ddgs` up to date with `pip install --upgrade ddgs`.

**Safe search "off" still returns filtered images.** On the keyless fallback it is best-effort: some `ddgs` engines pass the setting on and others ignore it. Set `BRAVE_API_KEY` for reliable control.

**A chart times out or fails.** yfinance can be slow on a cold first call; try again. Check the ticker on Yahoo Finance. Intraday intervals are limited, for example `1m` data only goes back about 7 days.

**`$SYMBOL` does not respond.** It needs the `$` prefix. Crypto uses Yahoo's format, `$BTC-USD`. In a group, privacy mode must be disabled (section 7).

**`/search` fails.** Check `PERPLEXITY_API_KEY`, the account's credits, and the logs.

**Docker build fails.** Is Docker Desktop running? Try `docker compose build --no-cache`, and run it from the folder that holds the `Dockerfile`.

**Railway build fails.** Read the build log under **Deployments**. The usual causes are a bad line in `requirements.txt` or a change that was not pushed.

For Windows-specific errors (conda not found, `EnvironmentNameNotFound`, `SSL_CERT_FILE`), see [section 3](#3-windows-and-git-bash-notes).

---

## 10. Quick reference

| Task | Command |
|---|---|
| Create the environment | `conda env create -f environment.yml` |
| Activate it | `conda activate switchboard-bot` |
| Load keys from a file outside the repo | `set -a; source "/path/to/your.env"; set +a` |
| Run locally | `python -m bot.main` |
| Run in Docker | `docker compose up -d --build` |
| Docker logs | `docker compose logs -f` |
| Stop Docker | `docker compose down` |
| Deploy to Railway | `git push` |
| Restart on Railway | Deployments, then Restart |
| Check which features are on | the ✅ / ⬜ lines at startup |
