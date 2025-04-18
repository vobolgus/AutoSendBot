import os
import logging
import json
from typing import Dict, List, Tuple, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ChatMemberHandler,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import init_db, add_chat, remove_chat, get_chats, get_chat_owner, get_chats_by_owner


# States for conversation handler
CHOOSING_GROUP, CHOOSING_ACTION, SET_MESSAGE, SET_TIME = range(4)

# Data structure to store schedules
# Format: {user_id: {chat_id: [{"message": "text", "times": ["HH:MM", ...]}]}}
USER_DATA_FILE = "user_data.json"


def load_user_data() -> Dict:
    """Load user data from file or return empty dict if file doesn't exist"""
    try:
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_user_data(data: Dict) -> None:
    """Save user data to file"""
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


async def send_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message to a specific chat"""
    job = context.job
    chat_id, message_text = job.data

    try:
        await context.bot.send_message(chat_id=chat_id, text=message_text)
        logging.info(f"Message sent successfully to {chat_id}: {message_text}")
    except Exception as e:
        logging.error(f"Error sending message to {chat_id}: {e}")


def schedule_all_messages(scheduler: BackgroundScheduler, app: Application) -> None:
    """Schedule all messages for all users from the saved data"""
    user_data = load_user_data()

    # Clear existing jobs
    scheduler.remove_all_jobs()

    for user_id, chats in user_data.items():
        for chat_id, schedules in chats.items():
            for schedule in schedules:
                message = schedule.get("message", "")
                for time_str in schedule.get("times", []):
                    try:
                        hour_str, minute_str = time_str.split(":")
                        hour, minute = int(hour_str), int(minute_str)

                        scheduler.add_job(
                            send_scheduled_message,
                            "cron",
                            hour=hour,
                            minute=minute,
                            args=[app, chat_id, message],
                        )
                        logging.info(
                            f"Scheduled message for chat {chat_id} at {time_str}"
                        )
                    except ValueError:
                        logging.error(
                            f"Invalid time format '{time_str}' for chat {chat_id}"
                        )


async def send_scheduled_message(
    app: Application, chat_id: str, message_text: str
) -> None:
    """Send a scheduled message through the application"""
    try:
        await app.bot.send_message(chat_id=chat_id, text=message_text)
        logging.info(
            f"Scheduled message sent successfully to {chat_id}: {message_text}"
        )
    except Exception as e:
        logging.error(f"Error sending scheduled message to {chat_id}: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "Welcome to AutoSendBot! I can help you schedule messages to groups.\n"
        "Use /groups to see your groups and manage schedules."
    )


async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """List groups where the bot is a member"""
    # Get chats (groups) that this user added the bot to
    user_id_int = update.effective_user.id
    try:
        bot_chats = get_chats_by_owner(user_id_int)
    except Exception as e:
        logging.error(f"Error fetching groups for user {user_id_int}: {e}")
        bot_chats = []

    if not bot_chats:
        await update.message.reply_text(
            "You don't manage any groups yet. Add me to a group (you must be the one to add me) and I'll remember!"
        )
        return ConversationHandler.END

    # Create inline keyboard with groups
    keyboard = []
    for chat_id, title in bot_chats:
        keyboard.append([InlineKeyboardButton(title, callback_data=f"group_{chat_id}")])

    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Select a group to manage schedules:", reply_markup=reply_markup
    )

    return CHOOSING_GROUP


async def group_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle group selection"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("Operation cancelled.")
        return ConversationHandler.END

    # Extract chat_id from callback data and save
    chat_id_str = query.data.split("_", 1)[1]
    context.user_data["selected_chat_id"] = chat_id_str
    # expose chat_id variable for use below
    chat_id = chat_id_str

    # Retrieve chat title from database, fallback to ID if missing
    chat_title = chat_id_str
    try:
        for cid, title in get_chats():
            if cid == int(chat_id_str):
                chat_title = title or chat_title
                break
    except Exception as e:
        logging.error(f"Error fetching chat title from DB for {chat_id_str}: {e}")
    context.user_data["selected_chat_title"] = chat_title

    # Show actions for the selected group
    keyboard = [
        [InlineKeyboardButton("View schedules", callback_data="view")],
        [InlineKeyboardButton("Add schedule", callback_data="add")],
        [InlineKeyboardButton("Delete schedule", callback_data="delete")],
        [InlineKeyboardButton("Back to groups", callback_data="back")],
        [InlineKeyboardButton("Cancel", callback_data="cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    chat_title = context.user_data.get("selected_chat_title", chat_id)
    await query.edit_message_text(
        f"Managing group: {chat_title}", reply_markup=reply_markup
    )

    return CHOOSING_ACTION


async def action_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle action selection"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("Operation cancelled.")
        return ConversationHandler.END

    if query.data == "back":
        return await list_groups(update, context)

    chat_id = context.user_data.get("selected_chat_id")
    chat_title = context.user_data.get("selected_chat_title", chat_id)
    # Current user identifiers
    current_user_id_int = update.effective_user.id
    user_id = str(current_user_id_int)

    # Load or initialize schedule data for this user and chat
    user_data = load_user_data()
    if user_id not in user_data:
        user_data[user_id] = {}
    if chat_id not in user_data[user_id]:
        user_data[user_id][chat_id] = []

    # Permission check: only the chat owner (who added the bot) can add/delete schedules
    try:
        chat_owner = get_chat_owner(int(chat_id))
    except Exception as e:
        logging.error(f"Error retrieving owner for chat {chat_id}: {e}")
        chat_owner = None
    # If no owner recorded, assign current user as owner
    if chat_owner is None:
        try:
            add_chat(int(chat_id), chat_title or '', current_user_id_int)
            chat_owner = current_user_id_int
        except Exception as e:
            logging.error(f"Error setting owner for chat {chat_id}: {e}")
    # Restrict add/delete actions to owner only
    if query.data in ("add", "delete") or query.data.startswith("delete_"):
        if chat_owner != current_user_id_int:
            await query.edit_message_text(
                "⚠️ Only the user who added the bot can manage schedules for this group."
            )
            return ConversationHandler.END

    if query.data == "view":
        # Show existing schedules
        schedules = user_data[user_id][chat_id]
        if not schedules:
            await query.edit_message_text(
                f"No schedules for {chat_title}.\n" f"Use /groups to go back."
            )
        else:
            schedule_text = f"Schedules for {chat_title}:\n\n"
            for i, schedule in enumerate(schedules):
                times = ", ".join(schedule.get("times", []))
                schedule_text += (
                    f"{i+1}. Message: {schedule.get('message')}\n"
                    f"   Times: {times}\n\n"
                )

            await query.edit_message_text(schedule_text + "Use /groups to go back.")
        return ConversationHandler.END

    elif query.data == "add":
        # Start process to add a new schedule
        context.user_data["action"] = "add"
        await query.edit_message_text(
            f"Adding new schedule for {chat_title}.\n"
            f"Send me the message text you want to schedule:"
        )
        return SET_MESSAGE

    elif query.data == "delete":
        # Show schedules to delete
        schedules = user_data[user_id][chat_id]
        if not schedules:
            await query.edit_message_text(
                f"No schedules to delete for {chat_title}.\n" f"Use /groups to go back."
            )
            return ConversationHandler.END

        keyboard = []
        for i, schedule in enumerate(schedules):
            times = ", ".join(schedule.get("times", []))
            label = f"{i+1}. {schedule.get('message')} at {times}"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"delete_{i}")])

        keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"Select a schedule to delete from {chat_title}:", reply_markup=reply_markup
        )
        return CHOOSING_ACTION

    elif query.data.startswith("delete_"):
        # Delete the selected schedule
        index = int(query.data.split("_")[1])
        schedules = user_data[user_id][chat_id]
        if 0 <= index < len(schedules):
            deleted = schedules.pop(index)
            save_user_data(user_data)

            # Reschedule all jobs
            app = context.application
            schedule_all_messages(app.bot_data["scheduler"], app)

            times = ", ".join(deleted.get("times", []))
            await query.edit_message_text(
                f"Schedule deleted: {deleted.get('message')} at {times}.\n"
                f"Use /groups to go back."
            )
        else:
            await query.edit_message_text(
                "Invalid schedule index.\n" "Use /groups to go back."
            )
        return ConversationHandler.END

    return ConversationHandler.END


async def message_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the entered message for scheduling"""
    context.user_data["message"] = update.message.text

    await update.message.reply_text(
        "Now send me the time(s) to schedule this message.\n"
        "Format: HH:MM (24-hour format)\n"
        "For multiple times, separate with commas (e.g., 09:00, 15:30)"
    )

    return SET_TIME


