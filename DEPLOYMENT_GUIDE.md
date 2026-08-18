# Deployment Walkthrough

A step-by-step guide to getting the bot running locally, containerized with Docker, deployed to Railway, and locked down securely.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Local Setup (No Docker)](#2-local-setup-no-docker)
3. [Docker Basics](#3-docker-basics)
4. [Deploy to Railway](#4-deploy-to-railway)
5. [Security Hardening](#5-security-hardening)
6. [Monitoring & Maintenance](#6-monitoring--maintenance)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Prerequisites

### Telegram Bot Setup

You can either reuse your existing bot or create a new one. Everything goes through [@BotFather](https://t.me/BotFather) on Telegram.

**Using your existing bot:**

Your bot is already created, so you just need a valid token. If you still have the token, skip to "Test your token" below. If the token was compromised (e.g. hardcoded in old code, shared in a chat), revoke it first:

1. Open [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/mybots`
3. Select your bot from the list
4. Tap **"API Token"** to view the token. If you don't need to revoke it, stop here and move on to "Test your token" below.
5. Tap **"Revoke current token"** — this kills the old token immediately, so anything using it stops working
6. BotFather gives you a new token — copy and save it somewhere safe

**Creating a new bot (if you want a fresh one):**

1. Open [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Give it a display name (e.g. "Rick's Bot")
4. Give it a username (must end in `bot`, e.g. `ricks_toolbox_bot`)
5. BotFather gives you a token — save it

**Test your token works:**

Paste this in a browser (replace `YOUR_TOKEN`):

```
https://api.telegram.org/botYOUR_TOKEN/getMe
```

If you get a JSON response with your bot's username, the token is valid.

**Other useful BotFather commands:**

- `/setdescription` — what people see before starting a chat with the bot
- `/setcommands` — set the command menu that appears when users type `/`
- `/setuserpic` — give your bot an avatar
- `/revoke` — revoke and regenerate the token (old one dies instantly)

**Setting the command menu** (optional but nice). Send `/setcommands` to BotFather, select your bot, then paste:

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

### Other accounts you need

- **GitHub account** — for pushing your code and connecting to Railway.
- **Railway account** — sign up at [railway.app](https://railway.app) with your GitHub account (free tier available).

### API keys — where to get them

None of these are required. The bot auto-disables features when keys are missing. But here's how to get each one.

**Anthropic (Claude)**

1. Go to [console.anthropic.com](https://console.anthropic.com) and create an account
2. Go to **Settings → API Keys → Create Key**
3. Copy the key (starts with `sk-ant-...`)
4. Add credits — Claude API is pay-per-token. $5 of credits lasts months for casual chat use.
5. In your `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   ANTHROPIC_MODEL=claude-haiku-4-5-20251001
   ```
6. Available models (cheapest → most expensive):
   - `claude-haiku-4-5-20251001` — cheapest, fastest. Great default for a chat bot.
   - `claude-sonnet-4-6-20260310` — balanced. Smarter but costs ~5-10x more than Haiku.
   - `claude-opus-4-6-20260310` — most capable. Expensive. Probably overkill for this.

**OpenAI (GPT)**

1. Go to [platform.openai.com](https://platform.openai.com) and create an account
2. Go to **API Keys** (left sidebar) → **Create new secret key**
3. Copy the key (starts with `sk-...`)
4. Add credits under **Billing**. Same deal — $5 lasts a long time for casual use.
5. In your `.env`:
   ```
   OPENAI_API_KEY=sk-xxxxx
   OPENAI_MODEL=gpt-5.4-mini
   ```
6. Available models (cheapest → most expensive):
   - `gpt-5.4-nano` — cheapest, fastest. Good for simple queries.
   - `gpt-5.4-mini` — great balance of cost and capability. Recommended default.
   - `gpt-5.4` — flagship. Expensive. Use via `/ask:gpt:5.4` for tough questions.
   - `gpt-4.1` / `gpt-4.1-mini` — older but still available in the API.

**xAI (Grok)**

1. Go to [console.x.ai](https://console.x.ai) and create an account
2. Go to **API Keys** → **Create Key** → copy it
3. Add credits under billing. Grok 4.1 Fast is extremely cheap — $5 of credits will last a very long time.
4. In your `.env`:
   ```
   GROK_API_KEY=your_key
   GROK_MODEL=grok-4.1-fast
   ```
5. Available models (cheapest → most expensive):
   - `grok-4.1-fast` — incredibly cheap ($0.20/M input tokens). Best value for a chat bot by far. Recommended default.
   - `grok-4` — flagship. Much more expensive ($3/M input). Use via `/ask:grok:4` when you need heavy reasoning.
   - `grok-3` — older generation, same price as Grok 4. No reason to use over Grok 4.

**Perplexity (web-grounded AI search)**

1. Go to [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api)
2. You need a Perplexity account — free tier works but you must add a payment method for API access
3. Click **Generate** to create an API key (starts with `pplx-...`)
4. Add credits — $5 gets you 1,000 searches, no monthly expiry
5. In your `.env`:
   ```
   PERPLEXITY_API_KEY=pplx-xxxxx
   PERPLEXITY_MODEL=sonar
   ```
6. Other models: `sonar` (fast, cheap — the default), `sonar-pro` (deeper reasoning, higher cost), `sonar-reasoning-pro` (most capable, premium pricing)

> **⚠️ Perplexity pricing warning:** Perplexity charges per-token AND a per-search fee on top ($5/1,000 searches). They also count retrieved web content as input tokens, which can inflate costs 10-20x beyond what you'd expect from the headline token price. Stick to the basic `sonar` model and set `MONTHLY_LIMIT_PERPLEXITY=20` until you've verified the actual costs. Avoid `sonar-reasoning-pro` and "High" search depth — these can cost $0.40+ per query. If Perplexity feels too expensive, just skip it — `/web` and `/img` handle search for free (via DuckDuckGo), and `/ask` handles LLM questions with predictable Claude/GPT/Grok pricing.

**Brave Search (web, image, news, video — with full safe search control)**

1. Go to [api-dashboard.search.brave.com](https://api-dashboard.search.brave.com/)
2. Sign up and select the **"Search"** plan (left one — NOT "Answers")
3. Create an API key
4. In your `.env`:
   ```
   BRAVE_API_KEY=your_api_key
   ```
5. You get $5 free credits every month, automatically applied (~1,000 queries/month for free)
6. Safe search is fully configurable including off — `/imge` turns safe search off
7. Without this key, search falls back to DuckDuckGo (free but can't turn safe search off for images)

**Finnhub (real-time US stock quotes)**

1. Go to [finnhub.io/register](https://finnhub.io/register) — no credit card needed
2. Copy your API key from the dashboard
3. In your `.env`:
   ```
   FINNHUB_API_KEY=xxxxx
   ```
4. Free tier gives you 60 calls/minute, real-time US quotes, company profiles, and news
5. Without this key the bot still works — quotes just come from yfinance (delayed 15-30 min) instead

**Songlink (optional)**

Works without a key. If you want to remove rate limits:
1. Go to [odesli.co](https://odesli.co/) and contact them for API access
2. In your `.env`:
   ```
   SONGLINK_API_KEY=xxxxx
   ```

### Choosing your default LLM

Set which provider `/ask` uses when you don't specify one:

```
LLM_DEFAULT=claude      # /ask uses Claude by default
LLM_DEFAULT=gpt         # /ask uses GPT by default
LLM_DEFAULT=perplexity  # /ask uses Perplexity by default
```

You can always override per-message with `/ask:claude`, `/ask:gpt`, or `/ask:perplexity` regardless of the default. You can also pass a specific model: `/ask:claude:haiku` or `/ask:gpt:nano` (see below).

### Swapping and updating models

Models change constantly. Here's how to keep up.

**Change the default model (no code change needed):**

Just update the env var on Railway (or in your `.env`) and restart:

```
ANTHROPIC_MODEL=claude-sonnet-4-6-20260310
```

The bot picks this up on next startup. No code change, no rebuild.

**Use a different model per-message (no change needed at all):**

Anyone in the chat can type the full model string as the model argument:

```
/ask:claude:claude-sonnet-4-6-20260310 explain quantum computing
/ask:gpt:gpt-5.4 what is dark matter
```

If the shortcut isn't in the alias list, it gets passed through as-is to the API. So new models work immediately — you don't have to wait for a code update.

**Add new shortcuts (small code change):**

When a new model drops and you want a clean shortcut, edit the `model_aliases` dict in the provider file. For example, if Anthropic releases Claude 5:

1. Open `bot/services/llm_providers/claude.py`
2. Add to `model_aliases`:
   ```python
   model_aliases = {
       "haiku":   "claude-haiku-4-5-20251001",
       "sonnet":  "claude-sonnet-4-6-20260310",
       "opus":    "claude-opus-4-6-20260310",
       "claude5": "claude-5-20260601",        # ← new
   }
   ```
3. Push to GitHub → Railway auto-deploys
4. Now `/ask:claude:claude5 hello` works

**Current shortcuts (as of March 2026):**

| Command | Resolves to | Notes |
|---|---|---|
| `/ask:claude:haiku` | claude-haiku-4-5 | Cheapest Claude. Default. |
| `/ask:claude:sonnet` | claude-sonnet-4-6 | Latest Sonnet |
| `/ask:claude:opus` | claude-opus-4-6 | Most expensive Claude |
| `/ask:gpt:nano` | gpt-5.4-nano | Cheapest GPT |
| `/ask:gpt:mini` | gpt-5.4-mini | Great value. Default. |
| `/ask:gpt:5.4` | gpt-5.4 | Flagship. Expensive. |
| `/ask:gpt:4.1` | gpt-4.1 | Older, still works |
| `/ask:grok:fast` | grok-4.1-fast | Cheapest overall. Default. |
| `/ask:grok:4` | grok-4 | Flagship Grok. Expensive. |
| `/ask:grok:3` | grok-3 | Older, same price as Grok 4 |
| `/search` | sonar | Cheapest Perplexity. Default. |
| `/search:pro` | sonar-pro | Deeper answers |
| `/search:reasoning` | sonar-reasoning-pro | Premium |

**Recommended budget defaults (what's set out of the box):**
- Grok: `grok-4.1-fast` — dirt cheap, great quality. The default for `/ask`.
- Claude: `claude-haiku-4-5` — fast, cheap, good enough for chat
- GPT: `gpt-5.4-mini` — current and affordable
- Perplexity: `sonar` — cheapest search option

Use the shortcuts to reach up to more expensive models when you actually need them, while keeping the defaults cheap for everyday use.

### Stock data — how it works now

The bot uses a two-tier approach:

- **Quick quotes** (`$MSFT`): Finnhub first (real-time US stocks), yfinance fallback (delayed, but covers everything including crypto, international, indices)
- **Chart data** (`/chart`): always yfinance (Finnhub's free tier doesn't serve historical candles well)
- **Market indices** (`/markets`): always yfinance (handles `^GSPC` style symbols)

If `FINNHUB_API_KEY` is not set, everything silently falls back to yfinance. You can check the logs to see which source each quote came from — it logs `"Quote for MSFT via Finnhub (real-time)"` or `"Quote for BTC-USD via yfinance (fallback)"`.

### Upgrading further in the future

All stock logic lives in one file: `bot/services/stock_data.py`. Handlers never touch Finnhub or yfinance directly — they call `fetch_quote()` and get back a `QuoteData` dataclass. So swapping to a different provider means rewriting the internals of that one file.

**Other alternatives worth knowing about:**

- **Polygon.io** — free tier for delayed data, paid for real-time. Very clean REST API.
- **Twelve Data** — free tier with 8 calls/minute, REST + WebSocket.
- **Alpha Vantage** — free, ~25 calls/day. Good for low-volume.
- **FMP (Financial Modeling Prep)** — free tier, best for fundamentals data.

For chart rendering, none of this matters — `chart_renderer.py` just takes a pandas DataFrame with OHLCV columns. It doesn't care where the data came from.

### Software to install on your machine

- **Git** — [git-scm.com](https://git-scm.com/downloads)
- **Python 3.11+** — [python.org](https://www.python.org/downloads/)
- **Docker Desktop** (optional, for local container testing) — [docker.com](https://www.docker.com/products/docker-desktop/)

---

## 2. Local Setup (No Docker)

This is for testing on your own machine before deploying anywhere.

```bash
# 1. Extract the project (or clone your repo)
tar xzf telegram-bot.tar.gz
cd telegram-bot

# 2. Create a conda environment
conda create -n telegrambot python=3.12 -y
conda activate telegrambot

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
cp .env.example .env          # macOS/Linux
copy .env.example .env         # Windows
```

Now edit `.env` with your actual tokens. At minimum you need:

```
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

Add any other API keys you have. Then run:

```bash
python -m bot.main
```

You should see logs like:

```
2026-03-21 12:00:00 | bot.main | INFO | ✅ stock_chart
2026-03-21 12:00:00 | bot.main | INFO | ✅ llm_claude
2026-03-21 12:00:00 | bot.main | INFO | ⬜ llm_gpt
2026-03-21 12:00:00 | bot.main | INFO | Bot started — polling for updates …
```

Go to your bot on Telegram and send `/help`. If it responds, you're good. `Ctrl+C` to stop.

---

### Conda environment management

```bash
# See all your conda environments
conda env list

# Reactivate later (every time you open a new terminal)
conda activate telegrambot

# Deactivate when done
conda deactivate

# If you need to nuke it and start over
conda env remove -n telegrambot
```

There's also an `environment.yml` in the project so you can create the environment in one shot:

```bash
conda env create -f environment.yml
conda activate telegrambot
```

> **Note:** Docker doesn't use conda — it installs dependencies directly with pip inside the container. Conda is only for local development on your machine.

> **Alternative:** If you ever want to use plain venv instead of conda:
> `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

---

## 3. Docker Basics

### What Docker does

Docker packages your bot + Python + all dependencies into a single "container" — a lightweight, isolated box that runs the same everywhere. You build it once and deploy it anywhere (your laptop, Railway, AWS, etc.) without worrying about Python versions or missing libraries.

### Key concepts

- **Image** — a snapshot/template of your app. Built from the `Dockerfile`.
- **Container** — a running instance of an image. This is your actual bot process.
- **docker-compose.yml** — a config file that makes running containers easier (sets env vars, restart policy, etc.)

### Build and run locally with Docker

```bash
cd telegram-bot

# Build the image (this installs Python, pip dependencies, copies your code)
docker compose build

# Run it (reads .env file automatically, restarts on crash)
docker compose up -d

# Check it's running
docker compose ps

# Watch the logs
docker compose logs -f

# Stop it
docker compose down
```

That's it. If `docker compose logs` shows the bot polling for updates and you can message it on Telegram, the container works.

### What's in the Dockerfile (plain English)

```dockerfile
FROM python:3.12-slim          # Start from official Python image
ENV MPLBACKEND=Agg             # Tell matplotlib: no display needed
WORKDIR /app                   # Work inside /app
RUN apt-get install ...        # Install C libraries for chart rendering
COPY requirements.txt .        # Copy requirements first (Docker caches this layer)
RUN pip install ...            # Install Python packages
COPY bot/ bot/                 # Copy your bot code
RUN useradd appuser            # Create non-root user (security)
USER appuser                   # Run as that user, not root
CMD ["python", "-m", "bot.main"]  # Start the bot
```

---

## 4. Deploy to Railway

### Step 1: Push to GitHub

```bash
cd telegram-bot
git init
git add .
git commit -m "Initial commit"

# Create a repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

**Important:** make sure `.env` is in your `.gitignore` (it already is). Never push real tokens to GitHub.

### Step 2: Create Railway project

1. Go to [railway.app/dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub Repo"**
4. Authorize Railway to access your GitHub if prompted
5. Select your bot repo
6. Railway will auto-detect the `Dockerfile` and start building

### Step 3: Add environment variables

1. In your Railway project, click on the service (your bot)
2. Go to the **"Variables"** tab
3. Add each variable one by one:

```
TELEGRAM_BOT_TOKEN = your_actual_token
LLM_DEFAULT = grok
GROK_API_KEY = ...
ANTHROPIC_API_KEY = sk-ant-...
BRAVE_API_KEY = ...
FINNHUB_API_KEY = ...
PERPLEXITY_API_KEY = pplx-...
```

Or click **"RAW Editor"** and paste them all at once in `KEY=VALUE` format.

### Step 4: Deploy

Railway auto-deploys when you push to `main`. After adding variables, it will redeploy automatically. Check the **"Deployments"** tab for build logs.

### Step 5: Verify

Message your bot on Telegram. If it responds, you're live.

### Updating the bot

Any time you push to `main`, Railway rebuilds and redeploys automatically:

```bash
git add .
git commit -m "Added new feature"
git push
```

Railway handles zero-downtime deploys — the old container keeps running until the new one is healthy.

---

## 5. Security Hardening

### Secrets management

**The #1 rule: tokens never go in code or Git.**

- All secrets are environment variables, read by `os.getenv()` in `config.py`
- `.env` is gitignored — it only exists on your local machine
- On Railway, secrets are stored encrypted in their dashboard and injected at runtime
- Railway encrypts variables at rest and in transit

**Rotate your old tokens immediately.** The ones from your old `config.py` (that were hardcoded) are compromised since they were in this conversation. Go to @BotFather → `/revoke` to kill the old Telegram tokens. Regenerate any other keys too.

### Container security

The Dockerfile already handles the basics:

- **Non-root user** — the bot runs as `appuser`, not `root`. If someone somehow gets code execution inside the container, they can't escalate to root.
- **Slim base image** — `python:3.12-slim` has minimal packages installed, reducing attack surface.
- **No SSH, no shell access** — the container only runs your bot process. There's no way to SSH into it.

### Network security

- **Polling mode (not webhooks)** — the bot makes outbound connections to Telegram's API. It doesn't listen on any port. There is no inbound attack surface. Nobody can send traffic to your container because it isn't accepting any.
- This is a major security advantage over your old Lambda webhook setup, which had a public HTTP endpoint.

### Railway-specific security

- Railway runs containers in isolated environments (each service gets its own sandbox)
- There's no public URL unless you explicitly create one (you don't need one for a polling bot)
- Go to your service **Settings** → make sure **"Public Networking"** is disabled. Your bot doesn't need it.

### Adding the bot to a group chat

1. Open your group chat on Telegram
2. Tap the group name at the top to open group info
3. Tap **"Add Members"** (or **"Add"** on some clients)
4. Search for your bot's username (e.g. `@ricks_toolbox_bot`)
5. Add it to the group

By default Telegram bots can't read all messages in a group — they only see commands (messages starting with `/`) and messages that explicitly @mention them. To let the bot see `$MSFT` and music links:

1. Go back to [@BotFather](https://t.me/BotFather)
2. Send `/setprivacy`
3. Select your bot
4. Choose **"Disable"** — this means the bot CAN read all messages (confusing naming, but "disable privacy mode" = "enable reading")

Without this step, `$SYMBOL` detection and Songlink auto-detection won't work. Commands like `/chart` and `/help` will still work either way.

### Getting your chat ID

You need the chat ID to set up the allowlist. Several ways to get it:

**Method 1: Check the bot logs (easiest)**

1. Make sure the bot is running (locally or on Railway)
2. Send any message in the group
3. Check the logs — when the bot receives a message, the chat ID appears in the log output
4. Group chat IDs are negative numbers. Your personal DM chat ID is a positive number.

**Method 2: Use the Telegram API directly**

After the bot has received at least one message, paste this in a browser:

```
https://api.telegram.org/botYOUR_TOKEN/getUpdates
```

Look through the JSON for `"chat":{"id": ...}`. That's your chat ID.

**Method 3: Use @userinfobot**

Add [@userinfobot](https://t.me/userinfobot) to the group, and it will reply with the chat ID. Remove it after.

### Chat allowlisting

Once you have the chat ID(s), lock the bot down so it only responds there:

1. Add to Railway variables (or your `.env`):
   ```
   ALLOWED_CHAT_IDS=<single chat id>
   ```
2. For multiple chats, comma-separate them:
   ```
   ALLOWED_CHAT_IDS=<chat id 1>, <chat id 2>
   ```
3. The bot will silently ignore messages from any other chat
4. Leave it empty (or don't set it) to allow all chats

### Dependency security

- Pin major versions in `requirements.txt` (already done)
- Periodically run `pip audit` to check for known vulnerabilities
- Keep the Docker base image updated — Railway rebuilds from scratch each deploy, so you always get the latest `python:3.12-slim` patches

### What you DON'T need to worry about

- **DDoS** — your bot polls Telegram, it doesn't expose a port. Can't be DDoSed.
- **SQL injection** — there's no database.
- **XSS/CSRF** — there's no web interface.
- **Man-in-the-middle** — all API calls use HTTPS. Telegram's Bot API is TLS-encrypted.

The realistic attack vectors for a Telegram bot are: compromised API keys (solved by env vars + rotation), and malicious input from users (solved by not using `eval()`, which your old calculator command wisely had commented out).

---

## 6. Monitoring & Maintenance

### Viewing logs on Railway

1. Go to your project → click the service → **"Deployments"** tab
2. Click the active deployment → **"View Logs"**
3. You'll see real-time output from the bot

### What to watch for

- `Bot started — polling for updates …` means it's healthy
- `Could not fetch info for XXXX` — yfinance hiccup, usually transient
- `DDG search error` — DuckDuckGo may be temporarily rate limiting, try again
- `LLM provider X not available` — missing API key for that provider

### Restarting

In Railway: go to your service → **"Deployments"** → click the three dots → **"Restart"**

Or just push an empty commit to trigger a redeploy:

```bash
git commit --allow-empty -m "redeploy"
git push
```

### Cost monitoring

Railway dashboard shows CPU, memory, and network usage. A Telegram bot sitting idle uses nearly zero resources. You'll only see spikes when someone requests a chart (matplotlib rendering). Expected Railway cost: $1-3/month.

### Cost controls (usage limiter)

The bot has a built-in monthly request limiter to prevent surprise bills. Set limits per provider as environment variables:

```
MONTHLY_LIMIT_CLAUDE=200
MONTHLY_LIMIT_GPT=200
MONTHLY_LIMIT_GROK=500
MONTHLY_LIMIT_PERPLEXITY=100
USAGE_WARN_PCT=80
```

How it works:

- Every `/ask` and `/search` call counts against the provider's limit
- At 80% usage (configurable with `USAGE_WARN_PCT`), responses include a warning like "⚠️ claude: 160/200 requests used this month (40 remaining)"
- At 100%, the bot blocks requests with a funny message telling people to bug Rick
- Counters reset automatically at the start of each calendar month
- Type `/usage` in the chat to see a dashboard with progress bars
- Search (`/img`, `/web`, `/news`, `/vid`) uses DuckDuckGo which is free and unlimited — no limit needed

**Rough cost estimates to help you set limits:**

| Provider | Cost per request (typical) | 100 requests ≈ | 200 requests ≈ |
|---|---|---|---|
| Claude Haiku | $0.002–0.005 | $0.20–0.50 | $0.40–1.00 |
| Claude Sonnet | $0.01–0.03 | $1–3 | $2–6 |
| GPT-5.4-mini | $0.002–0.005 | $0.20–0.50 | $0.40–1.00 |
| GPT-5.4 | $0.01–0.05 | $1–5 | $2–10 |
| Grok 4.1 Fast | $0.0001 | $0.01 | $0.02 |
| Perplexity Sonar | $0.005+ | $0.50+ | $1.00+ |
| DuckDuckGo | Free | $0 | $0 |

These are rough — actual cost depends on response length. But for a group chat where people send a few queries a day, setting Claude at 200 and Perplexity at 100 would cap you at about $5-8/month worst case.

If no limit is set for a provider, it's unlimited. You can add limits for some providers and not others.

---

## 7. Troubleshooting

### "Bot doesn't respond to messages"

1. Check Railway logs — is it running?
2. Is `TELEGRAM_BOT_TOKEN` set correctly?
3. Did you talk to the right bot? (Check the username with @BotFather)
4. Is `ALLOWED_CHAT_IDS` set? If so, is your chat in the list?

### "Chart command times out"

- yfinance can be slow on first call (cold cache). Try again.
- Invalid symbol? Check the exact ticker on Yahoo Finance.
- Period/interval mismatch? e.g., `1m` interval only works up to 7 days.

### "/search doesn't work"

- Is `PERPLEXITY_API_KEY` set?
- Do you have credits on your Perplexity account?
- Check logs for the specific error.

### "/img or /web returns errors"

- If Brave is configured: check if your $5 monthly credits ran out. The bot auto-falls back to DDG, but DDG can't turn safe search off for images. Check logs for "Brave rate limited" or "Brave error."
- If DDG only: DuckDuckGo may be temporarily rate limiting your IP. Wait a minute and try again.
- If it persists, DDG may have changed their internal API. Check if `duckduckgo-search` has a newer version: `pip install --upgrade duckduckgo-search`

### "Docker build fails"

- Make sure Docker Desktop is running
- Try `docker compose build --no-cache` to rebuild from scratch
- Check you're in the right directory (where `Dockerfile` lives)

### "Railway build fails"

- Check the build logs in the Deployments tab
- Most common issue: a typo in `requirements.txt` or a missing file
- Railway builds from whatever is on `main` in GitHub — make sure you pushed

### "$SYMBOL doesn't respond"

- The symbol must have a `$` prefix: `$AAPL` works, `AAPL` doesn't
- yfinance only covers symbols listed on Yahoo Finance
- Crypto uses different format: `$BTC-USD`, not `$BTC`

---

## Quick Reference

| Task | Command |
|---|---|
| Run locally | `python -m bot.main` |
| Build Docker | `docker compose build` |
| Run Docker | `docker compose up -d` |
| View Docker logs | `docker compose logs -f` |
| Stop Docker | `docker compose down` |
| Deploy | `git push` (Railway auto-deploys) |
| Restart on Railway | Deployments → Restart |
| Check features | Look at startup logs for ✅/⬜ |
