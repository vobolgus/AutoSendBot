import os
import logging
from datetime import datetime
import requests
from apscheduler.schedulers.blocking import BlockingScheduler

def send_message(bot_token, chat_id, message_text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message_text}
    try:
        resp = requests.post(url, data=payload)
        resp.raise_for_status()
        logging.info(f"Message sent successfully at {datetime.now()}: {message_text}")
    except requests.RequestException as e:
        logging.error(f"Error sending message: {e}")

def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(levelname)s] %(message)s')
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    message_text = os.environ.get('MESSAGE_TEXT', '')
    schedule_times = os.environ.get('SCHEDULE_TIMES', '')

    if not bot_token or not chat_id or not message_text or not schedule_times:
        logging.error('Environment variables TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, MESSAGE_TEXT, and SCHEDULE_TIMES must be set')
        return

    scheduler = BlockingScheduler()
    times = [t.strip() for t in schedule_times.split(',') if t.strip()]
    for t in times:
        try:
            hour_str, minute_str = t.split(':')
            hour = int(hour_str)
            minute = int(minute_str)
        except ValueError:
            logging.error(f"Invalid time format '{t}'. Expected HH:MM.")
            continue
        scheduler.add_job(
            send_message,
            'cron',
            hour=hour,
            minute=minute,
            args=[bot_token, chat_id, message_text]
        )
        logging.info(f"Scheduled message at {t} every day")

    logging.info("Starting scheduler...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler stopped")

if __name__ == '__main__':
    main()