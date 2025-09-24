#!/bin/bash
# backup_start.sh
# Startet den Discord-Bot aus der venv und das Backup-Skript automatisch

# Pfad zur virtuellen Umgebung
VENV_PATH="/root/rsync_bot_venv"

# Virtuelle Umgebung aktivieren
source "$VENV_PATH/bin/activate"

# Discord-Bot starten (im Hintergrund)
BOT_SCRIPT="$VENV_PATH/rsync_progress_bot.py"
"$VENV_PATH/bin/python" "$BOT_SCRIPT" &
BOT_PID=$!
echo "Discord-Bot gestartet (PID $BOT_PID)"

# Backup-Skript starten (im Home-Verzeichnis)
BACKUP_SCRIPT="/home/sync_to_nas.sh"
"$BACKUP_SCRIPT"

# Bot beenden, wenn Backup fertig ist
kill $BOT_PID
echo "Discord-Bot beendet"
