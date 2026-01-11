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
RCON_HOST = "localhost"  # Replace with your server IP (192.#.#.# for same network but different device)
RCON_PORT = 25575  # Default RCON port (explicitly an integer)
RCON_PASSWORD = "secret"  # Replace with your RCON password
ROLE_ID = 1459571224568139786  # The role ID given to users after verification
ROLE_NAME = (
    "."  # The role name required to list and use commands in any channel along with !list (admin role)
)

logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("discord").propagate = False

registration_logger = logging.getLogger("registration")
registration_logger.setLevel(logging.INFO)
registration_logger.propagate = False

file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(message)s"))
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
                    data["uuid"] = data.pop("id")
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
        rcon = mcrcon.MCRcon(
            host=RCON_HOST, port=int(RCON_PORT), password=RCON_PASSWORD
        )
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


async def remove_from_whitelist(username: str):
    """Remove user from Minecraft whitelist via RCON"""
    try:
        rcon = mcrcon.MCRcon(
            host=RCON_HOST, port=int(RCON_PORT), password=RCON_PASSWORD
        )
        # Connect to the server
        rcon.connect()
        # Send the remove command
        response = rcon.command(f"whitelist remove {username}")
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
        with open(WHITELIST_PATH, "r") as f:
            return json.load(f)
    return []


def save_whitelist(whitelist: list):
    """Save whitelist to file"""
    os.makedirs(os.path.dirname(WHITELIST_PATH), exist_ok=True)
    with open(WHITELIST_PATH, "w") as f:
        json.dump(whitelist, f, indent=2)


def load_log() -> list:
    """Load existing log"""
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
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


def remove_log_entry(user_id: int):
    """Remove the log entry for the user"""
    log_entries = load_log()
    with open(LOG_PATH, "w") as f:
        for entry in log_entries:
            if f"Discord ID: {user_id}" not in entry:
                f.write(entry)


@bot.event
async def on_ready():
    """Bot startup message"""
    print(f"✓ Bot logged in as {bot.user}")
    print(f"✓ Whitelist path: {WHITELIST_PATH}")
    print(f"✓ Log path: {LOG_PATH}")
    print(f"✓ Bot is ready to validate whitelist requests")

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
    """Process commands in any channel, but only respond to messages in the target channel"""
    # Check if the user has the required role
    required_role = discord.utils.get(message.guild.roles, name=ROLE_NAME)

    # If the user has the required role, allow them to use commands in any channel
    if required_role is not None and required_role in message.author.roles:
        # Process commands in any channel for users with the required role
        await bot.process_commands(message)
        return

    # For users without the required role, only process commands in the target channel
    if message.channel.id != TARGET_CHANNEL_ID:
        return

    # Process commands in the target channel
    await bot.process_commands(message)


