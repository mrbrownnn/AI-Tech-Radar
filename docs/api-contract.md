# API Contract

This document defines the internal HTTP API for AI Tech Radar.

The API is intended for health checks, manual job triggering, and lightweight inspection. Scheduled jobs remain the primary execution path.

## GET /health

Purpose:

- Check application health.

Response:

```json
{
  "status": "ok"
}
```

## POST /refresh

Purpose:

- Trigger data refresh manually.

Response:

```json
{
  "status": "started"
}
```

Notes:

- The endpoint should enqueue or start the refresh job.
- The request should return quickly and should not block until the full refresh finishes.

## POST /crawl

Purpose:

- Compatibility alias for `POST /refresh`.

Response:

```json
{
  "status": "started"
}
```

## POST /digest

Purpose:

- Generate digest manually.

Response:

```json
{
  "status": "generated"
}
```

Notes:

- Uses the latest ranked items.
- Stores the generated digest in PostgreSQL.
- Exports Markdown when enabled.

## POST /notify

Purpose:

- Send latest digest manually.

Response:

```json
{
  "status": "sent"
}
```

Notes:

- Sends the latest unsent digest by default.
- Writes delivery status to `delivery_logs`.

## GET /items

Purpose:

- Inspect normalized items and scores.

Query parameters:

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `source` | string | No | Filter by source |
| `type` | string | No | Filter by item type |
| `limit` | integer | No | Maximum number of items to return |

Response:

```json
[
  {
    "title": "",
    "source": "",
    "score": 0
  }
]
```

Recommended response fields for implementation:

```json
[
  {
    "id": "00000000-0000-0000-0000-000000000000",
    "title": "example/repo",
    "source": "github",
    "type": "repository",
    "url": "https://github.com/example/repo",
    "score": 92.5
  }
]
```

## GET /digests/latest

Purpose:

- Fetch the latest generated digest.

Response:

```json
{
  "date": "",
  "content": ""
}
```

Recommended response fields for implementation:

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "date": "2026-06-01",
  "channel": "telegram",
  "content": "# AI Tech Radar"
}
```

## Error Response

All endpoints should return a consistent error shape.

```json
{
  "status": "error",
  "message": "Human-readable error message"
}
```
