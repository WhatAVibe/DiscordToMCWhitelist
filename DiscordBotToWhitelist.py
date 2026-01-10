import discord
from discord.ext import commands
import json
import aiohttp
import os
from pathlib import Path
import asyncio
import logging
import mcrcon

# Configuration
WHITELIST_PATH = r"C:\whitelist.json"
LOG_PATH = r"C:\log.txt"
TARGET_CHANNEL_ID = 123456789123456789  # The channel ID where the bot should respond
RCON_HOST = "localhost"  # Replace with your server IP or keep localhost if hosted on same machine
RCON_PORT = 25575  # Default RCON port
RCON_PASSWORD = "secret"  # Replace with your RCON password


logging.getLogger('discord').setLevel(logging.WARNING)
logging.getLogger('discord').propagate = False

registration_logger = logging.getLogger('registration')
registration_logger.setLevel(logging.INFO)
registration_logger.propagate = False

file_handler = logging.FileHandler(LOG_PATH, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(message)s'))
registration_logger.addHandler(file_handler)

# Track registered users
VERIFIED_USERS = set()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

async def get_minecraft_uuid(username: str) -> dict | None:
    """Fetch Minecraft UUID from username using Mojang API"""
    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Convert 'id' to 'uuid' for consistency
                    data['uuid'] = data.pop('id')
                    return data
                elif response.status == 404:
                    return None
                else:
                    return None
    except Exception as e:
        print(f"Error fetching UUID: {e}")
        return None

async def reload_whitelist(username: str):
    """Add user to Minecraft whitelist via RCON"""
    try:
        # Create a new RCON connection with explicit type casting
        rcon = mcrcon.MCRcon(host=RCON_HOST, port=int(RCON_PORT), password=RCON_PASSWORD)
        # Connect to the server
        rcon.connect()
        # Send the add command
        response = rcon.command(f"whitelist add {username}")
        print(f"✅ RCON Response: {response}")
        # Disconnect from the server
        rcon.disconnect()
        return True
    except Exception as e:
        print(f"❌ RCON Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def load_whitelist() -> list:
    """Load existing whitelist"""
    if os.path.exists(WHITELIST_PATH):
        with open(WHITELIST_PATH, 'r') as f:
            return json.load(f)
    return []

def save_whitelist(whitelist: list):
    """Save whitelist to file"""
    os.makedirs(os.path.dirname(WHITELIST_PATH), exist_ok=True)
    with open(WHITELIST_PATH, 'w') as f:
        json.dump(whitelist, f, indent=2)

def load_log() -> list:
    """Load existing log"""
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r') as f:
            return f.readlines()
    return []

def user_already_registered(user_id: int) -> bool:
    """Check if user has already registered"""
    return user_id in VERIFIED_USERS

def add_to_verified(user_id: int):
    """Mark user as verified"""
    VERIFIED_USERS.add(user_id)

def is_username_in_whitelist(username: str) -> bool:
    """Check if username already exists in whitelist"""
    whitelist = load_whitelist()
    return any(entry["name"].lower() == username.lower() for entry in whitelist)

def is_user_in_log(user_id: int) -> bool:
    """Check if user has been in the log before"""
    log_entries = load_log()
    return any(f"Discord ID: {user_id}" in entry for entry in log_entries)

@bot.event
async def on_ready():
    """Bot startup message"""
    print(f"✓ Bot logged in as {bot.user}")
    print(f"✓ Whitelist path: {WHITELIST_PATH}")
    print(f"✓ Log path: {LOG_PATH}")
    print(f"✓ Bot is ready to vailidate whitelist requests")
    
    # Load previous registrations from log
    try:
        log_entries = load_log()
        for entry in log_entries:
            if "Discord ID: " in entry:
                start = entry.find("Discord ID: ") + len("Discord ID: ")
                end = entry.find(")", start)
                if start > 0 and end > start:
                    user_id_str = entry[start:end]
                    try:
                        user_id = int(user_id_str)
                        add_to_verified(user_id)
                    except ValueError:
                        pass
    except Exception:
        pass

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors silently"""
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"Error: {error}")

@bot.event
async def on_message(message):
    """Only respond to messages in the target channel"""
    if message.channel.id != TARGET_CHANNEL_ID:
        return
    
    await bot.process_commands(message)

@bot.command(name="whitelist")
async def whitelist(ctx):
    """Register Minecraft username"""
    
    # Check if user already registered
    if user_already_registered(ctx.author.id):
        await ctx.send("❌ You have already registered a Minecraft account. You can only register once.")
        return
    
    # Check if user has been in the log before
    if is_user_in_log(ctx.author.id):
        await ctx.send("❌ You have already registered before. You can only register once.")
        return
    
    # Check if username already in whitelist
    whitelist = load_whitelist()
    if any(entry["name"].lower() == ctx.author.display_name.lower() for entry in whitelist):
        await ctx.send("❌ Your username is already in the whitelist.")
        return
    
    await ctx.send("Please enter your Minecraft username:")
    
    try:
        message = await bot.wait_for(
            'message',
            timeout=30.0,
            check=lambda m: m.author == ctx.author and isinstance(m.channel, discord.TextChannel)
        )
        username = message.content.strip()
        
        # Validate username format
        if not username or len(username) > 16 or len(username) < 3:
            await ctx.send("❌ Invalid username. Minecraft usernames must be 3-16 characters.")
            return
        
        if is_username_in_whitelist(username):
            await ctx.send(f"❌ The username '{username}' is already whitelisted.")
            return
        
        # Fetch UUID from Mojang API
        await ctx.send(f"🔍 Checking username '{username}'")
        uuid_data = await get_minecraft_uuid(username)
        
        if uuid_data is None:
            await ctx.send(f"❌ Username '{username}' not found. Please check the spelling and try again.")
            return
        
        # Create initial message
        initial_message = await ctx.send("Please wait while we add your username to the whitelist...")
        
        await initial_message.edit(content=f"{initial_message.content}\n🔍 Username {uuid_data['name']} validated...")
        await asyncio.sleep(2)
        
        await initial_message.edit(content=f"{initial_message.content}\n✅ Adding {uuid_data['name']} to whitelist...")
        await asyncio.sleep(1)
        
        # Add to whitelist via RCON
        await initial_message.edit(content=f"{initial_message.content}\n✅ Adding {uuid_data['name']} to whitelist...")
        success = await reload_whitelist(uuid_data['name'])
        
        if success:
            # Log the registration
            log_entry = f"User: {ctx.author.name}#{ctx.author.discriminator} (Discord ID: {ctx.author.id}) Whitelisted: {uuid_data['name']} (UUID: {uuid_data['uuid']})"
            registration_logger.info(log_entry)
            
            await initial_message.edit(content=f"{initial_message.content}\n✅ Success! '{uuid_data['name']}' has been added to the whitelist.")
        else:
            await initial_message.edit(content=f"{initial_message.content}\n❌ Failed to add '{uuid_data['name']}' to the whitelist.")
        
    except asyncio.TimeoutError:
        await ctx.send("❌ You took too long to respond. Please try again.")
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

bot.run("BOT-TOKEN-HERE")
