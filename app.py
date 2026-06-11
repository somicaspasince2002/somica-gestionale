# -*- coding: utf-8 -*-
from flask import (Flask, render_template, request, redirect,
                   url_for, session, g, jsonify, make_response)
import sqlite3, hashlib, os, json
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = 'somica_gestionale_2026_carbonia'
DB  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db', 'somica.db')

# ─── DB ───────────────────────────────────────────────────────────────────────
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db: db.close()

def init_db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript(open(os.path.join(os.path.dirname(__file__),'schema.sql')).read())
    h = lambda p: hashlib.sha256(p.encode()).hexdigest()
    users = [
        ('Amministratore','Sistema','admin',    h('admin2024'),    'Direzione',        'Amministratore','admin@somica.it',    'admin'),
        ('Ufficio',       'Acquisti','acquisti',h('acquisti2024'), 'Ufficio Acquisti','Resp. Acquisti','acquisti@somica.it', 'ufficio_acquisti'),
        ('Geom. Stefano', 'Carboni','stefano',  h('tecnico2024'),  'Ufficio Tecnico', 'Geometra',      's.carboni@somica.it','richiedente'),
        ('Mario',         'Rossi',  'magazzino',h('magazzino2024'),'Magazzino',       'Magazziniere',  'magazzino@somica.it','richiedente'),
        ('Anna',          'Bianchi','amministrazione',h('amm2024'),'Ufficio Amministrativo','Impiegata','a.bianchi@somica.it','richiedente'),
        ('Direttore',     'Generale','master',  h('master2024'),   'Direzione',       'Direttore',     'dir@somica.it',      'master'),
    ]
    for u in users:
        db.execute("INSERT OR IGNORE INTO utenti (nome,cognome,username,password,ufficio,ruolo,email,livello) VALUES (?,?,?,?,?,?,?,?)", u)
    commesse = [
        ('GS-2024','Global Service 2024','Geom. Carboni','attiva'),
        ('VD-2024','Verde e Diserbo 2024','Geom. Carboni','attiva'),
        ('CIM-2024','Servizi Cimiteriali 2024','Resp. Cimiteri','attiva'),
        ('PUL-2024','Pulizie Edifici 2024','Resp. Pulizie','attiva'),
        ('MAN-2024','Manutenzione Strade 2024','Geom. Carboni','attiva'),
    ]
    for c in commesse:
        db.execute("INSERT OR IGNORE INTO commesse (codice,descrizione,responsabile,stato) VALUES (?,?,?,?)", c)
    articoli = [
        ('MAT-001','Cemento Portland 325','Settore Edile','sacchi'),
        ('MAT-002','Tondino ferro 12','Settore Edile','kg'),
        ('MAT-003','Sabbia fine','Settore Edile','mc'),
        ('MAT-004','Mattoni forati','Settore Edile','cad'),
        ('VRD-001','Erbicida selettivo','Verde e Sfalcio','l'),
        ('VRD-002','Seme misto prato','Verde e Sfalcio','kg'),
        ('VRD-003','Concime NPK','Verde e Sfalcio','kg'),
        ('VRD-004','Paletti recinzione','Verde e Sfalcio','cad'),
        ('SEG-001','Segnale precedenza','Segnaletica','cad'),
        ('SEG-002','Segnale stop','Segnaletica','cad'),
        ('SEG-003','Delineatore stradale','Segnaletica','cad'),
        ('IMP-001','Cavo FG7OR 3x2.5','Impiantistica','m'),
        ('IMP-002','Interruttore bipolare 16A','Impiantistica','cad'),
        ('IMP-003','Tubo PVC rigido 20mm','Impiantistica','m'),
        ('CIM-001','Vaso fiori cimiteriale','Cimiteriale','cad'),
        ('CIM-002','Lapide marmo 60x40','Cimiteriale','cad'),
        ('PUL-001','Detergente multiuso','Pulizie Edifici','l'),
        ('PUL-002','Carta igienica (conf.12)','Pulizie Edifici','conf'),
        ('PUL-003','Guanti monouso (box 100)','Pulizie Edifici','box'),
        ('VAR-001','Materiale vario','Varie','cad'),
    ]
    for a in articoli:
        db.execute("INSERT OR IGNORE INTO articoli (codice,descrizione,categoria,unita_misura) VALUES (?,?,?,?)", a)
    um_list = ['cad','m','mq','mc','kg','l','h','gg','conf','box','sacchi','rotoli','pz','ml']
    for um in um_list:
        db.execute("INSERT OR IGNORE INTO unita_misura (valore) VALUES (?)", (um,))
    db.commit()
    db.close()
    print("✓ Database pronto")

# ─── AUTH ──────────────────────────────────────────────────────────────────────
def login_req(f):
    @wraps(f)
    def dec(*a,**k):
        if 'uid' not in session: return redirect(url_for('login'))
        return f(*a,**k)
    return dec

def staff_req(f):
    @wraps(f)
    def dec(*a,**k):
        if 'uid' not in session: return redirect(url_for('login'))
        if session.get('liv') not in ('admin','master','ufficio_acquisti'):
            return redirect(url_for('dashboard'))
        return f(*a,**k)
    return dec

def utente():
    if 'uid' not in session: return None
    return get_db().execute("SELECT * FROM utenti WHERE id=?", (session['uid'],)).fetchone()

def log(azione, det='', ent='', eid=None):
    try:
        get_db().execute(
            "INSERT INTO log_attivita (utente_id,azione,entita,entita_id,dettaglio,ip) VALUES (?,?,?,?,?,?)",
            (session.get('uid'), azione, ent, eid, det, request.remote_addr))
        get_db().commit()
    except: pass

def num_richiesta():
    anno = datetime.now().year
    n = get_db().execute("SELECT COUNT(*) FROM richieste WHERE strftime('%Y',data)=?", (str(anno),)).fetchone()[0]
    return 'ACQ-%d-%04d' % (anno, n+1)

# ─── LOGIN ─────────────────────────────────────────────────────────────────────
@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    if 'uid' in session: return redirect(url_for('dashboard'))
    err = None
    if request.method == 'POST':
        usr = request.form.get('username','').strip()
        pw  = hashlib.sha256(request.form.get('password','').encode()).hexdigest()
        u   = get_db().execute("SELECT * FROM utenti WHERE username=? AND password=? AND attivo=1",(usr,pw)).fetchone()
        if u:
            session['uid']      = u['id']
            session['nome']     = u['nome']+' '+u['cognome']
            session['liv']      = u['livello']
            session['ufficio']  = u['ufficio']
            session['iniziali'] = (u['nome'][0]+u['cognome'][0]).upper()
            log('login','Accesso effettuato')
            return redirect(url_for('dashboard'))
        err = 'Username o password non corretti.'
    return render_template('login.html', err=err)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── DASHBOARD ─────────────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_req
