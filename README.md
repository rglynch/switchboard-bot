# Switchboard

Switchboard is a public version of the Telegram bot my friends and I use every day in our group chat: stock quotes and charts, questions to four AI models, web and image search, and music links that open on any service.

I wrote the original version from scratch in 2021, split between AWS Lambda and a self-hosted charting service. It now runs as one Docker deployment on Railway. In 2026, I directed an AI model through a rebuild: I gave it my old bot, my requirements, and what I wanted improved. Then I worked through the result to understand it, break it, fix it, and modify it. This repository is that rework, cleaned up for public release, and it is where changes are made before they go to the version my friends use.

## Features

**Stocks**
- `$AAPL` anywhere in a message: inline quote (real-time via Finnhub, yfinance fallback)
- `/chart MSFT 3d 1m rsi macd`: candlestick chart with optional indicators (RSI, MACD, Bollinger Bands, VWAP)
- `/chartv`: the same chart with volume
- `/markets`: major index overview (S&P 500, Nasdaq, Dow, VIX and more)

**AI chat, multi-provider**
- `/ask question`: ask the default provider
- `/ask:claude question`, `/ask:gpt question`, `/ask:grok question`: pick a provider
- `/ask:claude:sonnet question`: pick a provider and a model shortcut (or pass a full model string)
- `/ask:grok:web question`: Grok with live web search (extra cost)
- `/search query`: web-grounded answer with citations via Perplexity Sonar; `/search:pro` for Sonar Pro
- `/models`: list the providers and models this deployment allows
- `/usage`: monthly usage against each provider's limit

**Search**
- `/img`, `/web`, `/news`, `/vid` followed by a query
- Add `m` for moderate safe search or `e` to turn it off: `/imge query`
- Add a number for more results, up to 5: `/imgm4 cats`

**Other**
- Paste a Spotify, YouTube Music, Apple Music (or similar) link and get a Songlink that opens on every service
- `/gp`: the latest Xbox Game Pass news
- `/flip` or `/flip 5`: coin flips, up to 10
- `/teams`: random team splitter
- `$APPL` gets a typo correction to `$AAPL`

## Quick start

Full walkthrough, including Railway and Windows notes: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

### Local (conda)

```bash
git clone https://github.com/rglynch/switchboard-bot.git
cd switchboard-bot
conda env create -f environment.yml
conda activate switchboard-bot
cp .env.example .env        # then fill in at least TELEGRAM_BOT_TOKEN
python -m bot.main
```

### Docker

`docker-compose.yml` passes the variables it lists through from your shell, so export them first:

```bash
set -a; source .env; set +a
docker compose up -d --build
docker compose logs -f
```

## Environment variables

Only `TELEGRAM_BOT_TOKEN` is required. The startup log shows which features are on (✅) and off (⬜).

| Variable | Default | What it does |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | none (required) | Bot token from @BotFather |
| `ALLOWED_CHAT_IDS` | empty = all chats | Comma-separated allowlist of chat IDs |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LLM_DEFAULT` | `grok` | Provider `/ask` uses: `claude`, `gpt`, `grok` or `perplexity` |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` | / `claude-haiku-4-5` | Enables Claude |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | / `gpt-5.4-mini` | Enables GPT |
| `GROK_API_KEY` / `GROK_MODEL` | / `grok-4.1-fast` | Enables Grok |
| `PERPLEXITY_API_KEY` / `PERPLEXITY_MODEL` | / `sonar` | Enables `/search` |
| `ALLOWED_MODELS_<PROVIDER>` | empty = all models | Restrict which models users can pick, e.g. `ALLOWED_MODELS_CLAUDE=haiku,sonnet` |
| `MONTHLY_LIMIT_<PROVIDER>` | empty = unlimited | Monthly request cap per provider, e.g. `MONTHLY_LIMIT_CLAUDE=200` |
| `USAGE_WARN_PCT` | `80` | Percent of a limit at which replies start warning |
| `BRAVE_API_KEY` | none | Brave Search API for `/img`, `/web`, `/news`, `/vid`, with full safe search control. Without it, search falls back to the keyless `ddgs` library |
| `FINNHUB_API_KEY` | none | Real-time US quotes. Without it, quotes come from yfinance (delayed) |
| `SONGLINK_API_KEY` | none | Optional; lifts Songlink rate limits |

## Architecture

```
bot/
├── main.py                      # Entry point: logging, feature report, handler registration
├── config.py                    # Every env var, constant and feature flag
├── handlers/                    # Telegram-facing: parse the message, call a service, reply
│   ├── common.py                # Shared decorators (chat allowlist, error handling)
│   ├── help.py                  # /start, /help
│   ├── stocks.py                # $SYMBOL, /chart, /chartv, /markets, the $APPL correction
│   ├── search.py                # /img, /web, /news, /vid
│   ├── llm_handler.py           # /ask, /search, /models, /usage
│   ├── songlink.py              # Music link detection
│   ├── gamepass.py              # /gp
│   ├── flip.py                  # /flip
│   └── teams.py                 # /teams
└── services/                    # Plain API clients, no Telegram code
    ├── stock_data.py            # Finnhub (real-time) with yfinance fallback
    ├── chart_renderer.py        # mplfinance charts
    ├── search.py                # Brave Search API, with ddgs as the keyless fallback
    ├── songlink.py              # Odesli/Songlink client
    ├── usage_tracker.py         # Monthly per-provider request counts and limits
    ├── llm.py                   # Builds the provider registry from config
    └── llm_providers/
        ├── base.py              # Abstract provider, model shortcuts and restrictions, registry
        ├── claude.py            # Anthropic
        ├── openai.py            # OpenAI
        ├── grok.py              # xAI
        └── perplexity.py        # Perplexity Sonar
Dockerfile · docker-compose.yml · railway.toml · environment.yml · requirements.txt · .env.example
```

**Design decisions**
- **Provider registry for LLMs.** Each provider is one small class implementing `async def chat(...)`. Adding a provider means one new file plus registering it.
- **Handlers and services are separate.** Services hold no Telegram code. For example, only `services/stock_data.py` talks to Finnhub or yfinance, so `$SYMBOL`, `/chart` and `/markets` all go through it, and changing the data provider touches one file.
- **Feature flags from config.** A missing API key turns that feature off instead of crashing the bot.
- **Official API first, keyless fallback second.** Search uses Brave's API when a key is set and falls back to the `ddgs` library when it isn't.

## Tech stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Bot framework | python-telegram-bot 21.x |
| Stock data | Finnhub (real-time) with yfinance fallback |
| Charts | mplfinance and matplotlib |
| HTTP client | httpx (async) |
| LLMs | Anthropic, OpenAI, xAI, Perplexity |
| Search | Brave Search API, with `ddgs` as the keyless fallback |
| Deployment | Docker; Railway |

## Extending

**Add an LLM provider**
1. Create `bot/services/llm_providers/my_provider.py` implementing the `LLMProvider` base class
2. Add its env vars in `config.py`
3. Register it in `bot/services/llm.py`

**Add a command**
1. Create `bot/handlers/my_handler.py` with a `register(app)` function
2. Import it and call `register` in `bot/main.py`

## License

MIT. See [LICENSE](LICENSE).

## Disclaimer

For informational and educational purposes only. Not financial advice. Market data from Yahoo Finance may be delayed.
