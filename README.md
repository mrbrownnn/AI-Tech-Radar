# AI Tech Radar

AI Tech Radar is a Docker Compose service that refreshes GitHub and Hugging Face trend data, ranks items, generates a daily digest, and sends it to Telegram.

Detailed project docs live in [docs](docs/):

- [Project Specification](docs/project-specification.md)
- [Technical Design](docs/technical-design.md)
- [Database Design](docs/database-design.md)
- [API Contract](docs/api-contract.md)
- [Workflow Specification](docs/workflows.md)

## Prerequisites

- Docker Desktop or Docker Engine with Docker Compose
- Git
- Telegram bot token from `@BotFather`
- Telegram chat ID for the target chat
- Optional: GitHub token and Hugging Face token to reduce rate limits

## Installation

Clone the repository:

```bash
git clone https://github.com/mrbrownnn/daily_new.git
cd daily_new
```

Create your local environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set at least:

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Recommended optional values:

```env
GITHUB_TOKEN=
HUGGINGFACE_TOKEN=
```

## Telegram Setup

Create a bot:

1. Open Telegram and message `@BotFather`.
2. Send `/newbot`.
3. Copy the bot token into `TELEGRAM_BOT_TOKEN`.

Get your chat ID:

1. Send any message to your bot.
2. Open this URL in a browser, replacing the token:

```text
https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates
```

3. Copy `message.chat.id` into `TELEGRAM_CHAT_ID`.

## Run

Build and start the services:

```bash
docker compose up -d --build
```

Check service status:

```bash
docker compose ps
```

Check the API:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Manual Test

Refresh data:

```bash
curl -X POST http://localhost:8000/refresh
```

Generate a digest:

```bash
curl -X POST http://localhost:8000/digest
```

Send the digest to Telegram:

```bash
curl -X POST http://localhost:8000/notify
```

View top ranked items:

```bash
curl "http://localhost:8000/items?limit=5"
```

## Telegram Commands

After the app starts, the bot registers these commands:

- `/status` - show service status
- `/items` - show top ranked items
- `/latest` - send the latest digest
- `/refresh` - refresh data now
- `/digest` - generate a digest
- `/notify` - send the latest digest
- `/run` - refresh, digest, and notify

## Configuration

Important `.env` values:

```env
ENABLE_REALTIME_UPDATES=true
REALTIME_REFRESH_INTERVAL_MINUTES=15
DIGEST_TIME_LOCAL=08:05
DELIVERY_TIME_LOCAL=08:06
TOP_N_ITEMS=5
DIGEST_LANGUAGE=en
ENABLE_TELEGRAM_COMMANDS=true
EXPORT_MARKDOWN_REPORTS=true
```

Reports are exported to `reports/` when `EXPORT_MARKDOWN_REPORTS=true`.

## Development

Install dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
python -m pytest -q src/tests
```

Run the API locally without Docker:

```bash
uvicorn src.main:app --reload
```

## Troubleshooting

View app logs:

```bash
docker compose logs -f app
```

Restart the app after changing `.env`:

```bash
docker compose up -d --force-recreate app
```

Stop all services:

```bash
docker compose down
```

If Telegram messages are not sent, verify:

- The bot token is correct.
- You have sent at least one message to the bot.
- `TELEGRAM_CHAT_ID` matches the chat ID from `getUpdates`.
- The app logs do not show Telegram API errors.

