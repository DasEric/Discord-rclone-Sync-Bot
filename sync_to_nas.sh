#!/bin/bash
# Skript: sync_to_nas.sh
# Zweck: Sync von /merp-backups nach Synology NAS mit Fortschritt

LOCAL_DIR="/merp-backups"
NAS_USER="Midnight"
NAS_HOST="mikev2-2103.synology.me"
NAS_PORT="6969"
SSH_KEY="/root/.ssh/merp_backup_key"
NAS_DIR="/volume1/Karstens-Daten/Midnight/Backups"
PROGRESS_FILE="/tmp/rsync_progress.txt"

# --- Gesamtgröße der Dateien berechnen ---
TOTAL_BYTES=$(find "$LOCAL_DIR" -type f -exec stat -c%s {} \; | awk '{s+=$1} END {print s}')
echo "START,0,$TOTAL_BYTES" > "$PROGRESS_FILE"

# --- Rsync mit Fortschritt in Bytes ---
SYNCED_BYTES=0
LAST_UPDATE=$(date +%s)

rsync -avz --no-perms --no-owner --no-group \
--progress \
-e "ssh -q -p $NAS_PORT -i $SSH_KEY" \
"$LOCAL_DIR/" "$NAS_USER@$NAS_HOST:$NAS_DIR/" | while read -r line; do
    # Zeilen mit "to-check" ignorieren, wir nehmen "bytes" aus progress output
    if [[ "$line" =~ ([0-9]+)bytes ]]; then
        # Extrahiere Bytes übertragen
        BYTES=${BASH_REMATCH[1]}
        SYNCED_BYTES=$BYTES
        PERCENT=$((SYNCED_BYTES * 100 / TOTAL_BYTES))
        NOW=$(date +%s)
        if (( NOW - LAST_UPDATE >= 60 )); then
            echo "$PERCENT,$SYNCED_BYTES,$TOTAL_BYTES" > "$PROGRESS_FILE"
            LAST_UPDATE=$NOW
        fi
    fi
done

# --- Ergebnis prüfen ---
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    ssh -q -p $NAS_PORT -i $SSH_KEY "$NAS_USER@$NAS_HOST" "
        find \"$NAS_DIR\" -type f -name 'MidnightBackup*.zip' -mtime +3 -delete
        find \"$NAS_DIR\" -type f -name 'MidnightBackup*.sql' -mtime +7 -delete
    "
    echo "SUCCESS,$TOTAL_BYTES,$TOTAL_BYTES" > "$PROGRESS_FILE"
else
    echo "FAIL,$SYNCED_BYTES,$TOTAL_BYTES" > "$PROGRESS_FILE"
fi