def dashboard():
    db = get_db(); u = utente()
    is_staff = u['livello'] in ('admin','master','ufficio_acquisti')
    flt = "" if is_staff else "WHERE creato_da=%d" % u['id']
    tot = db.execute(
        "SELECT COUNT(*) t, SUM(stato='bozza') bozze, SUM(stato='inviata') inv,"
        " SUM(stato='in_lavorazione') lav, SUM(stato='chiusa') chi,"
        " SUM(stato='archiviata') arc FROM richieste "+flt).fetchone()
    rec = db.execute(
        "SELECT r.*,u.nome||' '||u.cognome rn FROM richieste r"
        " LEFT JOIN utenti u ON r.creato_da=u.id"
        +(" " if is_staff else " WHERE r.creato_da=%d"%u['id'])+
        " ORDER BY r.creato_il DESC LIMIT 10").fetchall()
    stati = db.execute("SELECT stato,COUNT(*) n FROM richieste "+flt+" GROUP BY stato").fetchall()
    uffici_stat = db.execute("SELECT ufficio_richiedente,COUNT(*) n FROM richieste GROUP BY 1 ORDER BY 2 DESC").fetchall() if is_staff else []
    ulti = db.execute("SELECT l.*,u.nome||' '||u.cognome nu FROM log_attivita l LEFT JOIN utenti u ON l.utente_id=u.id ORDER BY l.quando DESC LIMIT 8").fetchall()
    return render_template('dashboard.html', u=u, tot=tot, rec=rec, stati=stati,
        uffici_stat=uffici_stat, ulti=ulti, is_staff=is_staff,
        oggi=date.today().strftime('%d/%m/%Y'))

# ─── ANAGRAFICHE ───────────────────────────────────────────────────────────────
@app.route('/anagrafiche/utenti')
@login_req
def ana_utenti():
    if session.get('liv') != 'admin': return redirect(url_for('dashboard'))
    rows = [dict(r) for r in get_db().execute("SELECT * FROM utenti ORDER BY cognome").fetchall()]
    return render_template('ana_utenti.html', u=utente(), rows=rows)

@app.route('/anagrafiche/utenti/salva', methods=['POST'])
@login_req
def ana_utenti_salva():
    if session.get('liv') != 'admin': return redirect(url_for('dashboard'))
    db = get_db()
    uid2 = request.form.get('id')
    pw_raw = request.form.get('password','').strip()
    if uid2:
        if pw_raw:
            db.execute("UPDATE utenti SET nome=?,cognome=?,ufficio=?,ruolo=?,email=?,telefono=?,livello=?,password=? WHERE id=?",
                (request.form['nome'],request.form['cognome'],request.form['ufficio'],
                 request.form['ruolo'],request.form.get('email',''),request.form.get('telefono',''),
                 request.form['livello'],hashlib.sha256(pw_raw.encode()).hexdigest(),uid2))
        else:
            db.execute("UPDATE utenti SET nome=?,cognome=?,ufficio=?,ruolo=?,email=?,telefono=?,livello=? WHERE id=?",
                (request.form['nome'],request.form['cognome'],request.form['ufficio'],
                 request.form['ruolo'],request.form.get('email',''),request.form.get('telefono',''),
                 request.form['livello'],uid2))
    else:
        db.execute("INSERT INTO utenti (nome,cognome,username,password,ufficio,ruolo,email,telefono,livello) VALUES (?,?,?,?,?,?,?,?,?)",
            (request.form['nome'],request.form['cognome'],request.form['username'],
             hashlib.sha256(pw_raw.encode()).hexdigest(),request.form['ufficio'],
             request.form['ruolo'],request.form.get('email',''),request.form.get('telefono',''),
             request.form['livello']))
    db.commit()
    return redirect(url_for('ana_utenti'))

@app.route('/anagrafiche/fornitori')
@login_req
def ana_fornitori():
    rows = [dict(r) for r in get_db().execute("SELECT * FROM fornitori WHERE attivo=1 ORDER BY ragione_sociale").fetchall()]
    return render_template('ana_fornitori.html', u=utente(), rows=rows)

@app.route('/anagrafiche/fornitori/salva', methods=['POST'])
@login_req
def ana_fornitori_salva():
    db = get_db()
    fid = request.form.get('id')
    campi = (request.form.get('tipologia',''),request.form.get('ragione_sociale',''),
             request.form.get('indirizzo',''),request.form.get('comune',''),
             request.form.get('provincia',''),request.form.get('cap',''),
             request.form.get('partita_iva',''),request.form.get('codice_fiscale',''),
             request.form.get('pec',''),request.form.get('email',''),
             request.form.get('telefono',''),request.form.get('referente',''))
    if fid:
        db.execute("UPDATE fornitori SET tipologia=?,ragione_sociale=?,indirizzo=?,comune=?,provincia=?,cap=?,partita_iva=?,codice_fiscale=?,pec=?,email=?,telefono=?,referente=? WHERE id=?", campi+(fid,))
    else:
        db.execute("INSERT INTO fornitori (tipologia,ragione_sociale,indirizzo,comune,provincia,cap,partita_iva,codice_fiscale,pec,email,telefono,referente) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", campi)
    db.commit()
    return redirect(url_for('ana_fornitori'))

@app.route('/anagrafiche/fornitori/<int:fid>/elimina', methods=['POST'])
@login_req
def ana_fornitori_elimina(fid):
    get_db().execute("UPDATE fornitori SET attivo=0 WHERE id=?", (fid,)); get_db().commit()
    return redirect(url_for('ana_fornitori'))

@app.route('/api/fornitore/<int:fid>')
@login_req
def api_fornitore(fid):
    f = get_db().execute("SELECT * FROM fornitori WHERE id=?", (fid,)).fetchone()
    if not f: return jsonify({})
    return jsonify(dict(f))

