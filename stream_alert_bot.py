import discord
import aiohttp
import asyncio
import os
from discord.ext import commands, tasks

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
ALERT_CHANNEL_ID = 1085418150310445106

TWITCH_STREAMERS = [
    "xx_aichaxx",
    "Gabriottigaming84",
    "Borotalcotv",
    "Ciro_mlm",
    "Azizjunior_",
    "Gabry_il_matto",
    "fefeccio",
    "Incubopuro",
]

KICK_STREAMERS = [
    "FrankJack89",
    "Gi0rgina",
]

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

twitch_token = None
live_status = {}

async def get_twitch_token():
    global twitch_token
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params) as r:
            data = await r.json()
            twitch_token = data.get("access_token")

async def check_twitch(streamer):
    global twitch_token
    url = f"https://api.twitch.tv/helix/streams?user_login={streamer}"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {twitch_token}",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as r:
            data = await r.json()
            streams = data.get("data", [])
            if streams:
                return {
                    "live": True,
                    "title": streams[0].get("title", "Nessun titolo"),
                    "game": streams[0].get("game_name", "Sconosciuto"),
                    "viewers": streams[0].get("viewer_count", 0),
                    "url": f"https://twitch.tv/{streamer}",
                    "thumbnail": streams[0].get("thumbnail_url", "").replace("{width}", "320").replace("{height}", "180"),
                }
            return {"live": False}

async def check_kick(streamer):
    url = f"https://kick.com/api/v1/channels/{streamer}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status != 200:
                return {"live": False}
            data = await r.json()
            livestream = data.get("livestream")
            if livestream:
                return {
                    "live": True,
                    "title": livestream.get("session_title", "Nessun
