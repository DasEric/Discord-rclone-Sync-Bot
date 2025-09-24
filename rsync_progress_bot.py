
import discord
import asyncio
from datetime import datetime

# --- Konfiguration ---
TOKEN = "MTQyMDQxMjgxMDI1NjU4NDcwNQ.Gcgcky.bN88QHwwkApc40wGHFxCo5MYQWykI1ZXm2pjJs"
CHANNEL_ID = 1420173162846490784  # Discord-Kanal-ID
PROGRESS_FILE = "/tmp/rsync_progress.txt"
UPDATE_INTERVAL = 2  # Sekunden

intents = discord.Intents.default()
client = discord.Client(intents=intents)

progress_message = None

async def update_progress():
    global progress_message
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    while not client.is_closed():
        try:
            with open(PROGRESS_FILE, "r") as f:
                line = f.readline().strip()

            if not line:
                await asyncio.sleep(UPDATE_INTERVAL)
                continue

            parts = line.split(",")
            if len(parts) != 3:
                await asyncio.sleep(UPDATE_INTERVAL)
                continue

            status, synced_str, total_str = parts

            try:
                synced = int(synced_str)
                total = int(total_str)
            except ValueError:
                await asyncio.sleep(UPDATE_INTERVAL)
                continue

            def bytes_to_gb(b):
                return f"{b / (1024**3):.2f}"

            if total == 0:
                percent = 0
            else:
                percent = int(synced * 100 / total)

            total_gb = bytes_to_gb(total)
            synced_gb = bytes_to_gb(synced)

            if status == "START":
                description = f"Fortschritt: **0%**\n(0 von {total_gb} GB)"
                color = 0xFFFF00
            elif status == "SUCCESS":
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                description = f"✅ Das Backup wurde Erfolgreich auf dem NAS Gespeichert\n*Abgeschlossen am: {timestamp}*"
                color = 0x00FF00
            elif status == "FAIL":
                description = f"Fortschritt: **Fehler**\n({synced_gb} von {total_gb} GB)\n❌ Backup fehlgeschlagen"
                color = 0xFF0000
            else: # PROGRESS
                description = f"Fortschritt: **{percent}%**\n({synced_gb} von {total_gb} GB)"
                color = 0xFFFF00

            embed = discord.Embed(title="NAS Sync ⏳", description=description, color=color)

            if progress_message is None:
                progress_message = await channel.send(embed=embed)
            else:
                await progress_message.edit(embed=embed)

        except Exception as e:
            print("Fehler beim Lesen der Fortschrittsdatei:", e)

        await asyncio.sleep(UPDATE_INTERVAL)

@client.event
async def on_ready():
    print(f"Bot gestartet als {client.user}")
    client.loop.create_task(update_progress())

client.run(TOKEN)
