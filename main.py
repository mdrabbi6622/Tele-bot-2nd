import logging
import requests
import pymongo
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO)

# টোকেন এবং অন্যান্য তথ্য
TOKEN = 'BOT_TOKEN'
MONGO_URI = 'MONGO_URI'
WEBSITE_URL = 'https://bdshortner.com'
mongo_client = pymongo.MongoClient(MONGO_URI)
mongo_db = mongo_client['bdshortner']

# ইউজারকে ওয়েলকাম করবে
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Welcome to BD Shortner Bot! Visit: {WEBSITE_URL}')

# ইউজারের API কীগুলি অ্যাড করার জন্য
def add_api(update, context):
    user_id = update.effective_user.id
    api_key = context.args[0]  # ইউজার API কী দিবে
    mongo_db.users.update_one({'user_id': user_id}, {'$set': {'api_key': api_key}}, upsert=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text='API key added successfully!')

# চ্যানেল লিংক বা আইডি অ্যাড করার জন্য
def add_channel(update, context):
    user_id = update.effective_user.id
    channel_id = context.args[0]  # ইউজার চ্যানেল লিংক/আইডি দিবে
    mongo_db.users.update_one({'user_id': user_id}, {'$set': {'channel_id': channel_id}}, upsert=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Channel added successfully!')

# চ্যানেল লিংক বা আইডি রিমুভ করার জন্য
def remove_channel(update, context):
    user_id = update.effective_user.id
    mongo_db.users.update_one({'user_id': user_id}, {'$unset': {'channel_id': 1}})
    context.bot.send_message(chat_id=update.effective_chat.id, text='Channel removed successfully!')

# ফুটার টেক্সট অ্যাড করার জন্য
def add_footer(update, context):
    user_id = update.effective_user.id
    footer_text = " ".join(context.args)
    mongo_db.users.update_one({'user_id': user_id}, {'$set': {'footer_text': footer_text}}, upsert=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Footer added successfully!')

# ফুটার টেক্সট রিমুভ করার জন্য
def remove_footer(update, context):
    user_id = update.effective_user.id
    mongo_db.users.update_one({'user_id': user_id}, {'$unset': {'footer_text': 1}})
    context.bot.send_message(chat_id=update.effective_chat.id, text='Footer removed successfully!')

# টেক্সট আউটপুট ডিসেবল করার জন্য
def disable_text(update, context):
    user_id = update.effective_user.id
    mongo_db.users.update_one({'user_id': user_id}, {'$set': {'text_output': False}}, upsert=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Text output disabled!')

# টেক্সট আউটপুট এনাবল করার জন্য
def enable_text(update, context):
    user_id = update.effective_user.id
    mongo_db.users.update_one({'user_id': user_id}, {'$set': {'text_output': True}}, upsert=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Text output enabled!')

# পিকচার আউটপুট এনাবল করার জন্য
def enable_picture(update, context):
    user_id = update.effective_user.id
    mongo_db.users.update_one({'user_id': user_id}, {'$set': {'picture_output': True}}, upsert=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Picture output enabled!')

# পিকচার আউটপুট ডিসেবল করার জন্য
def disable_picture(update, context):
    user_id = update.effective_user.id
    mongo_db.users.update_one({'user_id': user_id}, {'$set': {'picture_output': False}}, upsert=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Picture output disabled!')

# ভাষা পরিবর্তন করার জন্য
def change_language(update, context):
    user_id = update.effective_user.id
    language_code = context.args[0]  # ভাষার কোড (উদাহরণস্বরূপ: en, bn)
    mongo_db.users.update_one({'user_id': user_id}, {'$set': {'language_code': language_code}}, upsert=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Language changed successfully!')

# ইউজারের আইডি দেখার জন্য
def getmyid(update, context):
    user_id = update.effective_user.id
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Your ID is {user_id}')

# সহায়তার জন্য
def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Contact support at support@bdshortner.com')

# শর্ট লিংক করা এবং টেলিগ্রাম লিংক রিপ্লেসমেন্ট
def process_message(update, context):
    user_id = update.effective_user.id
    user_data = mongo_db.users.find_one({'user_id': user_id})
    
    if not user_data or 'api_key' not in user_data:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Please add your API key using /add_api command.')
        return
    
    api_key = user_data['api_key']
    footer = user_data.get('footer_text', '')
    text_output_enabled = user_data.get('text_output', True)
    picture_output_enabled = user_data.get('picture_output', True)

    # চেক করা হচ্ছে ফরোয়ার্ড করা মেসেজের মধ্যে কোনো লিংক আছে কিনা
    for entity in update.message.entities or []:
        if entity.type == 'url' and "t.me/" in update.message.text:
            url = update.message.text[entity.offset: entity.offset + entity.length]
            
            # শর্ট লিংক করার জন্য API কল
            response = requests.get(f'https://bdshortner.com/api?api={api_key}&url={url}')
            shortened_url = response.json().get('short_url', url)  # যদি শর্ট লিংক না হয় তাহলে মূল লিংক রিটার্ন করবে

            # নতুন মেসেজে টেলিগ্রাম লিংক রিপ্লেস করা হবে
            new_message = update.message.text.replace(url, shortened_url)
            
            # চ্যানেল লিংক চেক করা এবং রিপ্লেস করা
            if 'channel_id' in user_data:
                new_message = new_message.replace("t.me/", f"t.me/{user_data['channel_id']}")

            # টেক্সট আউটপুট যদি ডিসেবল করা থাকে
            if not text_output_enabled:
                new_message = shortened_url  # শুধু শর্ট লিংক দেখাবে

            # ফুটার যুক্ত করা হচ্ছে
            if footer:
                new_message += f"\n\n{footer}"

            # ছবি বা ভিডিও আউটপুট ডিসেবল করা থাকলে ছবি বা ভিডিও বাদ দিয়ে রিপ্লাই করা হবে
            if not picture_output_enabled:
                update.message.delete()  # মূল মেসেজ ডিলিট
                context.bot.send_message(chat_id=update.effective_chat.id, text=new_message)
            else:
                # মূল পোস্টে ছবি বা ভিডিও সহ রিপ্লেস করা লিংক দিয়ে পোস্ট
                context.bot.send_message(chat_id=update.effective_chat.id, text=new_message)

# মেইন ফাংশন
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # কমান্ড হ্যান্ডলার
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('add_api', add_api))
    dp.add_handler(CommandHandler('add_channel', add_channel))
    dp.add_handler(CommandHandler('remove_channel', remove_channel))
    dp.add_handler(CommandHandler('add_footer', add_footer))
    dp.add_handler(CommandHandler('remove_footer', remove_footer))
    dp.add_handler(CommandHandler('disable_text', disable_text))
    dp.add_handler(CommandHandler('enable_text', enable_text))
    dp.add_handler(CommandHandler('enable_picture', enable_picture))
    dp.add_handler(CommandHandler('disable_picture', disable_picture))
    dp.add_handler(CommandHandler('change_language', change_language))
    dp.add_handler(CommandHandler('getmyid', getmyid))
    dp.add_handler(CommandHandler('help', help))

    # মেসেজ হ্যান্ডলার
    dp.add_handler(MessageHandler(Filters.text & Filters.forwarded, process_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