async def time_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the entered time(s) for scheduling"""
    times_text = update.message.text
    times = [t.strip() for t in times_text.split(",") if t.strip()]

    # Validate times
    valid_times = []
    invalid_times = []
    for t in times:
        try:
            hour_str, minute_str = t.split(":")
            hour, minute = int(hour_str), int(minute_str)
            if 0 <= hour < 24 and 0 <= minute < 60:
                valid_times.append(f"{hour:02d}:{minute:02d}")
            else:
                invalid_times.append(t)
        except ValueError:
            invalid_times.append(t)

    if invalid_times:
        await update.message.reply_text(
            f"Invalid time format(s): {', '.join(invalid_times)}.\n"
            f"Please try again with the format HH:MM (24-hour format)."
        )
        return SET_TIME

    if not valid_times:
        await update.message.reply_text("No valid times provided. Please try again.")
        return SET_TIME

    # Save the schedule
    user_id = str(update.effective_user.id)
    chat_id = context.user_data.get("selected_chat_id")
    message = context.user_data.get("message", "")

    user_data = load_user_data()
    if user_id not in user_data:
        user_data[user_id] = {}
    if chat_id not in user_data[user_id]:
        user_data[user_id][chat_id] = []

    chat_title = context.user_data.get("selected_chat_title", chat_id)

    # Add the new schedule
    new_schedule = {"message": message, "times": valid_times}
    user_data[user_id][chat_id].append(new_schedule)
    save_user_data(user_data)

    # Reschedule all jobs
    app = context.application
    schedule_all_messages(app.bot_data["scheduler"], app)

    await update.message.reply_text(
        f"Schedule added for {chat_title}:\n"
        f"Message: {message}\n"
        f"Times: {', '.join(valid_times)}\n\n"
        f"Use /groups to manage more schedules."
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logging.error(f"Update {update} caused error {context.error}")

async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle bot's chat member updates to track chats."""
    result = update.my_chat_member
    chat = result.chat
    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status
    # Only track bot's own membership changes
    if result.new_chat_member.user.id != context.bot.id:
        return
    # Added to chat: record chat and owner (user who added the bot)
    if new_status in ('member', 'administrator'):
        try:
            owner_id = result.from_user.id
            add_chat(chat.id, chat.title or '', owner_id)
            logging.info(f"Added chat {chat.id} - {chat.title} by user {owner_id}")
        except Exception as e:
            logging.error(f"Error adding chat {chat.id}: {e}")
    # Removed from chat
    elif new_status in ('kicked', 'left'):
        try:
            remove_chat(chat.id)
            logging.info(f"Removed chat {chat.id}")
        except Exception as e:
            logging.error(f"Error removing chat {chat.id}: {e}")