@app.route('/anagrafiche/articoli')
@login_req
def ana_articoli():
    rows = [dict(r) for r in get_db().execute("SELECT * FROM articoli ORDER BY categoria,descrizione").fetchall()]
    return render_template('ana_articoli.html', u=utente(), rows=rows,
        categorie=['Settore Edile','Verde e Sfalcio','Segnaletica','Impiantistica','Cimiteriale','Pulizie Edifici','Varie'])

@app.route('/anagrafiche/articoli/salva', methods=['POST'])
@login_req
def ana_articoli_salva():
    db = get_db()
    aid = request.form.get('id')
    campi = (request.form.get('codice',''),request.form.get('descrizione',''),
             request.form.get('categoria',''),request.form.get('unita_misura',''),
             request.form.get('note',''))
    if aid:
        db.execute("UPDATE articoli SET codice=?,descrizione=?,categoria=?,unita_misura=?,note=? WHERE id=?", campi+(aid,))
    else:
        db.execute("INSERT INTO articoli (codice,descrizione,categoria,unita_misura,note) VALUES (?,?,?,?,?)", campi)
    db.commit()
    return redirect(url_for('ana_articoli'))

@app.route('/anagrafiche/commesse')
@login_req
def ana_commesse():
    rows = [dict(r) for r in get_db().execute("SELECT * FROM commesse ORDER BY codice").fetchall()]
    return render_template('ana_commesse.html', u=utente(), rows=rows)

@app.route('/anagrafiche/commesse/salva', methods=['POST'])
@login_req
def ana_commesse_salva():
    db = get_db(); cid = request.form.get('id')
    campi = (request.form['codice'],request.form['descrizione'],request.form.get('responsabile',''),request.form.get('stato','attiva'))
    if cid: db.execute("UPDATE commesse SET codice=?,descrizione=?,responsabile=?,stato=? WHERE id=?", campi+(cid,))
    else: db.execute("INSERT INTO commesse (codice,descrizione,responsabile,stato) VALUES (?,?,?,?)", campi)
    db.commit(); return redirect(url_for('ana_commesse'))

@app.route('/api/articoli')
@login_req
def api_articoli():
    cat = request.args.get('cat','')
    q = "SELECT * FROM articoli"
    p = []
    if cat: q += " WHERE categoria=?"; p.append(cat)
    q += " ORDER BY descrizione"
    rows = get_db().execute(q,p).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/um')
@login_req
def api_um():
    rows = get_db().execute("SELECT valore FROM unita_misura ORDER BY valore").fetchall()
    return jsonify([r['valore'] for r in rows])

# ─── RICHIESTE DI ACQUISIZIONE ─────────────────────────────────────────────────
@app.route('/richieste')
@login_req
def lista_richieste():
    db = get_db(); u = utente()
    is_staff = u['livello'] in ('admin','master','ufficio_acquisti')
    stato = request.args.get('stato',''); cerca = request.args.get('cerca',''); uff = request.args.get('ufficio','')
    q = "SELECT r.*,ut.nome||' '||ut.cognome rn FROM richieste r LEFT JOIN utenti ut ON r.creato_da=ut.id WHERE 1=1"
    p = []
    if not is_staff: q += " AND r.creato_da=?"; p.append(u['id'])
    if stato: q += " AND r.stato=?"; p.append(stato)
    if uff:   q += " AND r.ufficio_richiedente=?"; p.append(uff)
    if cerca: q += " AND (r.numero LIKE ? OR r.oggetto LIKE ?)"; p += ['%'+cerca+'%','%'+cerca+'%']
    q += " ORDER BY r.creato_il DESC"
    rows = db.execute(q,p).fetchall()
    uffici = db.execute("SELECT DISTINCT ufficio_richiedente FROM richieste ORDER BY 1").fetchall()
    return render_template('lista_richieste.html', u=u, rows=rows, uffici=uffici,
        fs=stato, fu=uff, fc=cerca, is_staff=is_staff)

@app.route('/richieste/nuova', methods=['GET','POST'])
@login_req
def nuova_richiesta():
    db = get_db(); u = utente()
    if u['livello'] not in ('admin','master','richiedente'):
        return redirect(url_for('dashboard'))
    commesse = db.execute("SELECT * FROM commesse WHERE stato='attiva' ORDER BY codice").fetchall()
    articoli = db.execute("SELECT * FROM articoli ORDER BY categoria,descrizione").fetchall()
    utenti_l = db.execute("SELECT * FROM utenti WHERE attivo=1 ORDER BY cognome").fetchall()
    um_list  = db.execute("SELECT valore FROM unita_misura ORDER BY valore").fetchall()
    if request.method == 'POST':
        numero = num_richiesta()
        cur = db.execute(
            "INSERT INTO richieste (numero,data,ufficio_richiedente,referente_id,commessa_id,"
            "tipologia_acquisizione,tipologia_procedimento,oggetto,descrizione,stato,creato_da)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (numero, request.form.get('data',date.today().isoformat()),
             request.form.get('ufficio_richiedente',u['ufficio']),
             request.form.get('referente_id') or None,
             request.form.get('commessa_id') or None,
             request.form.get('tipologia_acquisizione'),
             request.form.get('tipologia_procedimento'),
             request.form.get('oggetto','').strip(),
             request.form.get('descrizione','').strip(),
             'bozza', u['id']))
        rid = cur.lastrowid
        descs=request.form.getlist('desc[]'); ums=request.form.getlist('um[]')
        qtas=request.form.getlist('qta[]'); pris=request.form.getlist('pri[]')
        notes=request.form.getlist('note_riga[]')
        for i,desc in enumerate(descs):
            if not desc.strip(): continue
            try: qta=float(qtas[i]) if i<len(qtas) and qtas[i] else None
            except: qta=None
            try: pri=int(pris[i]) if i<len(pris) and pris[i] else 5
            except: pri=5
            db.execute("INSERT INTO richiesta_articoli (richiesta_id,descrizione,unita_misura,quantita,priorita,note) VALUES (?,?,?,?,?,?)",
                (rid,desc.strip(),ums[i] if i<len(ums) else '',qta,pri,notes[i] if i<len(notes) else ''))
        az = request.form.get('azione','salva')
        if az == 'invia':
            db.execute("UPDATE richieste SET stato='inviata',inviato_il=? WHERE id=?",(datetime.now().isoformat(),rid))
            log('invio','Richiesta '+numero+' inviata','richiesta',rid)
        else:
            log('bozza','Richiesta '+numero+' salvata','richiesta',rid)
        db.commit()
        return redirect(url_for('dettaglio_richiesta', rid=rid))
    num_prev = num_richiesta()
    aj = json.dumps({a['descrizione']:{'um':a['unita_misura'] or '','cat':a['categoria']} for a in articoli}, ensure_ascii=False)
    return render_template('nuova_richiesta.html', u=u, commesse=commesse,
        articoli=articoli, utenti_l=utenti_l, um_list=um_list,
        num_prev=num_prev, aj=aj, oggi=date.today().isoformat(),
        categorie=['Settore Edile','Verde e Sfalcio','Segnaletica','Impiantistica','Cimiteriale','Pulizie Edifici','Varie'])

