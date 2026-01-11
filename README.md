# Minecraft Whitelist Bot
=========================

A Discord bot that allows users to whitelist themselves for a Minecraft server without administrator intervention.
![](https://cdn.discordapp.com/attachments/1053456829369290803/1459757081866404083/cUncbsGjam.gif?ex=69647039&is=69631eb9&hm=2860be04942f416386f3ebce27541116e2a596b5bf6c619e9dbc669d8ee88f7a&)
![](https://cdn.discordapp.com/attachments/1053456829369290803/1459757595370983565/image.png?ex=696470b3&is=69631f33&hm=bf653fa45c6ac897bec3b8668099d1bff630ae3be8c5fa6b23f2cdf7fbc5a35b&)


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
*   `ROLE_ID` Used for giving "Whitelist" role or whatever you want it to be after verification
*   `ROLE_NAME` Admin role name for bot usage in any channel and list current whitelist

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
*   `!remove`: Remove self from whitelist
    *   Checks if user is in the logs then removes whitelist and role

## License

This project is licensed under the MIT License.

## Contact

You can contact me at @WhatAVibe via discord for any questions.

## Notes
-----

*   This bot uses the Discord.py library for Discord interaction and the aiohttp library for API requests
*   The bot requires a RCON connection to the Minecraft server for whitelist management
*   The bot logs user registrations to a file for auditing purposes
