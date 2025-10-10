# LaserCare Italia

Sito vetrina professionale per i servizi di riparazione e manutenzione di sorgenti laser per macchine da taglio industriali.

## Struttura

- `index.html`: home page con panoramica servizi, vantaggi, incentivi, FAQ e contatti.
- `servizi/riparazione-sorgenti-laser.html`: dettaglio dei servizi di riparazione e taratura.
- `blog/`: articoli ottimizzati SEO su manutenzione e incentivi.
- `assets/css/style.css`: stile responsive moderno.
- `assets/js/main.js`: script per menu mobile e aggiornamento copyright.

## SEO

- Meta title e description personalizzati per ogni pagina.
- Keyword principali: "riparazione sorgenti laser", "assistenza sorgenti laser fibra", "manutenzione laser macchine da taglio".
- Schema Markup JSON-LD per servizi professionali e pagina servizi.

## Come usare

Apri `index.html` in un browser per visualizzare il sito. I link navigano fra le varie sezioni e pagine informative.

## Raybox GUI

Il file `raybox_gui.py` contiene l'interfaccia grafica aggiornata per gestire Raybox.

### Come scaricarla su Windows

1. Installa [Python 3.10 o superiore](https://www.python.org/downloads/windows/) assicurandoti di selezionare l'opzione **Add Python to PATH**.
2. Scarica il progetto:
   - Dal browser: clicca sul pulsante verde **Code** in alto a destra e scegli **Download ZIP**. Estrai l'archivio in una cartella, ad esempio `C:\RayboxGUI`.
   - Oppure, se hai Git installato: `git clone https://github.com/<tuo-utente>/<nome-repo>.git`
3. Apri il Prompt dei comandi nella cartella dove hai salvato i file (es. `cd C:\RayboxGUI`).
4. Installa le dipendenze richieste: `pip install requests` (aggiungi `openpyxl` se vuoi l'esportazione Excel).
5. Avvia l'applicazione con `python raybox_gui.py`.

### Creare l'eseguibile Windows

Per distribuire il programma come `.exe` eseguibile:

1. Assicurati di essere su Windows e di aver installato le dipendenze precedenti.
2. Installa PyInstaller: `pip install pyinstaller`.
3. Esegui `python build_exe.py` dalla cartella del progetto.
4. Al termine troverai `RayboxControlCenter.exe` dentro `dist/` pronto per essere copiato sui PC dei clienti.

Lo storico dei task viene salvato nella cartella `%APPDATA%\RayboxControlCenter` (su Linux/macOS in `~/.config/RayboxControlCenter`).