@app.route('/richieste/<int:rid>')
@login_req
def dettaglio_richiesta(rid):
    db=get_db(); u=utente()
    r = db.execute("SELECT r.*,ut.nome||' '||ut.cognome rn, c.codice cc, c.descrizione cd"
        " FROM richieste r LEFT JOIN utenti ut ON r.creato_da=ut.id"
        " LEFT JOIN commesse c ON r.commessa_id=c.id WHERE r.id=?", (rid,)).fetchone()
    if not r: return redirect(url_for('lista_richieste'))
    arti = db.execute("SELECT * FROM richiesta_articoli WHERE richiesta_id=? ORDER BY id",(rid,)).fetchall()
    return render_template('dettaglio_richiesta.html', u=u, r=r, arti=arti)

@app.route('/richieste/<int:rid>/azione', methods=['POST'])
@login_req
def azione_richiesta(rid):
    db=get_db(); u=utente(); az=request.form.get('azione')
    r=db.execute("SELECT * FROM richieste WHERE id=?",(rid,)).fetchone()
    if not r: return redirect(url_for('lista_richieste'))
    if az=='invia' and r['stato']=='bozza':
        db.execute("UPDATE richieste SET stato='inviata',inviato_il=? WHERE id=?",(datetime.now().isoformat(),rid))
        log('invio','Richiesta '+r['numero']+' inviata','richiesta',rid)
    elif az=='prendi' and r['stato']=='inviata' and u['livello'] in ('admin','master','ufficio_acquisti'):
        db.execute("UPDATE richieste SET stato='in_lavorazione',preso_in_carico_da=? WHERE id=?",(u['id'],rid))
        log('presa_in_carico','Richiesta '+r['numero'],'richiesta',rid)
    elif az=='chiudi' and r['stato']=='in_lavorazione':
        db.execute("UPDATE richieste SET stato='chiusa',chiuso_il=? WHERE id=?",(datetime.now().isoformat(),rid))
        log('chiusura','Richiesta '+r['numero'],'richiesta',rid)
    elif az=='archivia':
        db.execute("UPDATE richieste SET stato='archiviata' WHERE id=?",(rid,))
        log('archiviazione','Richiesta '+r['numero'],'richiesta',rid)
    db.commit()
    return redirect(url_for('dettaglio_richiesta',rid=rid))

@app.route('/richieste/<int:rid>/stampa')
@login_req
def stampa_richiesta(rid):
    db=get_db(); u=utente()
    r=db.execute("SELECT r.*,ut.nome||' '||ut.cognome rn,ut2.nome||' '||ut2.cognome rn2,"
        " c.codice cc,c.descrizione cd"
        " FROM richieste r LEFT JOIN utenti ut ON r.creato_da=ut.id"
        " LEFT JOIN utenti ut2 ON r.referente_id=ut2.id"
        " LEFT JOIN commesse c ON r.commessa_id=c.id WHERE r.id=?",(rid,)).fetchone()
    if not r: return redirect(url_for('lista_richieste'))
    arti=db.execute("SELECT * FROM richiesta_articoli WHERE richiesta_id=? ORDER BY id",(rid,)).fetchall()
    return render_template('stampa_richiesta.html', u=u, r=r, arti=arti,
        oggi=date.today().strftime('%d/%m/%Y'))

# ─── RICHIESTE AI FORNITORI ─────────────────────────────────────────────────────
@app.route('/fornitori/richieste')
@login_req
def lista_rif():
    if session.get('liv') not in ('admin','master','ufficio_acquisti'):
        return redirect(url_for('dashboard'))
    db=get_db(); u=utente()
    cerca=request.args.get('cerca',''); stato=request.args.get('stato','')
    q="SELECT rf.*,f.ragione_sociale fn, u.nome||' '||u.cognome un FROM richieste_fornitori rf LEFT JOIN fornitori f ON rf.fornitore_id=f.id LEFT JOIN utenti u ON rf.creato_da=u.id WHERE 1=1"
    p=[]
    if stato: q+=" AND rf.stato=?"; p.append(stato)
    if cerca: q+=" AND (rf.numero LIKE ? OR rf.oggetto LIKE ?)"; p+=['%'+cerca+'%','%'+cerca+'%']
    q+=" ORDER BY rf.creato_il DESC"
    rows=db.execute(q,p).fetchall()
    richieste_da_prendere=db.execute("SELECT COUNT(*) FROM richieste WHERE stato='inviata'").fetchone()[0]
    return render_template('lista_rif.html', u=u, rows=rows, fc=cerca, fs=stato,
        in_attesa=richieste_da_prendere)

