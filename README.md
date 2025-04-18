# Telegram Auto Sender Bot

Telegram Auto Sender Bot is an interactive Telegram bot that allows users to schedule messages to be sent automatically to their Telegram groups. It uses a PostgreSQL database to track group membership and a JSON file to persist user-defined schedules.

## Repository Structure

```
.
├── Dockerfile
├── .dockerignore
├── .gitignore
├── railway.toml
├── requirements.txt
├── src
│   ├── bot.py        # Main bot implementation
│   └── db.py         # Database module for tracking chats
├── example_bot_v20.py  # Example bot setup (python-telegram-bot v20)
├── test_indent.py      # Indentation test example
├── LICENSE
└── README.md
```

## Features

- Interactive button-based interface using python-telegram-bot
- Track group membership and ownership in PostgreSQL
- Schedule messages at one or multiple cron-style times per day
- Persist schedules in a local JSON file (`user_data.json`)
- Asynchronous scheduling powered by APScheduler
- Easy deployment via Docker or Railway

## Bot Commands

| Command   | Description                                     |
|------------|------------------------------------------------|
| /start     | Start the bot and get an introduction          |
| /groups    | List groups where the bot is a member          |
| /cancel    | Cancel the current operation                   |

## Environment Variables

| Variable           | Description                                                       |
|--------------------|-------------------------------------------------------------------|
| TELEGRAM_BOT_TOKEN | Your Telegram Bot API token (from BotFather)                     |
| DATABASE_URL       | PostgreSQL connection URL (e.g., `postgres://user:pass@host/db`)  |

## How to Use

1. Add your bot to a Telegram group
2. Start a private chat with the bot
3. Use the `/groups` command to see groups where the bot is a member
4. Select a group to manage schedules
5. Follow the interactive prompts to view, add, or delete scheduled messages

## Installation

### Running Locally

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd <repo-directory>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_token"
   export DATABASE_URL="postgres://user:password@host:port/database"
   ```

4. Run the bot:
   ```bash
   python src/bot.py
   ```

### Docker

1. Build the Docker image:
   ```bash
   docker build -t telegram-auto-sender .
   ```

2. Run the container:
   ```bash
   docker run -d \
     -e TELEGRAM_BOT_TOKEN="your_token" \
     -e DATABASE_URL="postgres://user:password@host:port/database" \
     telegram-auto-sender
   ```

### Railway Deployment

Railway is configured via `railway.toml`. Deploy with the Railway CLI:

```bash
railway up
```

Ensure `TELEGRAM_BOT_TOKEN` and `DATABASE_URL` are set in the Railway dashboard before deployment.

## License

This project is released under the MIT License.