import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# --- Configuración del bot ---
TOKEN = os.getenv("TOKEN")
VOICE_CHANNEL_ID = 1359566862123532502  # ID del canal de voz
RPP_STREAM_URL = "https://mdstrm.com/audio/5fab3416b5f9ef165cfab6e9/live.m3u8"
FFMPEG_PATH = "ffmpeg"

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    await connect_and_play()

async def connect_and_play():
    """Conectar al canal de voz y reproducir RPP"""
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if channel:
        if channel.guild.voice_client is None:
            vc = await channel.connect()
        else:
            vc = channel.guild.voice_client

            # Agregamos opciones a ffmpeg para que él mismo soporte micro-cortes y se reconecte
            FFMPEG_OPTIONS = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -user_agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" -headers "Referer: https://rpp.pe/\r\nOrigin: https://rpp.pe"',
                'options': '-vn'
            }
            vc.play(
                discord.FFmpegPCMAudio(RPP_STREAM_URL, executable=FFMPEG_PATH, **FFMPEG_OPTIONS),
                after=lambda e: bot.loop.create_task(restart_stream(vc))
            )

async def restart_stream(vc):
    """Reinicia el stream si se detiene"""
    if vc and not vc.is_playing():
        print("⏳ Stream caído. Esperando 5 segundos antes de reintentar...")
        await asyncio.sleep(5)
        print("🔄 Reiniciando stream...")
        try:
            FFMPEG_OPTIONS = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -user_agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" -headers "Referer: https://rpp.pe/\r\nOrigin: https://rpp.pe"',
                'options': '-vn'
            }
            vc.play(
                discord.FFmpegPCMAudio(RPP_STREAM_URL, executable=FFMPEG_PATH, **FFMPEG_OPTIONS),
                after=lambda e: bot.loop.create_task(restart_stream(vc))
            )
        except Exception as e:
            print(f"Error al reiniciar: {e}")

@bot.command()
async def stop(ctx):
    """Comando para parar la radio"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("⏹️ Radio detenida")

bot.run(TOKEN)