@app.route('/fornitori/richieste/nuova', methods=['GET','POST'])
@login_req
def nuova_rif():
    if session.get('liv') not in ('admin','master','ufficio_acquisti'):
        return redirect(url_for('dashboard'))
    db=get_db(); u=utente()
    fornitori=db.execute("SELECT * FROM fornitori WHERE attivo=1 ORDER BY ragione_sociale").fetchall()
    richieste_acq=db.execute("SELECT * FROM richieste WHERE stato IN ('inviata','in_lavorazione') ORDER BY numero DESC").fetchall()
    rid_src=request.args.get('from_richiesta')
    r_src=None; arti_src=[]
    if rid_src:
        r_src=db.execute("SELECT * FROM richieste WHERE id=?",(rid_src,)).fetchone()
        if r_src: arti_src=db.execute("SELECT * FROM richiesta_articoli WHERE richiesta_id=? ORDER BY id",(rid_src,)).fetchall()
    if request.method=='POST':
        anno=datetime.now().year
        n=db.execute("SELECT COUNT(*) FROM richieste_fornitori WHERE strftime('%Y',data)=?",(str(anno),)).fetchone()[0]
        numero='RIF-%d-%04d'%(anno,n+1)
        cur=db.execute("INSERT INTO richieste_fornitori (numero,data,fornitore_id,tipologia,oggetto,testo_intro,note,stato,creato_da,richiesta_acq_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (numero,request.form.get('data',date.today().isoformat()),
             request.form.get('fornitore_id') or None,
             request.form.get('tipologia'),
             request.form.get('oggetto','').strip(),
             request.form.get('testo_intro',''),
             request.form.get('note',''),
             'bozza',u['id'],
             request.form.get('richiesta_acq_id') or None))
        rfid=cur.lastrowid
        descs=request.form.getlist('desc[]'); ums=request.form.getlist('um[]')
        qtas=request.form.getlist('qta[]'); notes=request.form.getlist('note_riga[]')
        for i,desc in enumerate(descs):
            if not desc.strip(): continue
            try: qta=float(qtas[i]) if i<len(qtas) and qtas[i] else None
            except: qta=None
            db.execute("INSERT INTO rif_articoli (rif_id,descrizione,unita_misura,quantita,note) VALUES (?,?,?,?,?)",
                (rfid,desc.strip(),ums[i] if i<len(ums) else '',qta,notes[i] if i<len(notes) else ''))
        if request.form.get('azione')=='invia':
            db.execute("UPDATE richieste_fornitori SET stato='inviata' WHERE id=?",(rfid,))
        db.commit()
        return redirect(url_for('dettaglio_rif',rfid=rfid))
    um_list=db.execute("SELECT valore FROM unita_misura ORDER BY valore").fetchall()
    return render_template('nuova_rif.html', u=u, fornitori=fornitori,
        richieste_acq=richieste_acq, r_src=r_src, arti_src=arti_src,
        um_list=um_list, oggi=date.today().isoformat())

@app.route('/fornitori/richieste/<int:rfid>')
@login_req
def dettaglio_rif(rfid):
    if session.get('liv') not in ('admin','master','ufficio_acquisti'):
        return redirect(url_for('dashboard'))
    db=get_db(); u=utente()
    rf=db.execute("SELECT rf.*,f.ragione_sociale fn,f.indirizzo fi,f.comune fco,f.provincia fp,"
        "f.partita_iva fpi,f.pec fpec,f.email fe,f.telefono ft,f.referente fr"
        " FROM richieste_fornitori rf LEFT JOIN fornitori f ON rf.fornitore_id=f.id WHERE rf.id=?",(rfid,)).fetchone()
    if not rf: return redirect(url_for('lista_rif'))
    arti=db.execute("SELECT * FROM rif_articoli WHERE rif_id=? ORDER BY id",(rfid,)).fetchall()
    return render_template('dettaglio_rif.html', u=u, rf=rf, arti=arti)

@app.route('/fornitori/richieste/<int:rfid>/stampa')
@login_req
def stampa_rif(rfid):
    if session.get('liv') not in ('admin','master','ufficio_acquisti'):
        return redirect(url_for('dashboard'))
    db=get_db(); u=utente()
    rf=db.execute("SELECT rf.*,f.ragione_sociale fn,f.indirizzo fi,f.comune fco,f.provincia fp,"
        "f.partita_iva fpi,f.pec fpec,f.email fe,f.telefono ft,f.referente fr,f.codice_fiscale fcf"
        " FROM richieste_fornitori rf LEFT JOIN fornitori f ON rf.fornitore_id=f.id WHERE rf.id=?",(rfid,)).fetchone()
    if not rf: return redirect(url_for('lista_rif'))
    arti=db.execute("SELECT * FROM rif_articoli WHERE rif_id=? ORDER BY id",(rfid,)).fetchall()
    return render_template('stampa_rif.html', u=u, rf=rf, arti=arti,
        oggi=date.today().strftime('%d/%m/%Y'))


# ─── MODIFICA RICHIESTA ────────────────────────────────────────────────────────
@app.route('/richieste/<int:rid>/modifica', methods=['GET','POST'])
@login_req
def modifica_richiesta(rid):
    db=get_db(); u=utente()
    r=db.execute("SELECT * FROM richieste WHERE id=?",(rid,)).fetchone()
    if not r: return redirect(url_for('lista_richieste'))
    commesse=db.execute("SELECT * FROM commesse WHERE stato='attiva' ORDER BY codice").fetchall()
    articoli=db.execute("SELECT * FROM articoli ORDER BY categoria,descrizione").fetchall()
    utenti_l=db.execute("SELECT * FROM utenti WHERE attivo=1 ORDER BY cognome").fetchall()
    um_list=db.execute("SELECT valore FROM unita_misura ORDER BY valore").fetchall()
    arti_exist=db.execute("SELECT * FROM richiesta_articoli WHERE richiesta_id=? ORDER BY id",(rid,)).fetchall()
    if request.method=='POST':
        db.execute("UPDATE richieste SET data=?,ufficio_richiedente=?,referente_id=?,commessa_id=?,"
            "tipologia_acquisizione=?,tipologia_procedimento=?,oggetto=?,descrizione=? WHERE id=?",
            (request.form.get('data'),request.form.get('ufficio_richiedente',u['ufficio']),
             request.form.get('referente_id') or None,request.form.get('commessa_id') or None,
             request.form.get('tipologia_acquisizione'),request.form.get('tipologia_procedimento'),
             request.form.get('oggetto','').strip(),request.form.get('descrizione','').strip(),rid))
        db.execute("DELETE FROM richiesta_articoli WHERE richiesta_id=?",(rid,))
        descs=request.form.getlist('desc[]'); ums=request.form.getlist('um[]')
        qtas=request.form.getlist('qta[]'); pris=request.form.getlist('pri[]'); notes=request.form.getlist('note_riga[]')
        for i,desc in enumerate(descs):
            if not desc.strip(): continue
            try: qta=float(qtas[i]) if i<len(qtas) and qtas[i] else None
            except: qta=None
            try: pri=int(pris[i]) if i<len(pris) and pris[i] else 5
            except: pri=5
            db.execute("INSERT INTO richiesta_articoli (richiesta_id,descrizione,unita_misura,quantita,priorita,note) VALUES (?,?,?,?,?,?)",
                (rid,desc.strip(),ums[i] if i<len(ums) else '',qta,pri,notes[i] if i<len(notes) else ''))
        db.commit()
        return redirect(url_for('dettaglio_richiesta',rid=rid))
    anno=datetime.now().year
    n=db.execute("SELECT COUNT(*) FROM richieste WHERE strftime('%Y',data)=?",(str(anno),)).fetchone()[0]
    aj=json.dumps({a['descrizione']:{'um':a['unita_misura'] or '','cat':a['categoria']} for a in articoli},ensure_ascii=False)
    return render_template('nuova_richiesta.html', u=u, commesse=commesse,
        articoli=articoli, utenti_l=utenti_l, um_list=um_list,
        num_prev=r['numero'], aj=aj, oggi=r['data'] or date.today().isoformat(),
        modifica=True, r=r, arti_exist=arti_exist,
        categorie=['Settore Edile','Verde e Sfalcio','Segnaletica','Impiantistica','Cimiteriale','Pulizie Edifici','Varie'])

