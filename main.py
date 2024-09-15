from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
import pymongo

# MongoDB connection setup
client = pymongo.MongoClient("MONGO_URL")
db = client["url_shortener"]
users_collection = db["users"]

# Shortening the URL using the website's API
def shorten_url(api_key, long_url):
    api_url = f"https://bdshortner.com/api?api={api_key}&url={long_url}"
    response = requests.get(api_url)
    return response.json().get("shortenedUrl", long_url)

# /start command handler
def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    update.message.reply_text(f"Welcome {user.first_name}!\nUse /add_api to add your API key.\nWebsite: https://bdshortner.com")

# /add_api command handler
def add_api(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    api_key = context.args[0] if context.args else None

    if api_key:
        users_collection.update_one({"_id": user_id}, {"$set": {"api_key": api_key}}, upsert=True)
        update.message.reply_text("Your API key has been added successfully!")
    else:
        update.message.reply_text("Please provide an API key like this: /add_api YOUR_API_KEY")

# /add_channel command handler
def add_channel(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    channel_link = context.args[0] if context.args else None

    if channel_link:
        users_collection.update_one({"_id": user_id}, {"$set": {"channel": channel_link}}, upsert=True)
        update.message.reply_text(f"Channel {channel_link} added.")
    else:
        update.message.reply_text("Please provide a channel link like this: /add_channel @channel_username or https://t.me/channel_link")

# /remove_channel command handler
def remove_channel(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    users_collection.update_one({"_id": user_id}, {"$unset": {"channel": ""}})
    update.message.reply_text("Channel removed successfully!")

# /add_footer command handler
def add_footer(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    footer = ' '.join(context.args) if context.args else None

    if footer:
        users_collection.update_one({"_id": user_id}, {"$set": {"footer": footer}}, upsert=True)
        update.message.reply_text(f"Footer added: {footer}")
    else:
        update.message.reply_text("Please provide a footer text like this: /add_footer Your custom footer")

# /remove_footer command handler
def remove_footer(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    users_collection.update_one({"_id": user_id}, {"$unset": {"footer": ""}})
    update.message.reply_text("Footer removed successfully!")

# /disable_text and /enable_text command handlers
def disable_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    users_collection.update_one({"_id": user_id}, {"$set": {"text_enabled": False}}, upsert=True)
    update.message.reply_text("Text disabled for forwarded posts.")

def enable_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    users_collection.update_one({"_id": user_id}, {"$set": {"text_enabled": True}}, upsert=True)
    update.message.reply_text("Text enabled for forwarded posts.")

# /enable_picture and /disable_picture command handlers
def enable_picture(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    users_collection.update_one({"_id": user_id}, {"$set": {"picture_enabled": True}}, upsert=True)
    update.message.reply_text("Pictures and videos enabled for forwarded posts.")

def disable_picture(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    users_collection.update_one({"_id": user_id}, {"$set": {"picture_enabled": False}}, upsert=True)
    update.message.reply_text("Pictures and videos disabled for forwarded posts.")

# /change_language command handler
def change_language(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    language = context.args[0] if context.args else None

    if language:
        users_collection.update_one({"_id": user_id}, {"$set": {"language": language}}, upsert=True)
        update.message.reply_text(f"Language changed to {language}.")
    else:
        update.message.reply_text("Please provide a language like this: /change_language en or /change_language es")

# /getmyid command handler
def get_my_id(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    update.message.reply_text(f"Your Telegram ID is: {user_id}")

# /help command handler
def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("You can contact the support team at support@bdshortner.com")

# Message handler to shorten links and manage output formatting
def handle_forwarded_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data = users_collection.find_one({"_id": user_id})

    if user_data and "api_key" in user_data:
        # Find any URLs in the forwarded message
        message_text = update.message.text or ""
        urls = [word for word in message_text.split() if word.startswith("http")]

        if urls:
            # Shorten each URL and replace in the message
            shortened_urls = [shorten_url(user_data["api_key"], url) for url in urls]
            new_message = message_text

            for long_url, short_url in zip(urls, shortened_urls):
                new_message = new_message.replace(long_url, short_url)

            # Handle custom footer, channel, and other settings
            if user_data.get("footer"):
                new_message += f"\n{user_data['footer']}"
            if user_data.get("channel"):
                new_message += f"\nChannel: {user_data['channel']}"

            if not user_data.get("text_enabled", True):
                new_message = ' '.join(shortened_urls)  # Only show shortened links

            # Check if media is enabled/disabled
            if update.message.photo and not user_data.get("picture_enabled", True):
                update.message.reply_text("Pictures and videos are disabled for forwarded posts.")
            else:
                update.message.reply_text(new_message)
        else:
            update.message.reply_text("No URLs found to shorten.")
    else:
        update.message.reply_text("You need to set your API key using /add_api.")

# Main function to start the bot
def main():
    updater = Updater("BOT_TOKEN", use_context=True)
    dispatcher = updater.dispatcher

    # Registering the command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("add_api", add_api))
    dispatcher.add_handler(CommandHandler("add_channel", add_channel))
    dispatcher.add_handler(CommandHandler("remove_channel", remove_channel))
    dispatcher.add_handler(CommandHandler("add_footer", add_footer))
    dispatcher.add_handler(CommandHandler("remove_footer", remove_footer))
    dispatcher.add_handler(CommandHandler("disable_text", disable_text))
    dispatcher.add_handler(CommandHandler("enable_text", enable_text))
    dispatcher.add_handler(CommandHandler("enable_picture", enable_picture))
    dispatcher.add_handler(CommandHandler("disable_picture", disable_picture))
    dispatcher.add_handler(CommandHandler("change_language", change_language))
    dispatcher.add_handler(CommandHandler("getmyid", get_my_id))
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # Handler for forwarded messages
    dispatcher.add_handler(MessageHandler(Filters.forwarded, handle_forwarded_message))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
