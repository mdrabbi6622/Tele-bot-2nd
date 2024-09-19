import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
import requests
from urllib.parse import urlparse

# Adlinkfly ক্লাস
class Adlinkfly:
    def __init__(self, api_key: str, base_site: str = "bdshortner.com"):
        self.api_key = api_key
        self.base_site = base_site
        self.base_url = f"https://{self.base_site}/api"

        if not self.api_key:
            raise Exception("API key not provided")

    def __fetch(self, params: dict) -> dict:
        response = requests.get(self.base_url, params=params, verify=False)
        response.raise_for_status()
        return response.json()

    def convert(self, link: str, alias: str = "", silently_fail: bool = False) -> str:
        is_short_link = self.is_short_link(link)

        if is_short_link:
            original_url = self.resolve_short_link(link)
            if original_url:
                link = original_url

        params = {
            "api": self.api_key,
            "url": link,
            "alias": alias,
            "format": "json",
        }

        try:
            data = self.__fetch(params)

            if data["status"] == "success":
                return data["shortenedUrl"]

            if silently_fail:
                return link

            raise Exception(data["message"])

        except Exception as e:
            raise Exception(e)

    def is_short_link(self, link: str) -> bool:
        return self.base_site in urlparse(link).netloc

    def resolve_short_link(self, short_url: str) -> str:
        # প্রাপ্ত তথ্য অনুযায়ী কাস্টম লিঙ্ক রেজোলভ করুন
        resolve_url = f"https://{self.base_site}/resolve?short_url={short_url}"
        response = requests.get(resolve_url)
        result = response.json()
        return result.get('original_url', '')

# MongoDB কনফিগারেশন
MONGO_URL = 'YOUR_MONGO_URL'
client = MongoClient(MONGO_URL)
db = client['telegram_bot']
users = db['users']

# Pyrogram ক্লায়েন্ট কনফিগারেশন
API_ID = 'YOUR_API_ID'
API_HASH = 'YOUR_API_HASH'
BOT_TOKEN = 'YOUR_BOT_TOKEN'

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply_text(
        "Welcome! Use /add_api to add your API key and start shortening links. Visit https://bdshortner.com for more details."
    )

@app.on_message(filters.command("add_api"))
async def add_api(client: Client, message: Message):
    user_id = message.from_user.id
    api_key = message.text.split(None, 1)[1] if len(message.text.split()) > 1 else None

    if api_key:
        users.update_one({'user_id': user_id}, {'$set': {'api_key': api_key}}, upsert=True)
        await message.reply_text("API key added successfully.")
    else:
        await message.reply_text("Please provide your API key after the command.")

@app.on_message(filters.text & ~filters.command)
async def handle_message(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = users.find_one({'user_id': user_id})

    if user_data:
        api_key = user_data.get('api_key')
        footer = user_data.get('footer', '')
        channel_link = user_data.get('channel_link', 'https://defaultchannel.com')
        disable_text = user_data.get('disable_text', False)
        enable_picture = user_data.get('enable_picture', False)

        if api_key:
            adlinkfly = Adlinkfly(api_key=api_key)
            try:
                url = message.text
                short_url = adlinkfly.convert(url)
                message_text = short_url
                if not disable_text:
                    message_text = f"{message.text}\n{short_url}"
                if enable_picture and message.photo:
                    await message.reply_photo(photo=message.photo.file_id, caption=message_text)
                else:
                    await message.reply_text(message_text)
            except Exception as e:
                await message.reply_text(f"Error: {str(e)}")
        else:
            await message.reply_text('Please add your API Key using /add_api command.')
    else:
        await message.reply_text('No API Key found. Please add your API Key using /add_api command.')

@app.on_message(filters.command("add_channel"))
async def add_channel(client: Client, message: Message):
    user_id = message.from_user.id
    channel_link = message.text.split(None, 1)[1] if len(message.text.split()) > 1 else None

    if channel_link:
        users.update_one({'user_id': user_id}, {'$set': {'channel_link': channel_link}}, upsert=True)
        await message.reply_text("Channel link added successfully.")
    else:
        await message.reply_text("Please provide your channel link after the command.")

@app.on_message(filters.command("remove_channel"))
async def remove_channel(client: Client, message: Message):
    user_id = message.from_user.id
    users.update_one({'user_id': user_id}, {'$unset': {'channel_link': ''}})
    await message.reply_text("Channel link removed.")

@app.on_message(filters.command("add_footer"))
async def add_footer(client: Client, message: Message):
    user_id = message.from_user.id
    footer = message.text.split(None, 1)[1] if len(message.text.split()) > 1 else None

    if footer:
        users.update_one({'user_id': user_id}, {'$set': {'footer': footer}}, upsert=True)
        await message.reply_text("Footer added successfully.")
    else:
        await message.reply_text("Please provide your footer text after the command.")

@app.on_message(filters.command("remove_footer"))
async def remove_footer(client: Client, message: Message):
    user_id = message.from_user.id
    users.update_one({'user_id': user_id}, {'$unset': {'footer': ''}})
    await message.reply_text("Footer removed.")

@app.on_message(filters.command("enable_text"))
async def enable_text(client: Client, message: Message):
    user_id = message.from_user.id
    users.update_one({'user_id': user_id}, {'$set': {'disable_text': False}})
    await message.reply_text("Text output enabled.")

@app.on_message(filters.command("disable_text"))
async def disable_text(client: Client, message: Message):
    user_id = message.from_user.id
    users.update_one({'user_id': user_id}, {'$set': {'disable_text': True}})
    await message.reply_text("Text output disabled.")

@app.on_message(filters.command("enable_picture"))
async def enable_picture(client: Client, message: Message):
    user_id = message.from_user.id
    users.update_one({'user_id': user_id}, {'$set': {'enable_picture': True}})
    await message.reply_text("Pictures and videos output enabled.")

@app.on_message(filters.command("disable_picture"))
async def disable_picture(client: Client, message: Message):
    user_id = message.from_user.id
    users.update_one({'user_id': user_id}, {'$set': {'enable_picture': False}})
    await message.reply_text("Pictures and videos output disabled.")

@app.on_message(filters.command("change_language"))
async def change_language(client: Client, message: Message):
    await message.reply_text("Language change feature is not implemented yet.")

@app.on_message(filters.command("getmyid"))
async def get_my_id(client: Client, message: Message):
    user_id = message.from_user.id
    await message.reply_text(f"Your user ID is: {user_id}")

@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    await message.reply_text("Contact the support team for help.")

async def start_server():
    # Start the Pyrogram client
    await app.start()
    print("Pyrogram Bot is running...")

    # Create and start the web server
    async def handle(request):
        return web.Response(text="Server is running")

    server = web.Application()
    server.router.add_get('/', handle)
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, port=8080)
    await site.start()

    print("Web server is running on port 8080")

    # Keep the bot and web server running
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(start_server())
