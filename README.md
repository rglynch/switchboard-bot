# Switchboard

A feature-packed Telegram bot with stock charts, multi-provider AI chat, web search, music link sharing, and more. Built as a modular, Docker-ready Python application designed for deployment on Railway.

## Features

**Stocks**
- `$AAPL` — inline stock quote detection in any message (real-time via Finnhub, yfinance fallback)
- `/chart MSFT 3d 1m rsi macd` — TradingView-style candlestick charts with optional indicators (RSI, MACD, Bollinger Bands, VWAP)
- `/chartv` — same as `/chart` (volume always shown)
- `/markets` — major index overview (S&P 500, Nasdaq, Dow, VIX, etc.)

**AI Chat (Multi-Provider)**
- `/ask question` — ask the default LLM
- `/ask:claude question` — force Claude
- `/ask:gpt question` — force GPT
- `/ask:claude:haiku question` — force Claude with Haiku model
- `/ask:gpt:4o question` — force GPT with gpt-4o model
- `/search query` — web-grounded AI search via Perplexity Sonar (returns cited answers)
- `/search:pro query` — use Perplexity Sonar Pro for deeper answers
- `/models` — show all available providers and model shortcuts

**Search**
- `/img query` — image search
- `/web query` — web search
- `/news query` — news search
- `/vid query` — video search
- Add `m` for moderate, `e` to turn safe search off: `/imge query`
- Add a number for more results (max 5): `/imgm4 cats`

**Other**
- Paste a Spotify/YouTube Music/Apple Music/etc. link → automatic Songlink universal link
- `/gp` — latest Xbox Game Pass news
- `/flip` or `/flip 5` — coin flip (max 10)
- `/teams` — random team splitter

**Easter Eggs**
- `$APPL` typo correction

## Architecture

```
bot/
├── main.py                          # Entry point, handler registration
├── config.py                        # All env vars, constants, feature flags
├── handlers/
│   ├── common.py                    # Shared decorators (allowlist, error handling)
│   ├── help.py                      # /start, /help
│   ├── stocks.py                    # $SYMBOL, /chart, /chartv, /markets
│   ├── search.py                    # /img, /web, /news, /vid
│   ├── llm_handler.py               # /ask, /ask:provider, /search
│   ├── songlink.py                  # Auto music link detection
│   ├── gamepass.py                   # /gp
│   ├── flip.py                      # /flip
│   └── teams.py                     # /teams
├── services/
│   ├── stock_data.py                # yfinance wrapper
│   ├── chart_renderer.py            # mplfinance TradingView-style charts
│   ├── search.py                    # DuckDuckGo search client
│   ├── songlink.py                  # Odesli/Songlink client
│   ├── llm.py                       # Provider registry builder
│   └── llm_providers/
│       ├── base.py                  # Abstract base + registry class
│       ├── claude.py                # Anthropic Claude
│       ├── openai.py                # OpenAI GPT
│       └── perplexity.py            # Perplexity Sonar (search-grounded)
Dockerfile
docker-compose.yml
railway.toml
.env.example
```

**Key design decisions:**
- **Provider registry pattern** for LLMs — adding a new provider (Gemini, Mistral, etc.) means writing one small class that implements `async def chat(message, system_prompt) -> str`
- **Service/handler separation** — services are pure API clients, handlers are Telegram-specific. Either can be tested or reused independently.
- **Feature flags** — missing an API key? That feature silently disables instead of crashing.

## Quick Start

### Local Development

```bash
git clone https://github.com/YOUR_USERNAME/switchboard-bot.git
cd switchboard-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your tokens
python -m bot.main
```

### Docker

```bash
cp .env.example .env   # fill in your tokens
docker compose up -d --build
docker compose logs -f
```

### Deploy to Railway

1. Push to GitHub
2. Create a new Railway project → "Deploy from GitHub repo"
3. Railway auto-detects the Dockerfile
4. Add environment variables in Railway dashboard (same as .env.example)
5. Deploy — done

No public endpoint needed (the bot uses polling, not webhooks).

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | From @BotFather |
| `LLM_DEFAULT` | No | Default LLM: `claude`, `gpt`, or `perplexity` |
| `ANTHROPIC_API_KEY` | No | Enables `/ask:claude` |
| `OPENAI_API_KEY` | No | Enables `/ask:gpt` |
| `PERPLEXITY_API_KEY` | No | Enables `/search` |
| `BRAVE_API_KEY` | No | Brave Search — image/web/news/video with full safe search control ($5 free credits/month). Falls back to DDG without it |
| `FINNHUB_API_KEY` | No | Real-time US stock quotes (falls back to yfinance without it) |
| `SONGLINK_API_KEY` | No | Optional, removes Songlink rate limits |
| `ALLOWED_CHAT_IDS` | No | Comma-separated chat ID allowlist |
| `LOG_LEVEL` | No | DEBUG, INFO, WARNING, ERROR |

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Bot Framework | python-telegram-bot 21.x |
| Stock Data | Finnhub (real-time) + yfinance (fallback) |
| Charts | mplfinance + matplotlib |
| HTTP Client | httpx (async) |
| LLM | Anthropic / OpenAI / Perplexity (swappable) |
| Search | Brave Search (primary) + DuckDuckGo (fallback) |
| Deployment | Docker → Railway |

## Extending

**Add a new LLM provider:**
1. Create `bot/services/llm_providers/my_provider.py`
2. Implement the `LLMProvider` base class (one method: `async def chat`)
3. Add env vars in `config.py`
4. Register it in `bot/services/llm.py`

**Add a new command:**
1. Create `bot/handlers/my_handler.py` with a `register(app)` function
2. Import and call `register` in `bot/main.py`

## Disclaimer

For informational/educational purposes only. Not financial advice. Market data from Yahoo Finance may be delayed.

## License

MIT
