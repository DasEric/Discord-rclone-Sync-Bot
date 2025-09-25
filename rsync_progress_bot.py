import discord
import asyncio
import subprocess
import json
import os
import time
from datetime import datetime
import signal

# --- Konfiguration ---
TOKEN = "BOT_TOKEN_HERE"
CHANNEL_ID = CHANNEL_ID_HERE
LOCAL_DIR = "BACKUP_FOLDER_HERE"
REMOTE_NAME = "MyNAS"
REMOTE_DIR = "WHERE_THE_BACKUP_SHOULD_BE_SAVED"
RCLONE_LOG_FILE = "/tmp/rclone_final.log"
UPDATE_INTERVAL = 15
RC_ADDR = "127.0.0.1:5572"

# --- Globale Variablen ---
rcd_process = None
shutdown_signal_received = False

def signal_handler(signum, frame):
    """Handles CTRL+C to allow for graceful shutdown."""
    global shutdown_signal_received
    if not shutdown_signal_received:
        print("\nAbbruch durch Benutzer erkannt. Beende...")
        shutdown_signal_received = True

def get_total_size_bytes():
    try:
        result = subprocess.run(['rclone', 'size', '--json', LOCAL_DIR], capture_output=True, text=True, check=True)
        return int(json.loads(result.stdout).get('bytes', 0))
    except Exception as e:
        print(f"Fehler bei der Größenberechnung: {e}")
        return 0

def bytes_to_gb(b):
    return f"{b / (1024**3):.2f}" if b is not None else "0.00"

def bytes_to_mb_s(b):
    return f"{b / (1024**2):.2f}" if b is not None else "0.00"

class BackupBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backup_task = None
        self.progress_message = None
        self.job_id = None
        self.total_bytes = 0

    async def on_ready(self):
        print(f"Bot gestartet als {self.user}")
        self.backup_task = self.loop.create_task(self.run_backup_and_monitor())

    async def update_discord_message(self, new_embed):
        if not self.progress_message: return
        try:
            await self.progress_message.edit(embed=new_embed)
        except discord.NotFound:
            print("Nachricht nicht gefunden, kann nicht aktualisieren.")
            self.progress_message = None
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Nachricht: {e}")

    async def shutdown_bot(self):
        await self.close()

    async def run_backup_and_monitor(self):
        global shutdown_signal_received
        channel = self.get_channel(CHANNEL_ID)
        if not channel:
            print(f"Kanal mit ID {CHANNEL_ID} nicht gefunden.")
            await self.shutdown_bot()
            return

        self.total_bytes = get_total_size_bytes()
        total_gb = bytes_to_gb(self.total_bytes)
        embed = discord.Embed(title="NAS Sync ⏳", description=f"Fortschritt: **0%**\n(0.00 von {total_gb} GB)", color=0xFFFF00)
        self.progress_message = await channel.send(embed=embed)

        payload = {"srcFs": LOCAL_DIR, "dstFs": f"{REMOTE_NAME}:{REMOTE_DIR}", "_async": True, "checkers": 16, "transfers": 16, "_config": {"LogLevel": "INFO", "Stats": "1s"}}
        
        try:
            start_result = subprocess.run(['rclone', 'rc', f'--rc-addr={RC_ADDR}', 'sync/sync', '--json', json.dumps(payload)], capture_output=True, text=True, check=True)
            self.job_id = json.loads(start_result.stdout).get('jobid')
            if not self.job_id: raise ValueError("Keine Job-ID erhalten.")
            print(f"rclone-Job gestartet mit ID: {self.job_id}")
        except Exception as e:
            desc = f"❌ Backup konnte nicht gestartet werden.\n\n**Fehler:**\n```\n{e}\n{start_result.stderr if 'start_result' in locals() else ''}```"
            await self.update_discord_message(discord.Embed(title="NAS Sync ⏳", description=desc, color=0xFF0000))
            await self.shutdown_bot(); return

        job_data = {}
        while not shutdown_signal_received:
            try:
                job_status_result = subprocess.run(['rclone', 'rc', f'--rc-addr={RC_ADDR}', 'job/status', '--json', json.dumps({"jobid": self.job_id})], capture_output=True, text=True)
                job_data = json.loads(job_status_result.stdout)
                if job_data.get('finished'): break

                stats_result = subprocess.run(['rclone', 'rc', f'--rc-addr={RC_ADDR}', 'core/stats'], capture_output=True, text=True)
                stats_data = json.loads(stats_result.stdout)
                
                synced_bytes = stats_data.get('bytes', 0)
                percent = int((synced_bytes * 100.0) / self.total_bytes) if self.total_bytes > 0 else 0
                synced_gb = bytes_to_gb(synced_bytes)
                speed_mbs = bytes_to_mb_s(stats_data.get('speed'))
                
                desc = f"Fortschritt: **{percent}%**\n({synced_gb} von {total_gb} GB)\nGeschwindigkeit: {speed_mbs} MB/s"
                await self.update_discord_message(discord.Embed(title="NAS Sync ⏳", description=desc, color=0xFFFF00))
                
                await asyncio.sleep(UPDATE_INTERVAL)
            except Exception as e:
                print(f"Fehler in der Überwachungsschleife: {e}")
                await asyncio.sleep(UPDATE_INTERVAL)

        if shutdown_signal_received:
            desc = "Backup Sync wurde Manuell Abgebrochen ❌"
            color = 0xFF0000
            subprocess.run(['rclone', 'rc', f'--rc-addr={RC_ADDR}', 'job/stop', '--json', json.dumps({"jobid": self.job_id})])
        else:
            error = job_data.get('error', '')
            if error:
                desc = f"❌ Backup fehlgeschlagen.\n\n**Fehler:**\n```\n{error}```"
                color = 0xFF0000
            else:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                desc = f"✅ Das Backup wurde Erfolgreich auf dem NAS Gespeichert\n*Abgeschlossen am: {timestamp}*"
                color = 0x00FF00
        
        await self.update_discord_message(discord.Embed(title="NAS Sync ⏳", description=desc, color=color))
        await self.shutdown_bot()

def main():
    global rcd_process
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    subprocess.run(['pkill', '-f', 'rclone rcd'], check=False)
    time.sleep(1)
    
    rcd_process = subprocess.Popen(['rclone', 'rcd', '--rc-no-auth', f'--rc-addr={RC_ADDR}'])
    time.sleep(2)
    
    intents = discord.Intents.default()
    bot = BackupBot(intents=intents)
    
    try:
        bot.run(TOKEN)
    finally:
        print("Beende rclone RC-Daemon...")
        rcd_process.terminate()
        rcd_process.wait()

if __name__ == "__main__":
    main()
