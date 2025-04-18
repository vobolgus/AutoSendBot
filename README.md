# Telegram Auto Sender Bot

This repository contains an interactive Telegram bot that allows users to schedule messages to be sent automatically to groups where the bot is a member.

## Repository Structure

```
.
├── Dockerfile
├── .dockerignore
├── railway.toml
├── requirements.txt
├── src
│   └── bot.py
└── README.md
```

## Features

- Interactive bot interface with button menus
- List groups where the bot is a member
- View, add, and delete scheduled messages for each group
- Schedule messages at multiple times per day (cron-style scheduling)
- User management of their own schedules
- Persistent storage of schedules

## Bot Commands

| Command   | Description                                     |
|------------|------------------------------------------------|
| /start     | Start the bot and get an introduction          |
| /groups    | List groups where the bot is a member          |
| /cancel    | Cancel the current operation                   |

## Environment Variables

| Variable           | Description                                |
|--------------------|--------------------------------------------|
| TELEGRAM_BOT_TOKEN | Your Telegram bot token (from BotFather)   |

## How to Use

1. Add your bot to a Telegram group
2. Start a private chat with the bot
3. Use the `/groups` command to see groups where the bot is a member
4. Select a group to manage schedules
5. Follow the interactive prompts to view, add, or delete scheduled messages

## Running Locally

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
```

4. Run the bot:
```bash
python src/bot.py
```

## Docker

1. Build the image:
```bash
docker build -t telegram-bot .
```

2. Run the container:
```bash
docker run -d \
  -e TELEGRAM_BOT_TOKEN="your_token" \
  telegram-bot
```

## Railway Deployment

This project includes a `railway.toml` file for Railway integration.

1. Install the Railway CLI:
```bash
curl -sSL https://railway.app/install.sh | sh
```

2. Connect and deploy:
```bash
railway up
```

3. Set the environment variables in the Railway dashboard.

## License

This project is released under the MIT License.