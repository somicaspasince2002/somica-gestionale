"""
SO.MI.CA. S.p.A. - Gestionale Acquisizioni
Launcher: apre il browser sul server cloud
"""
import sys
import os
import webbrowser
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import urllib.error

# URL del server cloud — verrà aggiornato dopo il deploy su Railway
SERVER_URL = "https://somica-gestionale.up.railway.app"

# Fallback locale se il server non è raggiungibile
LOCAL_URL = "http://localhost:5000"

class SomicaLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SO.MI.CA. S.p.A. — Gestionale Acquisizioni")
        self.root.geometry("420x220")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f1b2d")

        # Icona
        ico_path = os.path.join(os.path.dirname(sys.executable if getattr(sys,'frozen',False) else __file__), 'static','img','icon.ico')
        try:
            self.root.iconbitmap(ico_path)
        except:
            pass

        # Centra la finestra
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 420) // 2
        y = (self.root.winfo_screenheight() - 220) // 2
        self.root.geometry(f"420x220+{x}+{y}")

        self._build_ui()
        self.root.after(500, self._avvia)
        self.root.mainloop()

    def _build_ui(self):
        # Logo testuale
        tk.Label(self.root, text="SO.MI.CA. S.p.A.",
                 font=("Arial", 18, "bold"), fg="#ffffff", bg="#0f1b2d").pack(pady=(24,2))
        tk.Label(self.root, text="Gestionale Richieste di Acquisizione",
                 font=("Arial", 10), fg="#94a3b8", bg="#0f1b2d").pack()

        # Separatore
        tk.Frame(self.root, bg="#1a3a6b", height=1).pack(fill="x", padx=30, pady=14)

        # Stato
        self.lbl_stato = tk.Label(self.root, text="Connessione al server in corso...",
                                   font=("Arial", 9), fg="#94a3b8", bg="#0f1b2d")
        self.lbl_stato.pack()

        # Barra progresso
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("blu.Horizontal.TProgressbar",
                        troughcolor="#1a2a3a", background="#2952a3", bordercolor="#0f1b2d")
        self.pb = ttk.Progressbar(self.root, style="blu.Horizontal.TProgressbar",
                                   orient="horizontal", length=340, mode="indeterminate")
        self.pb.pack(pady=10)
        self.pb.start(12)

        # Footer
        tk.Label(self.root, text="Carbonia (SU) — D.Lgs. 36/2023",
                 font=("Arial", 8), fg="#334466", bg="#0f1b2d").pack(side="bottom", pady=8)

    def _avvia(self):
        threading.Thread(target=self._controlla_server, daemon=True).start()

    def _controlla_server(self):
        # Prova il server cloud
        for tentativo in range(3):
            try:
                self._set_stato(f"Connessione al server... (tentativo {tentativo+1}/3)")
                req = urllib.request.urlopen(SERVER_URL, timeout=8)
                if req.status == 200:
                    self._apri_browser(SERVER_URL)
                    return
            except Exception as e:
                time.sleep(1)

        # Fallback: prova server locale
        self._set_stato("Server cloud non raggiungibile. Provo locale...")
        try:
            req = urllib.request.urlopen(LOCAL_URL, timeout=3)
            if req.status == 200:
                self._apri_browser(LOCAL_URL)
                return
        except:
            pass

        # Nessun server disponibile
        self.root.after(0, self._errore_connessione)

    def _apri_browser(self, url):
        self._set_stato(f"Apertura in corso...")
        time.sleep(0.5)
        webbrowser.open(url)
        self.root.after(1500, self.root.destroy)

    def _set_stato(self, testo):
        self.root.after(0, lambda: self.lbl_stato.config(text=testo))

    def _errore_connessione(self):
        self.pb.stop()
        self.lbl_stato.config(text="⚠ Impossibile connettersi al server", fg="#ff6b6b")
        messagebox.showerror(
            "Errore di connessione",
            "Impossibile raggiungere il server.\n\n"
            "Verifica:\n"
            "• La connessione internet\n"
            "• Che il server Railway sia attivo\n\n"
            f"URL server: {SERVER_URL}"
        )
        self.root.destroy()

if __name__ == "__main__":
    SomicaLauncher()
