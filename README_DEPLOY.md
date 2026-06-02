# SO.MI.CA. S.p.A. — Gestionale Acquisizioni
## Guida completa: Deploy online + Installazione PC

---

## PARTE 1 — Mettere online su Railway (una volta sola)

### Passo 1 — GitHub
1. Vai su github.com → Sign up (crea account gratuito)
2. Clicca **+** → **New repository**
3. Nome: `somica-gestionale` → **Create repository**
4. Clicca **uploading an existing file**
5. Trascina TUTTI i file di questa cartella (non la cartella, i file dentro)
6. Clicca **Commit changes**

### Passo 2 — Railway
1. Vai su railway.app → **Login with GitHub**
2. **New Project** → **Deploy from GitHub repo**
3. Seleziona `somica-gestionale`
4. Aspetta 2-3 minuti che finisca il deploy
5. Vai su **Settings** → **Networking** → **Generate Domain**
6. Ottieni il tuo link tipo: `somica-gestionale.up.railway.app`

### Passo 3 — Aggiorna l'URL nel launcher
Apri `launcher.py` con Notepad e cambia la riga:
```
SERVER_URL = "https://somica-gestionale.up.railway.app"
```
con il tuo URL reale di Railway.

---

## PARTE 2 — Installare sui PC aziendali

### Metodo A — Con EXE compilato (consigliato)
1. Su UN solo PC, esegui `COMPILA_EXE.bat`
2. Viene creato `dist\SoMiCa_Gestionale.exe`
3. Copia l'exe nella cartella principale (insieme agli altri file)
4. Su ogni PC da installare:
   - Copia l'intera cartella su `C:\SoMiCa\`
   - Tasto destro su `INSTALLA.ps1` → **Esegui con PowerShell**
   - Appare l'icona sul Desktop!

### Metodo B — Con Python (più semplice)
1. Installa Python da python.org su ogni PC
2. Copia la cartella su ogni PC
3. Esegui `INSTALLA.ps1` con PowerShell
4. L'icona sul Desktop aprirà il launcher

---

## Credenziali predefinite
| Username  | Password     | Livello           |
|-----------|--------------|-------------------|
| admin     | admin2024    | Amministratore    |
| master    | master2024   | Master            |
| acquisti  | acquisti2024 | Ufficio Acquisti  |
| stefano   | tecnico2024  | Richiedente       |

⚠️ **Cambia le password dopo il primo accesso!**

---

## Come funziona
- Il **database** vive sul server Railway — tutti condividono gli stessi dati
- Il **launcher** sul PC apre semplicemente il browser sull'URL del server
- Funziona da **qualsiasi PC, tablet o smartphone** con browser
- Se il server cloud non è raggiungibile, prova il server locale (se avviato)
- 
