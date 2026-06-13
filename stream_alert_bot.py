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
    url = "https://api.twitch.tv/helix/streams?user_login=" + streamer
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": "Bearer " + twitch_token,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as r:
            data = await r.json()
            streams = data.get("data", [])
            if streams:
                thumb = streams[0].get("thumbnail_url", "")
                thumb = thumb.replace("{width}", "320").replace("{height}", "180")
                return {
                    "live": True,
                    "title": streams[0].get("title", "Nessun titolo"),
                    "game": streams[0].get("game_name", "Sconosciuto"),
                    "viewers": streams[0].get("viewer_count", 0),
                    "url": "https://twitch.tv/" + streamer,
                    "thumbnail": thumb,
                }
            return {"live": False}

async def check_kick(streamer):
    url = "https://kick.com/api/v1/channels/" + streamer
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status != 200:
                return {"live": False}
            data = await r.json()
            livestream = data.get("livestream")
            if livestream:
                cats = livestream.get("categories", [])
                game = cats[0].get("name", "Sconosciuto") if cats else "Sconosciuto"
                thumb = livestream.get("thumbnail", {})
                thumb_url = thumb.get("url", "") if thumb else ""
                return {
                    "live": True,
                    "title": livestream.get("session_title", "Nessun titolo"),
                    "game": game,
                    "viewers": livestream.get("viewer_count", 0),
                    "url": "https://kick.com/" + streamer,
                    "thumbnail": thumb_url,
                }
            return {"live": False}

async def send_alert(streamer, info, platform):
    channel = bot.get_channel(ALERT_CHANNEL_ID)
    if not channel:
        print("Canale non trovato!")
        return
    color = 0x9146FF if platform == "Twitch" else 0x53FC18
    emoji = "[Twitch]" if platform == "Twitch" else "[Kick]"
    embed = discord.Embed(
        title=emoji + " " + streamer + " e LIVE su " + platform + "!",
        description=info["title"],
        color=color,
        url=info["url"],
    )
    embed.add_field(name="Gioco", value=info["game"], inline=True)
    embed.add_field(name="Spettatori", value=str(info["viewers"]), inline=True)
    embed.add_field(name="Link", value=info["url"], inline=False)
    if info.get("thumbnail"):
        embed.set_image(url=info["thumbnail"])
    embed.set_footer(text="Alert automatico - " + platform)
    await channel.send("@everyone", embed=embed)

@tasks.loop(minutes=2)
async def check_streams():
    global twitch_token
    print("Controllo streams...")
    if not twitch_token:
        await get_twitch_token()
    for streamer in TWITCH_STREAMERS:
        key = "twitch_" + streamer.lower()
        try:
            info = await check_twitch(streamer)
            if info["live"] and not live_status.get(key):
                live_status[key] = True
                await send_alert(streamer, info, "Twitch")
            elif not info["live"]:
                live_status[key] = False
        except Exception as e:
            print("Errore Twitch " + streamer + ": " + str(e))
    for streamer in KICK_STREAMERS:
        key = "kick_" + streamer.lower()
        try:
            info = await check_kick(streamer)
            if info["live"] and not live_status.get(key):
                live_status[key] = True
                await send_alert(streamer, info, "Kick")
            elif not info["live"]:
                live_status[key] = False
        except Exception as e:
            print("Errore Kick " + streamer + ": " + str(e))

@bot.event
async def on_ready():
    print("StreamAlertBot online come " + str(bot.user))
    check_streams.start()

bot.run(DISCORD_TOKEN)