# ─── MODIFICA RIF ──────────────────────────────────────────────────────────────
@app.route('/fornitori/richieste/<int:rfid>/modifica', methods=['GET','POST'])
@login_req
def modifica_rif(rfid):
    if session.get('liv') not in ('admin','master','ufficio_acquisti'):
        return redirect(url_for('dashboard'))
    db=get_db(); u=utente()
    rf=db.execute("SELECT * FROM richieste_fornitori WHERE id=?",(rfid,)).fetchone()
    if not rf: return redirect(url_for('lista_rif'))
    fornitori=db.execute("SELECT * FROM fornitori WHERE attivo=1 ORDER BY ragione_sociale").fetchall()
    um_list=db.execute("SELECT valore FROM unita_misura ORDER BY valore").fetchall()
    arti_exist=db.execute("SELECT * FROM rif_articoli WHERE rif_id=? ORDER BY id",(rfid,)).fetchall()
    richieste_acq=db.execute("SELECT * FROM richieste WHERE stato IN ('inviata','in_lavorazione') ORDER BY numero DESC").fetchall()
    if request.method=='POST':
        db.execute("UPDATE richieste_fornitori SET data=?,fornitore_id=?,tipologia=?,oggetto=?,testo_intro=?,note=? WHERE id=?",
            (request.form.get('data'),request.form.get('fornitore_id') or None,
             request.form.get('tipologia'),request.form.get('oggetto','').strip(),
             request.form.get('testo_intro',''),request.form.get('note',''),rfid))
        db.execute("DELETE FROM rif_articoli WHERE rif_id=?",(rfid,))
        descs=request.form.getlist('desc[]'); ums=request.form.getlist('um[]')
        qtas=request.form.getlist('qta[]'); notes=request.form.getlist('note_riga[]')
        for i,desc in enumerate(descs):
            if not desc.strip(): continue
            try: qta=float(qtas[i]) if i<len(qtas) and qtas[i] else None
            except: qta=None
            db.execute("INSERT INTO rif_articoli (rif_id,descrizione,unita_misura,quantita,note) VALUES (?,?,?,?,?)",
                (rfid,desc.strip(),ums[i] if i<len(ums) else '',qta,notes[i] if i<len(notes) else ''))
        db.commit()
        return redirect(url_for('dettaglio_rif',rfid=rfid))
    return render_template('nuova_rif.html', u=u, fornitori=fornitori,
        richieste_acq=richieste_acq, r_src=None, arti_src=arti_exist,
        um_list=um_list, oggi=rf['data'] or date.today().isoformat(),
        rf=rf, modifica=True)

