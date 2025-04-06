from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import random
from datetime import datetime
from pymongo import MongoClient

# --- Config ---
API_ID = "21546320"
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

# --- Titles ---
def get_title(score: int):
    if score >= 2000:
        return "God of Emojiland"
    elif score >= 200:
        return "Emoji Warrior"
    elif score >= 100:
        return "Rising Fighter"
    return ""

# --- Welcome Message ---
WELCOME_IMAGE = "https://envs.sh/JBB.jpg"
WELCOME_TEXT = """
🔥 Welcome to **Emoji Fight Arena**! 🔥

Choose your fighter:
⚔️ /animalfight — Use animal emojis  
🔪 /weaponfight — Use weapon emojis  

▶️ How to Play:  
Reply to someone in a group with /animalfight or /weaponfight.  
Then select your emoji and let the fight begin!
"""

# --- App Init ---
app = Client("emoji_fight_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- /start ---
@app.on_message(filters.private & filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_photo(WELCOME_IMAGE, caption=WELCOME_TEXT)

# --- /list ---
@app.on_message(filters.command("list"))
async def list_emojis(client, message: Message):
    text = "**🧾 Available Emojis:**\n\n__Animals:__\n"
    for emoji, stats in ANIMAL_STATS.items():
        text += f"{emoji} {stats['name']} - Speed: {stats['speed']}/10 | Power: {stats['power']}/10\n"
    text += "\n__Weapons:__\n"
    for emoji, stats in WEAPON_STATS.items():
        text += f"{emoji} {stats['name']} - Speed: {stats['speed']}/10 | Power: {stats['power']}/10\n"
    await message.reply_text(text)

# --- Emoji Selection ---
selected_emojis = {}

def build_emoji_keyboard(emoji_dict, prefix):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(emoji, callback_data=f"{prefix}:{emoji}")]
        for emoji in emoji_dict
    ])

@app.on_message(filters.group & filters.command(["animalfight", "weaponfight"]))
async def emoji_fight_start(client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to someone to start the fight!")

    emoji_type = message.command[0].replace("fight", "")
    stats_dict = ANIMAL_STATS if emoji_type == "animal" else WEAPON_STATS

    initiator_id = message.from_user.id
    opponent_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id

    key = f"{chat_id}:{initiator_id}:{opponent_id}"
    selected_emojis[key] = {"type": emoji_type, "initiator": None, "opponent": None}

    await message.reply_text(
        f"{message.from_user.first_name}, choose your {emoji_type} emoji:",
        reply_markup=build_emoji_keyboard(stats_dict, f"fight_{key}_init")
    )

    await message.reply_text(
        f"{message.reply_to_message.from_user.first_name}, choose your {emoji_type} emoji:",
        reply_markup=build_emoji_keyboard(stats_dict, f"fight_{key}_opp")
    )

@app.on_callback_query(filters.regex(r"^fight_(.+)_(init|opp):(.+)$"))
async def emoji_selected(client, callback_query: CallbackQuery):
    full_key, role, emoji = callback_query.data.split(":", maxsplit=2)
    _, chat_id, initiator_id, opponent_id = full_key.split("_")
    chat_key = f"{chat_id}:{initiator_id}:{opponent_id}"

    if chat_key not in selected_emojis:
        return await callback_query.answer("Fight session expired.", show_alert=True)

    selected_emojis[chat_key][role] = emoji
    await callback_query.answer(f"Selected {emoji}!")

    data = selected_emojis[chat_key]
    if data["initiator"] and data["opponent"]:
        stats_dict = ANIMAL_STATS if data["type"] == "animal" else WEAPON_STATS
        user1 = await client.get_users(int(initiator_id))
        user2 = await client.get_users(int(opponent_id))

        score1 = stats_dict[data["initiator"]]["speed"] + stats_dict[data["initiator"]]["power"] + random.randint(1, 6)
        score2 = stats_dict[data["opponent"]]["speed"] + stats_dict[data["opponent"]]["power"] + random.randint(1, 6)

        if score1 > score2:
            winner, loser = user1, user2
            win_emoji = data["initiator"]
        else:
            winner, loser = user2, user1
            win_emoji = data["opponent"]

        scores.update_one(
            {"user_id": winner.id},
            {"$inc": {"score": 1}, "$set": {"name": winner.first_name, "last_win": datetime.utcnow()}},
            upsert=True
        )

        score_data = scores.find_one({"user_id": winner.id})
        title = get_title(score_data["score"])
        await callback_query.message.reply_text(
            f"{win_emoji} **{winner.first_name}** {f'({title}) ' if title else ''}defeated **{loser.first_name}** in a {data['type']} fight!"
        )
        del selected_emojis[chat_key]

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
async def leaderboard_buttons(client, callback_query: CallbackQuery):
    lb_type = callback_query.data
    now = datetime.utcnow()

    if lb_type == "lb_today":
        today = datetime(now.year, now.month, now.day)
        users = scores.find({"last_win": {"$gte": today}})
    elif lb_type == "lb_global":
        users = scores.find({"score": {"$gte": 1}}).sort("last_win", -1)
    else:
        users = scores.find().sort("score", -1)

    text = f"**{lb_type.split('_')[1].capitalize()} Leaderboard**\n\n"
    for i, user in enumerate(users.limit(10), 1):
        title = get_title(user["score"])
        text += f"{i}. {user.get('name', 'Unknown')} - {user['score']} pts {f'({title})' if title else ''}\n"

    await callback_query.message.edit_text(text, reply_markup=callback_query.message.reply_markup)

# --- Run Bot ---
app.run()