# Telegram Auto Uploader Bot

This repository contains a Telegram bot that automatically sends a predefined message to a specified channel every day at scheduled times.

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

- Schedules messages at one or more times per day (cron-style scheduling).
- Sends messages to a specified Telegram channel.
- Configurable via environment variables.

## Environment Variables

| Variable             | Description                                                 |
|----------------------|-------------------------------------------------------------|
| TELEGRAM_BOT_TOKEN   | Your Telegram bot token (from BotFather)                    |
| TELEGRAM_CHAT_ID     | Chat ID or channel username (e.g. `@mychannel`)             |
| MESSAGE_TEXT         | The text message to send                                    |
| SCHEDULE_TIMES       | Comma-separated times in `HH:MM` 24-hour format (e.g. `09:00,18:30`) |

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
export TELEGRAM_CHAT_ID="@yourchannel"
export MESSAGE_TEXT="Hello, world!"
export SCHEDULE_TIMES="09:00,18:30"
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
  -e TELEGRAM_CHAT_ID="@yourchannel" \
  -e MESSAGE_TEXT="Hello, world!" \
  -e SCHEDULE_TIMES="09:00,18:30" \
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

3. Set the environment variables in the Railway dashboard to match the ones above.

## License

This project is released under the MIT License.