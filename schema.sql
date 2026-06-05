CREATE TABLE IF NOT EXISTS utenti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL, cognome TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
    ufficio TEXT NOT NULL, ruolo TEXT NOT NULL,
    email TEXT, telefono TEXT,
    livello TEXT NOT NULL DEFAULT 'richiedente',
    attivo INTEGER DEFAULT 1,
    creato_il TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS fornitori (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipologia TEXT, ragione_sociale TEXT NOT NULL,
    indirizzo TEXT, comune TEXT, provincia TEXT, cap TEXT,
    partita_iva TEXT, codice_fiscale TEXT, pec TEXT,
    email TEXT, telefono TEXT, referente TEXT,
    attivo INTEGER DEFAULT 1,
    creato_il TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS commesse (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codice TEXT UNIQUE NOT NULL, descrizione TEXT NOT NULL,
    responsabile TEXT, stato TEXT DEFAULT 'attiva'
);
CREATE TABLE IF NOT EXISTS articoli (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codice TEXT, descrizione TEXT NOT NULL,
    categoria TEXT, unita_misura TEXT, note TEXT
);
CREATE TABLE IF NOT EXISTS unita_misura (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    valore TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS richieste (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT UNIQUE NOT NULL, data TEXT NOT NULL,
    ufficio_richiedente TEXT NOT NULL,
    referente_id INTEGER, commessa_id INTEGER,
    tipologia_acquisizione TEXT, tipologia_procedimento TEXT,
    oggetto TEXT NOT NULL, descrizione TEXT,
    stato TEXT DEFAULT 'bozza',
    creato_da INTEGER, creato_il TEXT DEFAULT CURRENT_TIMESTAMP,
    inviato_il TEXT, preso_in_carico_da INTEGER,
    chiuso_il TEXT, note_interne TEXT
);
CREATE TABLE IF NOT EXISTS richiesta_articoli (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    richiesta_id INTEGER NOT NULL, descrizione TEXT NOT NULL,
    unita_misura TEXT, quantita REAL, priorita INTEGER DEFAULT 5, note TEXT
);
CREATE TABLE IF NOT EXISTS richieste_fornitori (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT UNIQUE NOT NULL, data TEXT NOT NULL,
    fornitore_id INTEGER, tipologia TEXT,
    oggetto TEXT NOT NULL, testo_intro TEXT, note TEXT,
    stato TEXT DEFAULT 'bozza',
    creato_da INTEGER, richiesta_acq_id INTEGER,
    creato_il TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS rif_articoli (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rif_id INTEGER NOT NULL, descrizione TEXT NOT NULL,
    unita_misura TEXT, quantita REAL, note TEXT
);
CREATE TABLE IF NOT EXISTS log_attivita (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    utente_id INTEGER, azione TEXT, entita TEXT,
    entita_id INTEGER, dettaglio TEXT, ip TEXT,
    quando TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ordini (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT UNIQUE NOT NULL,
    data TEXT NOT NULL,
    rif_id INTEGER,
    richiesta_acq_id INTEGER,
    fornitore_id INTEGER,
    commessa_id INTEGER,
    oggetto TEXT NOT NULL,
    cig TEXT,
    rif_preventivo TEXT,
    durc_ente TEXT,
    durc_data TEXT,
    durc_scadenza TEXT,
    split_payment INTEGER DEFAULT 1,
    tempi_consegna TEXT,
    modalita_fatturazione TEXT DEFAULT 'Split Payment art. 17-ter co.1-bis D.P.R. 633/1972 - Cod. destinatario KRRH6B9 - PEC: somica@pec.it',
    trasporto_incluso INTEGER DEFAULT 0,
    trasporto_importo REAL DEFAULT 0,
    trasporto_note TEXT,
    note TEXT,
    stato TEXT DEFAULT 'bozza',
    creato_da INTEGER,
    creato_il TEXT DEFAULT CURRENT_TIMESTAMP,
    confermato_il TEXT
);

CREATE TABLE IF NOT EXISTS ordini_articoli (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ordine_id INTEGER NOT NULL,
    descrizione TEXT NOT NULL,
    unita_misura TEXT,
    quantita REAL,
    prezzo_unitario REAL,
    note TEXT
);
