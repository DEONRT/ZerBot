import os
import asyncio
import discord
from discord.ext import commands
from aiohttp import web

# --- Настройки бота ---
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

ALONE_TIMEOUT = 600  #Через сколько кикает
active_timers = {}

@bot.event
async def on_ready():
    print(f"Бот {bot.user} успешно запущен в облаке!")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    channels_to_check = set()
    if before.channel:
        channels_to_check.add(before.channel)
    if after.channel:
        channels_to_check.add(after.channel)

    for channel in channels_to_check:
        humans = [m for m in channel.members if not m.bot]

        if len(humans) == 1:
            lone_member = humans[0]
            if lone_member.id not in active_timers:
                task = asyncio.create_task(kick_if_still_alone(lone_member, channel))
                active_timers[lone_member.id] = task
        else:
            for m in channel.members:
                if m.id in active_timers:
                    active_timers[m.id].cancel()
                    del active_timers[m.id]

async def kick_if_still_alone(member, channel):
    try:
        await asyncio.sleep(ALONE_TIMEOUT)
        if member.voice and member.voice.channel == channel:
            humans = [m for m in channel.members if not m.bot]
            if len(humans) == 1:
                await member.move_to(None, reason="Одиночное пребывание в голосовом канале")
    except asyncio.CancelledError:
        pass
    finally:
        active_timers.pop(member.id, None)

async def handle(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    await start_web_server()
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise ValueError("Не задана переменная окружения DISCORD_TOKEN!")
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())