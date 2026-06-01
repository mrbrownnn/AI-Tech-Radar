# Workflow Specification

This document defines the scheduled workflows, notification templates, error handling, and acceptance criteria for AI Tech Radar.

The default realtime schedule is:

- Every 15 minutes: Realtime refresh workflow.
- 08:05: Daily digest workflow.

The refresh interval and daily digest time should be configurable by the user.

## Realtime Refresh Workflow

Default interval:

- Every 15 minutes.

Flow:

```text
Scheduler triggers Realtime Refresh Job
  -> GitHub Collector
  -> Hugging Face Collector
  -> arXiv Collector
  -> RSS Collector
  -> Normalize Data
  -> Remove Duplicates
  -> Calculate Scores
  -> Upsert Results
  -> Success
```

MVP note:

- GitHub and Hugging Face are active first.
- arXiv and RSS are designed extension points and may be disabled in configuration.

## Daily Digest Workflow

Default time:

- 08:05 local time.

Flow:

```text
Scheduler triggers Digest Job
  -> Load Top Ranked Items
  -> Group By Category
  -> Generate Markdown Digest
  -> Store Digest
  -> Send Telegram
  -> Send Email
  -> Store Delivery Logs
  -> Success
```

Categories:

- Repositories
- Models
- Papers
- News

MVP note:

- Telegram is active first.
- Email is part of the notification design but may be disabled until the email phase.
- Papers and news sections should be omitted or left empty when arXiv and RSS are disabled.

## Telegram Message Template

Telegram delivery should send multiple messages: one overview message and one message per section.

Overview:

```text
AI TECH RADAR

Date: {date}

Generated Automatically
```

Top GitHub Repositories:

```text
Top GitHub Repositories

1. {repo_name}
   Stars: {stars}

{description}

{url}
```

Top AI Models:

```text
Top AI Models

1. {model_name}

Downloads: {downloads}

Task: {task}

{url}
```

Top Papers:

```text
Top Papers

1. {paper_title}

Authors: {authors}

Published: {date}

{url}
```

Footer:

```text
Generated Automatically
```

## Email Template

Email is a future notification channel, but the template is defined now so the notification interface can support it later.

Subject:

```text
AI Tech Radar Daily Digest
```

Body:

```text
Daily Technology Intelligence Report

1. GitHub Repositories
2. AI Models
3. Research Papers
4. Industry News

Generated Automatically
```

## Error Handling

### GitHub API Failure

Action:

- Retry 3 times.

Backoff:

- 5 seconds.
- 10 seconds.
- 20 seconds.

After final failure:

- Store the error.
- Continue with other enabled collectors.
- Mark GitHub refresh as failed for refresh success metrics.

### Telegram Failure

Action:

- Retry 3 times.
- Store delivery log.

After final failure:

- Mark delivery status as `failed`.
- Preserve digest so it can be resent manually.

### Database Failure

Action:

- Abort the current workflow.
- Send alert if alerting is configured.

Reason:

- The pipeline depends on persistence for normalized items, scores, digests, and delivery logs.

## Acceptance Criteria

The system must:

- Refresh successfully more than 95% of the time.
- Generate digest in less than 5 minutes.
- Deliver notifications in less than 1 minute.
- Store historical data for 12 months.
- Support at least 10,000 items per day ingestion.
- Run entirely using Docker Compose.
