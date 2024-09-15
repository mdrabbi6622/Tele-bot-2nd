import logging
import requests
import pymongo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# Logging setup
logging.basicConfig(level=logging.INFO)

# Token and other info
TOKEN = 'BOT_TOKEN'
MONGO_URI = 'MONGO_URI'
WEBSITE_URL = 'https://bdshortner.com'
mongo_client = pymongo.MongoClient(MONGO_URI)
mongo_db = mongo_client['bdshortner']

# Welcome message
async def start(update, context):
    await update.message.reply_text(f'Welcome to BD Shortner Bot! Visit: {WEBSITE_URL}')

# Add API key
async def add_api(update, context):
    user_id = update.effective_user.id
    api_key = context.args[0]  # User gives API key
    mongo_db.users.update_one({'user_id': user_id}, {'$set': {'api_key': api_key}}, upsert=True)
    await update.message.reply_text('API key added successfully!')

# Add channel link or ID
async def add_channel(update, context):
    user_id = update.effective_user.id
    channel_id = context.args[0]  # User gives channel link/ID
    mongo_db.users.update_one({'user_id': user_id}, {'$set': {'channel_id': channel_id}}, upsert=True)
    await update.message.reply_text('Channel added successfully!')

# Remove channel link or ID
async def remove_channel(update, context):
    user_id = update.effective_user.id
    mongo_db.users.update_one({'user_id': user_id}, {'$unset': {'channel_id': 1}})
    await update.message.reply_text('Channel removed successfully!')

# Add footer text
async def add_footer(update, context):
    user_id = update.effective_user.id
    footer_text = " ".join(context.args)
    mongo_db.users.update_one({'user_id': user_id}, {'$set': {'footer_text': footer_text}}, upsert=True)
    await update.message.reply_text('Footer added successfully!')

# Remove footer text
async def remove_footer(update, context):
    user_id = update.effective_user.id
    mongo_db.users.update_one({'user_id': user_id}, {'$unset': {'footer_text': 1}})
    await update.message.reply_text('Footer removed successfully!')

# Disable text output
async def disable_text(update, context):
    user_id = update.effective_user.id
    mongo_db.users.update_one({'user_id': user_id}, {'$set': {'text_output': False}}, upsert=True)
    await update.message.reply_text('Text output disabled!')

# Enable text output
async def enable_text(update, context):
    user_id = update.effective_user.id
    mongo_db.users.update_one({'user_id': user_id}, {'$set': {'text_output': True}}, upsert=True)
    await update.message.reply_text('Text output enabled!')

# Enable picture output
async def enable_picture(update, context):
    user_id = update.effective_user.id
    mongo_db.users.update_one({'user_id': user_id}, {'$set': {'picture_output': True}}, upsert=True)
    await update.message.reply_text('Picture output enabled!')

# Disable picture output
async def disable_picture(update, context):
    user_id = update.effective_user.id
    mongo_db.users.update_one({'user_id': user_id}, {'$set': {'picture_output': False}}, upsert=True)
    await update.message.reply_text('Picture output disabled!')

# Change language
async def change_language(update, context):
    user_id = update.effective_user.id
    language_code = context.args[0]  # Language code (e.g., en, bn)
    mongo_db.users.update_one({'user_id': user_id}, {'$set': {'language_code': language_code}}, upsert=True)
    await update.message.reply_text('Language changed successfully!')

# Get user's ID
async def getmyid(update, context):
    user_id = update.effective_user.id
    await update.message.reply_text(f'Your ID is {user_id}')

# Help
async def help(update, context):
    await update.message.reply_text('Contact support at support@bdshortner.com')

# Short link processing and Telegram link replacement
async def process_message(update, context):
    user_id = update.effective_user.id
    user_data = mongo_db.users.find_one({'user_id': user_id})

    if not user_data or 'api_key' not in user_data:
        await update.message.reply_text('Please add your API key using /add_api command.')
        return

    api_key = user_data['api_key']
    footer = user_data.get('footer_text', '')
    text_output_enabled = user_data.get('text_output', True)
    picture_output_enabled = user_data.get('picture_output', True)

    for entity in update.message.entities or []:
        if entity.type == 'url' and "t.me/" in update.message.text:
            url = update.message.text[entity.offset: entity.offset + entity.length]

            # Shorten URL
            response = requests.get(f'https://bdshortner.com/api?api={api_key}&url={url}')
            shortened_url = response.json().get('short_url', url)

            # Replace link in the new message
            new_message = update.message.text.replace(url, shortened_url)

            # Replace Telegram channel links if any
            if 'channel_id' in user_data:
                new_message = new_message.replace("t.me/", f"t.me/{user_data['channel_id']}")

            if not text_output_enabled:
                new_message = shortened_url  # Show only the shortened link

            # Add footer
            if footer:
                new_message += f"\n\n{footer}"

            # Handle picture or video output
            if not picture_output_enabled:
                await update.message.delete()  # Delete the original message
                await update.message.reply_text(new_message)
            else:
                await update.message.reply_text(new_message)

# Main function
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('add_api', add_api))
    app.add_handler(CommandHandler('add_channel', add_channel))
    app.add_handler(CommandHandler('remove_channel', remove_channel))
    app.add_handler(CommandHandler('add_footer', add_footer))
    app.add_handler(CommandHandler('remove_footer', remove_footer))
    app.add_handler(CommandHandler('disable_text', disable_text))
    app.add_handler(CommandHandler('enable_text', enable_text))
    app.add_handler(CommandHandler('enable_picture', enable_picture))
    app.add_handler(CommandHandler('disable_picture', disable_picture))
    app.add_handler(CommandHandler('change_language', change_language))
    app.add_handler(CommandHandler('getmyid', getmyid))
    app.add_handler(CommandHandler('help', help))

    # Message handler
    app.add_handler(MessageHandler(filters.TEXT & filters.FORWARDED, process_message))

    await app.start()
    await app.updater.stop()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
