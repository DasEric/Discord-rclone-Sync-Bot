#!/bin/bash
# Skript: sync_to_nas.sh (WebDAV version, v3)
# Zweck: Sync von /merp-backups nach Synology NAS mit rclone und WebDAV

LOCAL_DIR="/merp-backups"
REMOTE_NAME="MyNAS"
REMOTE_DIR="/Karstens-Daten/Midnight/Backups"
PROGRESS_FILE="/tmp/rsync_progress.txt"
RCLONE_LOG_FILE="/tmp/rclone_log.json"

# --- Startnachricht für den Bot ---
echo "START,0,1" > "$PROGRESS_FILE"

# --- rclone ausführen und Log speichern ---
# Führe rclone aus und speichere den gesamten JSON-Output in einer Log-Datei.
# Der Exit-Code wird zur späteren Überprüfung gespeichert.
rclone sync "$LOCAL_DIR" "$REMOTE_NAME:$REMOTE_DIR" --progress --use-json-log --log-level INFO > "$RCLONE_LOG_FILE" 2>&1
RCLONE_EXIT_CODE=$?

# --- Log-Datei verarbeiten, um den Bot zu aktualisieren ---
# Lese die gespeicherte Log-Datei Zeile für Zeile.
while read -r line; do
    if echo "$line" | grep -q '"stats"'; then
        BYTES=$(echo "$line" | grep -o '"bytes":[0-9]*' | cut -d':' -f2)
        TOTAL_BYTES=$(echo "$line" | grep -o '"totalBytes":[0-9]*' | cut -d':' -f2)

        if [ -n "$BYTES" ] && [ -n "$TOTAL_BYTES" ]; then
            # Schreibe den Fortschritt in die Datei, die der Bot liest.
            echo "PROGRESS,$BYTES,$TOTAL_BYTES" > "$PROGRESS_FILE"
            # Eine kleine Pause, damit der Bot die Änderung auch wirklich mitbekommt.
            sleep 0.1
        fi
    fi
done < "$RCLONE_LOG_FILE"

# --- Endergebnis prüfen und schreiben ---
if [ $RCLONE_EXIT_CODE -eq 0 ]; then
    # Bei Erfolg die letzte bekannte Gesamtgröße für die 100%-Anzeige verwenden.
    FINAL_TOTAL_BYTES=$(tail -n1 "$PROGRESS_FILE" | cut -d',' -f3)
    if [ -z "$FINAL_TOTAL_BYTES" ] || [ "$FINAL_TOTAL_BYTES" -eq 1 ]; then
        # Falls keine Dateien übertragen wurden, berechne die Größe manuell.
        FINAL_TOTAL_BYTES=$(rclone size --json "$LOCAL_DIR" | grep -o '"bytes":[0-9]*' | cut -d':' -f2)
    fi
    echo "SUCCESS,$FINAL_TOTAL_BYTES,$FINAL_TOTAL_BYTES" > "$PROGRESS_FILE"
else
    # Bei einem Fehler die letzte bekannte Information verwenden.
    FINAL_TOTAL_BYTES=$(tail -n1 "$PROGRESS_FILE" | cut -d',' -f3)
    FINAL_SYNCED_BYTES=$(tail -n1 "$PROGRESS_FILE" | cut -d',' -f2)
    echo "FAIL,$FINAL_SYNCED_BYTES,$FINAL_TOTAL_BYTES" > "$PROGRESS_FILE"
fi

# --- Eine letzte Pause, um sicherzustellen, dass der Bot die finale Nachricht liest ---
sleep 3