# ─── MULTI FORNITORE ───────────────────────────────────────────────────────────
@app.route('/fornitori/richieste/<int:rfid>/multi', methods=['POST'])
@login_req
def duplica_rif_multi(rfid):
    if session.get('liv') not in ('admin','master','ufficio_acquisti'):
        return redirect(url_for('dashboard'))
    db=get_db(); u=utente()
    rf=db.execute("SELECT * FROM richieste_fornitori WHERE id=?",(rfid,)).fetchone()
    if not rf: return redirect(url_for('lista_rif'))
    arti=db.execute("SELECT * FROM rif_articoli WHERE rif_id=? ORDER BY id",(rfid,)).fetchall()
    for i in range(1,6):
        fid=request.form.get('fornitore_'+str(i),'').strip()
        if not fid: continue
        anno=datetime.now().year
        n=db.execute("SELECT COUNT(*) FROM richieste_fornitori WHERE strftime('%Y',data)=?",(str(anno),)).fetchone()[0]
        numero='RIF-%d-%04d'%(anno,n+1)
        cur=db.execute("INSERT INTO richieste_fornitori (numero,data,fornitore_id,tipologia,oggetto,testo_intro,note,stato,creato_da,richiesta_acq_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (numero,rf['data'],fid,rf['tipologia'],rf['oggetto'],rf['testo_intro'],rf['note'],'bozza',u['id'],rf['richiesta_acq_id']))
        new_rfid=cur.lastrowid
        for a in arti:
            db.execute("INSERT INTO rif_articoli (rif_id,descrizione,unita_misura,quantita,note) VALUES (?,?,?,?,?)",
                (new_rfid,a['descrizione'],a['unita_misura'],a['quantita'],a['note']))
        db.commit()
    return redirect(url_for('dettaglio_rif',rfid=rfid))

# ─── ORDINI ────────────────────────────────────────────────────────────────────
@app.route('/ordini')
@login_req
def lista_ordini():
    if session.get('liv') not in ('admin','master','ufficio_acquisti'):
        return redirect(url_for('dashboard'))
    db=get_db(); u=utente()
    cerca=request.args.get('cerca',''); stato=request.args.get('stato','')
    q="SELECT o.*,f.ragione_sociale fn FROM ordini o LEFT JOIN fornitori f ON o.fornitore_id=f.id WHERE 1=1"
    p=[]
    if stato: q+=" AND o.stato=?"; p.append(stato)
    if cerca: q+=" AND (o.numero LIKE ? OR o.oggetto LIKE ?)"; p+=['%'+cerca+'%','%'+cerca+'%']
    q+=" ORDER BY o.creato_il DESC"
    rows=db.execute(q,p).fetchall()
    return render_template('lista_ordini.html', u=u, rows=rows, fc=cerca, fs=stato)

@app.route('/ordini/nuovo', methods=['GET','POST'])
@login_req
def nuovo_ordine():
    if session.get('liv') not in ('admin','master','ufficio_acquisti'):
        return redirect(url_for('dashboard'))
    db=get_db(); u=utente()
    fornitori=db.execute("SELECT * FROM fornitori WHERE attivo=1 ORDER BY ragione_sociale").fetchall()
    commesse=db.execute("SELECT * FROM commesse WHERE stato='attiva' ORDER BY codice").fetchall()
    um_list=db.execute("SELECT valore FROM unita_misura ORDER BY valore").fetchall()
    rif_id=request.args.get('from_rif')
    rf_src=None; arti_src=[]
    if rif_id:
        rf_src=db.execute("SELECT rf.*,f.ragione_sociale fn,f.indirizzo fi,f.comune fco,"
            "f.provincia fp,f.partita_iva fpi,f.pec fpec,f.email fe,f.telefono ft,f.referente fr"
            " FROM richieste_fornitori rf LEFT JOIN fornitori f ON rf.fornitore_id=f.id WHERE rf.id=?",(rif_id,)).fetchone()
        if rf_src: arti_src=db.execute("SELECT * FROM rif_articoli WHERE rif_id=? ORDER BY id",(rif_id,)).fetchall()
    if request.method=='POST':
        anno=datetime.now().year
        n=db.execute("SELECT COUNT(*) FROM ordini WHERE strftime('%Y',data)=?",(str(anno),)).fetchone()[0]
        numero='ORD-%d-%04d'%(anno,n+1)
        cur=db.execute("INSERT INTO ordini (numero,data,rif_id,richiesta_acq_id,fornitore_id,commessa_id,"
            "oggetto,cig,rif_preventivo,durc_ente,durc_data,durc_scadenza,"
            "tempi_consegna,modalita_fatturazione,trasporto_incluso,trasporto_importo,"
            "trasporto_note,note,stato,creato_da) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (numero,request.form.get('data',date.today().isoformat()),
             request.form.get('rif_id') or None,request.form.get('richiesta_acq_id') or None,
             request.form.get('fornitore_id') or None,request.form.get('commessa_id') or None,
             request.form.get('oggetto','').strip(),request.form.get('cig','').strip(),
             request.form.get('rif_preventivo','').strip(),request.form.get('durc_ente','').strip(),
             request.form.get('durc_data','').strip(),request.form.get('durc_scadenza','').strip(),
             request.form.get('tempi_consegna','').strip(),request.form.get('modalita_fatturazione',''),
             1 if request.form.get('trasporto_incluso') else 0,
             float(request.form.get('trasporto_importo',0) or 0),
             request.form.get('trasporto_note','').strip(),request.form.get('note','').strip(),
             'bozza',u['id']))
        oid=cur.lastrowid
        descs=request.form.getlist('desc[]'); ums=request.form.getlist('um[]')
        qtas=request.form.getlist('qta[]'); prezzi=request.form.getlist('prezzo[]'); notes=request.form.getlist('note_riga[]')
        for i,desc in enumerate(descs):
            if not desc.strip(): continue
            try: qta=float(qtas[i]) if i<len(qtas) and qtas[i] else None
            except: qta=None
            try: prezzo=float(prezzi[i]) if i<len(prezzi) and prezzi[i] else None
            except: prezzo=None
            db.execute("INSERT INTO ordini_articoli (ordine_id,descrizione,unita_misura,quantita,prezzo_unitario,note) VALUES (?,?,?,?,?,?)",
                (oid,desc.strip(),ums[i] if i<len(ums) else '',qta,prezzo,notes[i] if i<len(notes) else ''))
        if request.form.get('azione')=='conferma':
            db.execute("UPDATE ordini SET stato='confermato',confermato_il=? WHERE id=?",(datetime.now().isoformat(),oid))
        db.commit()
        return redirect(url_for('dettaglio_ordine',oid=oid))
    anno=datetime.now().year
    n=db.execute("SELECT COUNT(*) FROM ordini WHERE strftime('%Y',data)=?",(str(anno),)).fetchone()[0]
    return render_template('nuovo_ordine.html', u=u, fornitori=fornitori, commesse=commesse,
        um_list=um_list, rf_src=rf_src, arti_src=arti_src,
        numero_prev='ORD-%d-%04d'%(anno,n+1), oggi=date.today().isoformat(),
        modalita_default="Split Payment in base all'art. 17-ter, co.1-bis D.P.R. n. 633/1972 - Cod. destinatario KRRH6B9 - PEC: somica@pec.it",
        o=None, modifica=False)

@app.route('/ordini/<int:oid>/modifica', methods=['GET','POST'])
@login_req
def modifica_ordine(oid):
    if session.get('liv') not in ('admin','master','ufficio_acquisti'):
        return redirect(url_for('dashboard'))
    db=get_db(); u=utente()
    o=db.execute("SELECT * FROM ordini WHERE id=?",(oid,)).fetchone()
    if not o: return redirect(url_for('lista_ordini'))
    fornitori=db.execute("SELECT * FROM fornitori WHERE attivo=1 ORDER BY ragione_sociale").fetchall()
    commesse=db.execute("SELECT * FROM commesse WHERE stato='attiva' ORDER BY codice").fetchall()
    um_list=db.execute("SELECT valore FROM unita_misura ORDER BY valore").fetchall()
    arti_exist=db.execute("SELECT * FROM ordini_articoli WHERE ordine_id=? ORDER BY id",(oid,)).fetchall()
    if request.method=='POST':
        db.execute("UPDATE ordini SET data=?,fornitore_id=?,commessa_id=?,oggetto=?,cig=?,"
            "rif_preventivo=?,durc_ente=?,durc_data=?,durc_scadenza=?,tempi_consegna=?,"
            "modalita_fatturazione=?,trasporto_incluso=?,trasporto_importo=?,trasporto_note=?,note=? WHERE id=?",
            (request.form.get('data'),request.form.get('fornitore_id') or None,
             request.form.get('commessa_id') or None,request.form.get('oggetto','').strip(),
             request.form.get('cig','').strip(),request.form.get('rif_preventivo','').strip(),
             request.form.get('durc_ente','').strip(),request.form.get('durc_data','').strip(),
             request.form.get('durc_scadenza','').strip(),request.form.get('tempi_consegna','').strip(),
             request.form.get('modalita_fatturazione',''),
             1 if request.form.get('trasporto_incluso') else 0,
             float(request.form.get('trasporto_importo',0) or 0),
             request.form.get('trasporto_note','').strip(),request.form.get('note','').strip(),oid))
        db.execute("DELETE FROM ordini_articoli WHERE ordine_id=?",(oid,))
        descs=request.form.getlist('desc[]'); ums=request.form.getlist('um[]')
        qtas=request.form.getlist('qta[]'); prezzi=request.form.getlist('prezzo[]'); notes=request.form.getlist('note_riga[]')
        for i,desc in enumerate(descs):
            if not desc.strip(): continue
            try: qta=float(qtas[i]) if i<len(qtas) and qtas[i] else None
            except: qta=None
            try: prezzo=float(prezzi[i]) if i<len(prezzi) and prezzi[i] else None
            except: prezzo=None
            db.execute("INSERT INTO ordini_articoli (ordine_id,descrizione,unita_misura,quantita,prezzo_unitario,note) VALUES (?,?,?,?,?,?)",
                (oid,desc.strip(),ums[i] if i<len(ums) else '',qta,prezzo,notes[i] if i<len(notes) else ''))
        db.commit()
        return redirect(url_for('dettaglio_ordine',oid=oid))
    return render_template('nuovo_ordine.html', u=u, fornitori=fornitori, commesse=commesse,
        um_list=um_list, rf_src=None, arti_src=arti_exist,
        numero_prev=o['numero'], oggi=o['data'] or date.today().isoformat(),
        modalita_default=o['modalita_fatturazione'] or '',
        o=o, modifica=True)