def main() -> None:
    """Run the bot."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    # Initialize database for tracking chats
    try:
        init_db()
        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        return

    # Get the token from environment variable
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logging.error("Environment variable TELEGRAM_BOT_TOKEN must be set")
        return

    # Create the scheduler for scheduled messages (asyncio-based)
    scheduler = AsyncIOScheduler()
    # Start scheduler once the bot's asyncio loop is running
    async def start_scheduler(app: Application) -> None:
        scheduler.start()

    # Create the application with post-init hook to start the scheduler
    application = (
        Application.builder()
        .token(token)
        .post_init(start_scheduler)
        .build()
    )
    application.bot_data["scheduler"] = scheduler

    # Register handlers
    # Track bot being added/removed from chats
    application.add_handler(
        ChatMemberHandler(chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER)
    )
    application.add_handler(CommandHandler("start", start))

    # Conversation handler for managing groups and schedules
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("groups", list_groups)],
        states={
            CHOOSING_GROUP: [CallbackQueryHandler(group_selected)],
            CHOOSING_ACTION: [CallbackQueryHandler(action_selected)],
            SET_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_entered)
            ],
            SET_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, time_entered)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)

    # Register error handler
    application.add_error_handler(error_handler)

    # Load and schedule all messages
    schedule_all_messages(scheduler, application)

    # Start the Bot
    logging.info("Starting bot")

    # Run the bot until the user presses Ctrl-C
    application.run_polling(stop_signals=None)

    # Shutdown scheduler when bot is stopped
    scheduler.shutdown()

if __name__ == "__main__":
    main()
