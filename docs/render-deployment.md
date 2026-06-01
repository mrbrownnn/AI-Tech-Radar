# Render Deployment

AI Tech Radar can be deployed on Render with the Blueprint in `render.yaml`.

## Resources

The Blueprint creates:

- Web service: `ai-tech-radar`
- PostgreSQL database: `ai-tech-radar-db`

## Required Secrets

Render prompts for these values during Blueprint setup:

```env
GITHUB_TOKEN=
HUGGINGFACE_TOKEN=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Do not hardcode these secrets in `render.yaml`.

## Runtime Behavior

The app runs as a Docker web service. It starts FastAPI and the in-process scheduler.

Enabled jobs:

- Realtime refresh every 15 minutes.
- Daily digest generation at `08:05` Asia/Bangkok time.
- Daily delivery at `08:06` Asia/Bangkok time.
- Telegram command long polling.

## Database URL

Render Postgres provides `DATABASE_URL` as a `postgresql://...` connection string. The application normalizes this to `postgresql+psycopg://...` for SQLAlchemy.

## Deploy Steps

1. Open Render Dashboard.
2. Select **New +**.
3. Select **Blueprint**.
4. Connect the GitHub repository.
5. Confirm the detected `render.yaml`.
6. Enter the required secret values.
7. Apply the Blueprint.

## Smoke Test

After deployment, open:

```text
https://<your-render-service>.onrender.com/health
```

Expected response:

```json
{"status":"ok"}
```

Then test Telegram:

```text
/status
/items
/run
```