@bot.command(name="whitelist")
async def whitelist(ctx):
    """Register Minecraft username"""

    # Check if user already registered
    if user_already_registered(ctx.author.id):
        await ctx.send(
            "❌ You have already registered a Minecraft account. You can only register once."
        )
        return

    # Check if user has been in the log before
    if is_user_in_log(ctx.author.id):
        await ctx.send(
            "❌ You have already registered before. You can only register once."
        )
        return

    # Check if username already in whitelist
    whitelist = load_whitelist()
    if any(
        entry["name"].lower() == ctx.author.display_name.lower() for entry in whitelist
    ):
        await ctx.send("❌ Your username is already in the whitelist.")
        return

    await ctx.send("Please enter your Minecraft username:")

    try:
        message = await bot.wait_for(
            "message",
            timeout=30.0,
            check=lambda m: m.author == ctx.author
            and isinstance(m.channel, discord.TextChannel),
        )
        username = message.content.strip()

        # Validate username format
        if not username or len(username) > 16 or len(username) < 3:
            await ctx.send(
                "❌ Invalid username. Minecraft usernames must be 3-16 characters."
            )
            return

        if is_username_in_whitelist(username):
            await ctx.send(f"❌ The username '{username}' is already whitelisted.")
            return

        # Fetch UUID from Mojang API
        await ctx.send(f"🔍 Checking username '{username}'")
        uuid_data = await get_minecraft_uuid(username)

        if uuid_data is None:
            await ctx.send(
                f"❌ Username '{username}' not found. Please check the spelling and try again."
            )
            return

        # Create initial message
        initial_message = await ctx.send(
            "Please wait while we add your username to the whitelist..."
        )

        await initial_message.edit(
            content=f"{initial_message.content}\n🔍 Username {uuid_data['name']} validated..."
        )
        await asyncio.sleep(2)

        await initial_message.edit(
            content=f"{initial_message.content}\n✅ Adding {uuid_data['name']} to whitelist..."
        )
        await asyncio.sleep(1)

        # Add to whitelist via RCON
        await initial_message.edit(
            content=f"{initial_message.content}\n✅ Adding {uuid_data['name']} to whitelist..."
        )
        success = await reload_whitelist(uuid_data["name"])

        if success:
            # Log the registration
            log_entry = f"User: {ctx.author.name}#{ctx.author.discriminator} (Discord ID: {ctx.author.id}) Whitelisted: {uuid_data['name']} (UUID: {uuid_data['uuid']})"
            registration_logger.info(log_entry)

            # Add the role to the user
            role = ctx.guild.get_role(ROLE_ID)
            if role:
                await ctx.author.add_roles(role)
                await initial_message.edit(
                    content=f"{initial_message.content}\n✅ Success! '{uuid_data['name']}' has been added to the whitelist and you've been given the role."
                )
            else:
                await initial_message.edit(
                    content=f"{initial_message.content}\n✅ Success! '{uuid_data['name']}' has been added to the whitelist. You've been given the role."
                )
        else:
            await initial_message.edit(
                content=f"{initial_message.content}\n❌ Failed to add '{uuid_data['name']}' to the whitelist."
            )

    except asyncio.TimeoutError:
        await ctx.send("❌ You took too long to respond. Please try again.")
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")


@bot.command(name="remove")
async def remove(ctx):
    """Remove your whitelist entry"""
    # Check if user has been in the log before
    if not is_user_in_log(ctx.author.id):
        await ctx.send(
            "❌ You haven't registered before. You can't remove a non-existent entry."
        )
        return

    # Find the log entry and extract the Minecraft username
    log_entries = load_log()
    username = None
    for entry in log_entries:
        if f"Discord ID: {ctx.author.id}" in entry:
            start = entry.find("Whitelisted: ") + len("Whitelisted: ")
            end = entry.find(" (UUID:", start)
            if start > 0 and end > start:
                username = entry[start:end]
                break

    if username is None:
        await ctx.send("❌ Unable to find your Minecraft username in the log.")
        return

    # Remove from whitelist via RCON
    success = await remove_from_whitelist(username)

    if success:
        # Remove the log entry
        remove_log_entry(ctx.author.id)

        # Remove the role from the user
        role = ctx.guild.get_role(ROLE_ID)
        if role:
            await ctx.author.remove_roles(role)

        # Send confirmation message
        await ctx.send(
            f"✅ Your whitelist has been removed and you've lost the role. You can register again."
        )
    else:
        await ctx.send("❌ Failed to remove your whitelist entry. Please try again.")


@bot.command(name="list")
async def listwhitelist(ctx):
    """List all whitelisted players on the server (requires role named '.')"""
    # Check if user has the required role
    required_role = discord.utils.get(ctx.guild.roles, name=ROLE_NAME)
    if required_role is None or required_role not in ctx.author.roles:
        await ctx.send("❌ You don't have the required role to use this command.")
        return

    # Load whitelist
    whitelist = load_whitelist()

    # Format the list of players
    if not whitelist:
        await ctx.send("❌ No players are currently whitelisted.")
        return

    # Create a formatted list of players
    player_list = []
    for entry in whitelist:
        player_list.append(f"{entry['name']} (UUID: {entry['uuid']})")

    # Send the list in a formatted message
    message = "📋 Whitelisted Players:\n\n"
    message += "\n".join(player_list)

    # Send the message
    await ctx.send(message)


bot.run("BOT_TOKEN_HERE")
