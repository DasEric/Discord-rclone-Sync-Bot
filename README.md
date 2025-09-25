# Rclone Discord Backup Bot

Dieses Projekt verwendet ein einziges Python-Skript, um einen `rclone`-Backup-Prozess zu verwalten und den Fortschritt in Echtzeit an einen Discord-Kanal zu senden. Falls etwas nicht Funktioniert einfach bescheid geben es wird sich dann darum gekümmert.

## BITTE BEACHTEN
**Ich habe rclone mit WebDAV Konfiguriert ich weiß nicht ob der Bot auch mit einer anderen rclone Konfiguration funktioniert**

## Funktionsweise

Das System besteht aus einem einzigen Python-Skript, `backup_bot.py`, das alle Aspekte des Prozesses steuert:

1.  **Startet einen `rclone` RC (Remote Control) Daemon:** Dies ermöglicht die programmatische Steuerung von `rclone`.
2.  **Startet einen Discord-Bot:** Der Bot meldet sich bei Discord an.
3.  **Startet den Backup-Job:** Das Skript sendet einen API-Aufruf an den `rclone`-Daemon, um den `sync`-Vorgang zu starten.
4.  **Überwacht den Fortschritt:** In einer Schleife fragt das Skript alle 15 Sekunden den `rclone`-API-Endpunkt `core/stats` ab, um den aktuellen Fortschritt (übertragene Bytes, Geschwindigkeit) zu erhalten.
5.  **Aktualisiert Discord:** Es aktualisiert eine einzelne Nachricht in einem bestimmten Discord-Kanal mit dem prozentualen Fortschritt, der übertragenen Datenmenge und der aktuellen Geschwindigkeit in MB/s.
6.  **Behandelt das Ende:** Wenn der Job abgeschlossen ist, wird die Nachricht mit einer Erfolgs- oder Fehlermeldung aktualisiert.
7.  **Graceful Shutdown:** Das Skript kann jederzeit mit `CTRL+C` beendet werden. Es fängt das Signal ab, sendet eine "Manuell Abgebrochen"-Nachricht an Discord und beendet alle Hintergrundprozesse sauber.

## Anforderungen

- **Python 3.8+**
- **pip** (Python-Paket-Installer)
- **rclone**: Muss installiert und konfiguriert sein. Der Remote-Name (z.B. `MyNAS`) muss in Ihrer `rclone.conf` existieren.
- **jq**: Ein Kommandozeilen-JSON-Prozessor auf Debian/Ubuntu.
- **bc**: Ein Kommandozeilen-Taschenrechner auf Debian/Ubuntu.

## Setup

## Setup

1.  **Python-Bibliotheken installieren:**
    ```bash
    pip install discord.py
    ```
    
2. **Packete Installieren:**
    **jq**: Ein Kommandozeilen-JSON-Prozessor auf Debian/Ubuntu. 
    ```bash
    sudo apt-get install jq
    ```
    **bc**: Ein Kommandozeilen-Taschenrechner auf Debian/Ubuntu. 
    ```bash
    sudo apt-get install bc
    ```

3.  **Skript konfigurieren:**
    Öffnen Sie die Datei `backup_bot.py` und passen Sie die folgenden Variablen im Konfigurationsbereich am Anfang der Datei an:
    - `TOKEN`: Ihr Discord-Bot-Token. **BEHANDELN SIE DIESES WIE EIN PASSWORT!**
    - `CHANNEL_ID`: Die ID des Discord-Kanals, in den die Nachrichten gesendet werden sollen.
    - `LOCAL_DIR`: Das lokale Verzeichnis, das gesichert werden soll.
    - `REMOTE_NAME`: Der Name Ihres `rclone`-Remotes (z.B. "MyNAS").
    - `REMOTE_DIR`: Das Zielverzeichnis auf Ihrem Remote.

## Ausführung

Um den Backup-Prozess und den Bot zu starten, führen Sie einfach das Skript direkt aus:

```bash
./backup_start.sh
```

Das Skript kümmert sich um das Beenden alter Prozesse, das Starten des `rclone`-Daemons und die gesamte Berichterstattung.

Um den Prozess zu stoppen, drücken Sie `CTRL+C` im Terminal, in dem Sie das Skript gestartet haben.
