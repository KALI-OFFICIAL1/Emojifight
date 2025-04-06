from pyrogram import Client, filters
from pyrogram.types import Message
import random

# --- Config ---
API_ID = 12345678  # Replace with your API ID
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"

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
WELCOME_IMAGE = "https://yourdomain.com/emoji_fight_welcome.jpg"
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

# --- /start Command ---
@app.on_message(filters.private & filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_photo(photo=WELCOME_IMAGE, caption=WELCOME_TEXT)

# --- /list Command ---
@app.on_message(filters.command("list"))
async def list_emojis(client, message: Message):
    text = "**🧾 Available Emojis:**\n\n"
    text += "__Animals:__\n"
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
        winner_emoji = emoji1
        loser = fighter2
    else:
        winner = fighter2
        winner_emoji = emoji2
        loser = fighter1

    title = get_title(150)  # Placeholder; later will use actual score
    await message.reply_text(f"{title} {winner_emoji} **{winner.first_name}** defeated **{loser.first_name}** in a {emoji_type} fight!")

# --- /animalfight Command ---
@app.on_message(filters.group & filters.command("animalfight"))
async def animal_fight(client, message: Message):
    await emoji_fight(message, ANIMAL_STATS, "animal")

# --- /weaponfight Command ---
@app.on_message(filters.group & filters.command("weaponfight"))
async def weapon_fight(client, message: Message):
    await emoji_fight(message, WEAPON_STATS, "weapon")

# --- Run Bot ---
app.run()
