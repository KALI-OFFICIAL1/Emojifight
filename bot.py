from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import random
from datetime import datetime
from pymongo import MongoClient

# --- Config ---
API_ID = "21546320"  # Replace with your API ID
API_HASH = "c16805d6f2393d35e7c49527daa317c7"
BOT_TOKEN = "7789344228:AAGLvdcqj70nezj817gJ9RstrAtrD9IMvpo"
MONGO_URI = "mongodb+srv://Somu:Somu@somu.xbkiklu.mongodb.net/?retryWrites=true&w=majority&appName=Somu"

# --- MongoDB Setup ---
mongo = MongoClient(MONGO_URI)
db = mongo["emoji_fight"]
scores = db["scores"]

# --- Emoji Stats ---
ANIMAL_STATS = {
    "🐯": {"name": "Tiger", "speed": 7, "power": 6},
    "🐘": {"name": "Elephant", "speed": 4, "power": 9},
    "🐍": {"name": "Snake", "speed": 9, "power": 5},
    "🐺": {"name": "Wolf", "speed": 6, "power": 6},
    "🦁": {"name": "Lion", "speed": 6, "power": 7},
    "🐶": {"name": "Dog", "speed": 5, "power": 4},
    "🐼": {"name": "Panda", "speed": 3, "power": 8}
}

WEAPON_STATS = {
    "⚔️": {"name": "Sword", "speed": 7, "power": 8},
    "🗡️": {"name": "Dagger", "speed": 9, "power": 5},
    "🔫": {"name": "Pistol", "speed": 8, "power": 7},
    "🪓": {"name": "Axe", "speed": 5, "power": 9},
    "🏹": {"name": "Bow", "speed": 6, "power": 7},
    "🔪": {"name": "Knife", "speed": 8, "power": 6}
}

# --- Titles Based on Score ---
def get_title(score: int):
    if score >= 2000:
        return "God of Emojiland"
    elif score >= 200:
        return "Emoji Warrior"
    elif score >= 100:
        return "Rising Fighter"
    return ""

# --- Welcome Image and Message ---
WELCOME_IMAGE = "https://envs.sh/JBB.jpg"
WELCOME_TEXT = """
🔥 Welcome to **Emoji Fight Arena**! 🔥

Get ready to dive into a world of animals, weapons, and epic 1v1 battles!

Choose your fighter:
⚔️ /animalfight — Use animal emojis to battle  
🔪 /weaponfight — Use weapon emojis to fight your enemies  

▶️ How to Play:  
Reply to someone in a group with /animalfight or /weaponfight and let the battle begin!

Only the boldest will rise through the ranks to become the **God of Emojiland**.  
Let the war of emojis begin!
"""

# --- Bot Init ---
app = Client("emoji_fight_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- Start Command ---
@app.on_message(filters.private & filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_photo(photo=WELCOME_IMAGE, caption=WELCOME_TEXT)

# --- List Command ---
@app.on_message(filters.command("list"))
async def list_emojis(client, message: Message):
    text = "**🧾 Available Emojis:**\n\n__Animals:__\n"
    for emoji, stats in ANIMAL_STATS.items():
        text += f"{emoji} {stats['name']} - Speed: {stats['speed']}/10 | Power: {stats['power']}/10\n"
    text += "\n__Weapons:__\n"
    for emoji, stats in WEAPON_STATS.items():
        text += f"{emoji} {stats['name']} - Speed: {stats['speed']}/10 | Power: {stats['power']}/10\n"
    await message.reply_text(text)

# --- Fight Function ---
async def emoji_fight(message, stats_dict, emoji_type="animal"):
    if not message.reply_to_message:
        return await message.reply_text(f"Reply to someone with a valid {emoji_type} emoji to start a fight!")

    fighter1 = message.from_user
    fighter2 = message.reply_to_message.from_user
    emoji1 = message.text.split(maxsplit=1)[-1].strip()
    emoji2 = message.reply_to_message.text.strip() if message.reply_to_message.text else None

    if emoji1 not in stats_dict or emoji2 not in stats_dict:
        return await message.reply_text(f"Both users must use valid {emoji_type} emojis!")

    score1 = stats_dict[emoji1]["speed"] + stats_dict[emoji1]["power"] + random.randint(1, 6)
    score2 = stats_dict[emoji2]["speed"] + stats_dict[emoji2]["power"] + random.randint(1, 6)

    if score1 > score2:
        winner = fighter1
        loser = fighter2
        winner_emoji = emoji1
    else:
        winner = fighter2
        loser = fighter1
        winner_emoji = emoji2

    # --- Update MongoDB ---
    scores.update_one(
        {"user_id": winner.id},
        {"$inc": {"score": 1}, "$set": {"name": winner.first_name, "last_win": datetime.utcnow()}},
        upsert=True
    )

    user_data = scores.find_one({"user_id": winner.id})
    title = get_title(user_data["score"])

    await message.reply_text(f"{winner_emoji} **{winner.first_name}** {f'({title}) ' if title else ''}defeated **{loser.first_name}** in a {emoji_type} fight!")

# --- Commands ---
@app.on_message(filters.group & filters.command("animalfight"))
async def animal_fight(client, message: Message):
    await emoji_fight(message, ANIMAL_STATS, "animal")

@app.on_message(filters.group & filters.command("weaponfight"))
async def weapon_fight(client, message: Message):
    await emoji_fight(message, WEAPON_STATS, "weapon")

# --- Leaderboard ---
@app.on_message(filters.command("leaderboard"))
async def leaderboard_cmd(client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏅 Today", callback_data="lb_today"),
         InlineKeyboardButton("🌍 Global", callback_data="lb_global"),
         InlineKeyboardButton("🏆 Overall", callback_data="lb_overall")]
    ])
    await message.reply("Choose leaderboard type:", reply_markup=keyboard)

@app.on_callback_query(filters.regex("lb_"))
async def leaderboard_buttons(client, callback_query):
    lb_type = callback_query.data
    now = datetime.utcnow()

    if lb_type == "lb_today":
        today = datetime(now.year, now.month, now.day)
        users = scores.find({"last_win": {"$gte": today}})
    elif lb_type == "lb_global":
        users = scores.find({"score": {"$gte": 1}}).sort("last_win", -1)
    else:  # lb_overall
        users = scores.find().sort("score", -1)

    text = f"**{callback_query.data.split('_')[1].capitalize()} Leaderboard**\n\n"
    for i, user in enumerate(users.limit(10), 1):
        title = get_title(user["score"])
        text += f"{i}. {user.get('name', 'Unknown')} - {user['score']} pts {f'({title})' if title else ''}\n"

    await callback_query.message.edit_text(text, reply_markup=callback_query.message.reply_markup)

# --- Run Bot ---
app.run()