@app.route('/ordini/<int:oid>')
@login_req
def dettaglio_ordine(oid):
    if session.get('liv') not in ('admin','master','ufficio_acquisti'):
        return redirect(url_for('dashboard'))
    db=get_db(); u=utente()
    o=db.execute("SELECT o.*,f.ragione_sociale fn,f.indirizzo fi,f.comune fco,f.provincia fp,"
        "f.partita_iva fpi,f.pec fpec,f.email fe,f.telefono ft,f.referente fr,f.codice_fiscale fcf,"
        "c.codice cc,c.descrizione cd FROM ordini o"
        " LEFT JOIN fornitori f ON o.fornitore_id=f.id"
        " LEFT JOIN commesse c ON o.commessa_id=c.id WHERE o.id=?",(oid,)).fetchone()
    if not o: return redirect(url_for('lista_ordini'))
    arti=db.execute("SELECT * FROM ordini_articoli WHERE ordine_id=? ORDER BY id",(oid,)).fetchall()
    totale=sum((a['quantita'] or 0)*(a['prezzo_unitario'] or 0) for a in arti)
    trasporto=o['trasporto_importo'] or 0
    totale_finale=totale+(trasporto if o['trasporto_incluso'] else 0)
    return render_template('dettaglio_ordine.html', u=u, o=o, arti=arti,
        totale=totale, trasporto=trasporto, totale_finale=totale_finale)

@app.route('/ordini/<int:oid>/azione', methods=['POST'])
@login_req
def azione_ordine(oid):
    if session.get('liv') not in ('admin','master','ufficio_acquisti'):
        return redirect(url_for('dashboard'))
    db=get_db(); az=request.form.get('azione')
    o=db.execute("SELECT * FROM ordini WHERE id=?",(oid,)).fetchone()
    if not o: return redirect(url_for('lista_ordini'))
    if az=='conferma':
        db.execute("UPDATE ordini SET stato='confermato',confermato_il=? WHERE id=?",(datetime.now().isoformat(),oid))
    elif az=='archivia':
        db.execute("UPDATE ordini SET stato='archiviato' WHERE id=?",(oid,))
    get_db().commit()
    return redirect(url_for('dettaglio_ordine',oid=oid))

@app.route('/ordini/<int:oid>/stampa')
@login_req
def stampa_ordine(oid):
    if session.get('liv') not in ('admin','master','ufficio_acquisti'):
        return redirect(url_for('dashboard'))
    db=get_db(); u=utente()
    o=db.execute("SELECT o.*,f.ragione_sociale fn,f.indirizzo fi,f.comune fco,f.provincia fp,"
        "f.partita_iva fpi,f.pec fpec,f.email fe,f.telefono ft,f.referente fr,f.codice_fiscale fcf,"
        "c.codice cc,c.descrizione cd FROM ordini o"
        " LEFT JOIN fornitori f ON o.fornitore_id=f.id"
        " LEFT JOIN commesse c ON o.commessa_id=c.id WHERE o.id=?",(oid,)).fetchone()
    if not o: return redirect(url_for('lista_ordini'))
    arti=db.execute("SELECT * FROM ordini_articoli WHERE ordine_id=? ORDER BY id",(oid,)).fetchall()
    totale=sum((a['quantita'] or 0)*(a['prezzo_unitario'] or 0) for a in arti)
    trasporto=o['trasporto_importo'] or 0
    totale_finale=totale+(trasporto if o['trasporto_incluso'] else 0)
    return render_template('stampa_ordine.html', u=u, o=o, arti=arti,
        totale=totale, trasporto=trasporto, totale_finale=totale_finale,
        oggi=date.today().strftime('%d/%m/%Y'))

# ─── ELIMINA ANAGRAFICHE ───────────────────────────────────────────────────────
@app.route('/anagrafiche/articoli/<int:aid>/elimina', methods=['POST'])
@login_req
def ana_articoli_elimina(aid):
    get_db().execute("DELETE FROM articoli WHERE id=?",(aid,)); get_db().commit()
    return redirect(url_for('ana_articoli'))

@app.route('/anagrafiche/commesse/<int:cid>/elimina', methods=['POST'])
@login_req
def ana_commesse_elimina(cid):
    get_db().execute("DELETE FROM commesse WHERE id=?",(cid,)); get_db().commit()
    return redirect(url_for('ana_commesse'))

@app.route('/anagrafiche/utenti/<int:uid>/elimina', methods=['POST'])
@login_req
def ana_utenti_elimina(uid):
    if uid==session.get('uid'): return redirect(url_for('ana_utenti'))
    get_db().execute("UPDATE utenti SET attivo=0 WHERE id=?",(uid,)); get_db().commit()
    return redirect(url_for('ana_utenti'))


    init_db()
    print("\n"+"="*54)
    print("  SO.MI.CA. S.p.A. — Gestionale Acquisizioni v3")
    print("  http://localhost:5000")
    print("="*54)
    print("  admin/admin2024  |  acquisti/acquisti2024")
    print("  stefano/tecnico2024  |  master/master2024\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
