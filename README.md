# Minecraft Whitelist Bot
=========================

A Discord bot that allows users to whitelist themselves for a Minecraft server without administrator intervention.

## Features
-----------

*   User registration via Discord username
*   Minecraft username validation using Mojang API
*   Whitelist management via RCON
*   Log management for user registrations

## Requirements
------------

*   Python 3.8+
*   Discord.py library (>= 1.7.0)
*   aiohttp library (>= 3.0.0)
*   mcrcon library (>= 0.1.0)
*   Discord bot token

## Configuration
--------------

*   `WHITELIST_PATH`: Path to the whitelist JSON file
*   `LOG_PATH`: Path to the log file
*   `TARGET_CHANNEL_ID`: ID of the target channel for whitelist requests
*   `RCON_HOST`: Host IP or hostname of the Minecraft server
*   `RCON_PORT`: RCON port of the Minecraft server
*   `RCON_PASSWORD`: RCON password of the Minecraft server

## Usage
-----

1.  Create a new Discord bot and obtain a bot token
2.  `pip install mcrcon` and `pip install discord.py`
3.  Replace the `WHITELIST_PATH`, `LOG_PATH`, `TARGET_CHANNEL_ID`, `RCON_HOST`, `RCON_PORT`, and `RCON_PASSWORD` variables with your own values
4.  Run the bot using `DiscordBotToWhitelist.py`

## Commands
---------

*   `!whitelist`: Register a Minecraft username
    *   Responds with a message asking for the Minecraft username
    *   Validates the username using Mojang API
    *   Adds the username to the whitelist via RCON
    *   Logs the registration

## License

This project is licensed under the MIT License.

## Contact

You can contact me at @WhatAVibe via discord for any questions.

## Notes
-----

*   This bot uses the Discord.py library for Discord interaction and the aiohttp library for API requests
*   The bot requires a RCON connection to the Minecraft server for whitelist management
*   The bot logs user registrations to a file for auditing purposes
