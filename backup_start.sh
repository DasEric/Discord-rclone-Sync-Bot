#!/bin/bash
# backup_start.sh (Final, Simplified)
# Manages the all-in-one Python backup bot.

# --- Konfiguration ---
# Pfad zur virtuellen Umgebung, falls Sie eine verwenden
VENV_PATH="/root/rsync_bot_venv" 
# Der Name des neuen, einzelnen Python-Skripts
BOT_SCRIPT_NAME="backup_bot.py"
# Der vollständige Pfad zum Skript
BOT_SCRIPT_PATH="/home/$BOT_SCRIPT_NAME"


# --- 1. Alte Prozesse beenden ---
# Stellt sicher, dass keine alten Instanzen des Skripts oder von rclone laufen.
echo "Bereinige alte Prozesse..."
pkill -f "python $BOT_SCRIPT_PATH" || true
pkill -f "rclone rcd" || true
# Eine kurze Pause, um sicherzustellen, dass die Prozesse beendet sind.
sleep 1


# --- 2. Das Hauptskript ausführen ---
echo "Starte den Backup-Bot..."
# Aktiviert die virtuelle Umgebung und startet das Python-Skript.
source "$VENV_PATH/bin/activate"
"$VENV_PATH/bin/python" "$BOT_SCRIPT_PATH"

echo "Skript beendet."
