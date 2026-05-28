# DS_chat_bot

MVP technical skeleton for the Telegram bot of the “Давай сконнектимся” community.

The project currently provides only the foundation for future MVP work:

- aiogram 3 Telegram bot in long polling mode;
- environment-based configuration;
- Docker Compose local startup with PostgreSQL prepared;
- `/start`, `/connect`, and `/health` commands;
- placeholder `/connect` menu actions that do not implement future features yet.

Profiles, moderation, partner discovery, Random Coffee logic, admin flows, database models, migrations, webhooks, web admin panels, and payment features are intentionally not implemented in this skeleton.

## Requirements

- Docker
- Docker Compose
- A Telegram bot token from BotFather

## Local startup with Docker Compose

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Fill the required values in `.env`:

   ```dotenv
   BOT_TOKEN=<telegram bot token from BotFather>
   ADMIN_TELEGRAM_IDS=<comma-separated admin Telegram IDs, for example 123456789,987654321>
   MAIN_CHAT_ID=<main Telegram chat ID>
   ```

   Keep the remaining defaults unless you need to customize local PostgreSQL or logging:

   ```dotenv
   TIMEZONE=Europe/Moscow
   DATABASE_URL=postgresql+asyncpg://ds_bot:ds_bot_password@postgres:5432/ds_bot
   POSTGRES_DB=ds_bot
   POSTGRES_USER=ds_bot
   POSTGRES_PASSWORD=ds_bot_password
   LOG_LEVEL=INFO
   ```

3. Build and start the services:

   ```bash
   docker compose up --build
   ```

4. Confirm the bot is running:

   - the bot container logs should include `bot_running mode=long_polling`;
   - send `/start` to the bot in Telegram;
   - send `/connect` to open the placeholder menu;
   - send `/health` to receive a lightweight running check.

## Commands

- `/start` — shows the introductory community bot text.
- `/connect` — shows the MVP placeholder menu.
- `/health` — replies that the bot is running.

All `/connect` menu buttons currently reply with:

```text
Этот раздел появится в следующей версии MVP.
```

## Configuration

The application fails fast on startup if any required environment variables are missing or invalid:

- `BOT_TOKEN`
- `ADMIN_TELEGRAM_IDS`
- `MAIN_CHAT_ID`
- `DATABASE_URL`

`ADMIN_TELEGRAM_IDS` must be a comma-separated list of integer Telegram IDs. `MAIN_CHAT_ID` must be an integer.

## Development

Install dependencies locally if you want to run tests outside Docker:

```bash
python -m pip install -e '.[dev]'
pytest
```
