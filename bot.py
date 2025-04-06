from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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

# --- Fight Function with Emoji Buttons ---
async def emoji_fight(message, stats_dict, emoji_type="animal"):
    if not message.reply_to_message:
        return await message.reply_text("Reply to someone’s message to start a fight!")

    opponent = message.reply_to_message.from_user
    emojis = list(stats_dict.keys())
    buttons = [
        [InlineKeyboardButton(emoji, callback_data=f"{emoji_type}_{emoji}_{message.from_user.id}_{opponent.id}")]
        for emoji in emojis
    ]

    await message.reply_text(
        f"**{message.from_user.first_name}**, choose your {emoji_type} emoji to fight with:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# --- Emoji Button Callback ---
@app.on_callback_query(filters.regex(r"^(animal|weapon)_"))
async def emoji_choice_callback(client, callback_query: CallbackQuery):
    data = callback_query.data.split("_")
    emoji_type, emoji, fighter1_id, fighter2_id = data[0], data[1], int(data[2]), int(data[3])

    if callback_query.from_user.id != fighter1_id:
        return await callback_query.answer("You're not the player!", show_alert=True)

    stats_dict = ANIMAL_STATS if emoji_type == "animal" else WEAPON_STATS

    fighter1 = callback_query.from_user
    message = callback_query.message

    # Ask opponent to choose
    emojis = list(stats_dict.keys())
    buttons = [
        [InlineKeyboardButton(e, callback_data=f"{emoji_type}_vs_{emoji}_{e}_{fighter1_id}_{fighter2_id}")]
        for e in emojis
    ]

    await message.edit_text(
        f"**{fighter1.first_name}** chose {emoji}!\n\nNow **{fighter2_id}** choose your emoji:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# --- Final Callback: Player 2 selects emoji and result shown ---
@app.on_callback_query(filters.regex(r"^(animal|weapon)_vs_"))
async def emoji_battle_result(client, callback_query: CallbackQuery):
    data = callback_query.data.split("_")
    emoji_type = data[0]
    emoji1 = data[2]
    emoji2 = data[3]
    fighter1_id = int(data[4])
    fighter2_id = int(data[5])

    if callback_query.from_user.id != fighter2_id:
        return await callback_query.answer("You're not the second player!", show_alert=True)

    stats_dict = ANIMAL_STATS if emoji_type == "animal" else WEAPON_STATS

    fighter1 = await client.get_users(fighter1_id)
    fighter2 = callback_query.from_user

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

    scores.update_one(
        {"user_id": winner.id},
        {"$inc": {"score": 1}, "$set": {"name": winner.first_name, "last_win": datetime.utcnow()}},
        upsert=True
    )
    user_data = scores.find_one({"user_id": winner.id})
    title = get_title(user_data["score"])
    
    await callback_query.message.edit_text(
        f"{winner_emoji} **{winner.first_name}** {f'({title}) ' if title else ''}defeated **{loser.first_name}** in a {emoji_type} fight!"
    )

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
    else:
        users = scores.find().sort("score", -1)

    text = f"**{lb_type.split('_')[1].capitalize()} Leaderboard**\n\n"
    for i, user in enumerate(users.limit(10), 1):
        title = get_title(user["score"])
        text += f"{i}. {user.get('name', 'Unknown')} - {user['score']} pts {f'({title})' if title else ''}\n"

    await callback_query.message.edit_text(text, reply_markup=callback_query.message.reply_markup)

# --- Help Command ---
@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    help_text = """
**🆘 Emoji Fight Bot Help Menu**

Welcome to Emoji Fight Arena! Here's what you can do:

**🎮 Game Commands**
- `/animalfight` — Reply to someone and fight using animal emojis
- `/weaponfight` — Reply to someone and fight using weapon emojis
- Choose emojis from buttons and let the battle begin!

**📋 Info Commands**
- `/list` — See available emojis with stats
- `/leaderboard` — Check top players (Today / Global / Overall)
- `/help` — Show this help message

**🏆 Scoring System**
- Win battles to earn points
- Titles based on your score:
  - 100+ : Rising Fighter
  - 200+ : Emoji Warrior
  - 2000+ : God of Emojiland

**ℹ️ How To Play**
1. Reply to someone’s message in a group.
2. Use `/animalfight` or `/weaponfight`.
3. Both players select emoji via buttons.
4. Bot calculates winner based on speed, power, and luck!

Enjoy the fight!
"""
    await message.reply_text(help_text)

# --- Run Bot ---
app.run()