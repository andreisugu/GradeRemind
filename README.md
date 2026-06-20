# 🎓 GradeRemind

> **Monitorizare automată a notelor pe portaluri academice**, cu notificări Discord și un dashboard web modern.

---

## 📋 Cuprins

- [Despre proiect](#-despre-proiect)
- [Funcționalități](#-funcționalități)
- [Cerințe prealabile](#-cerințe-prealabile)
- [Instalare](#-instalare)
- [Configurare](#-configurare)
- [Utilizare](#-utilizare)
- [Docker](#-docker)
- [Pterodactyl / Pelican Panel](#-pterodactyl--pelican-panel)
- [Arhitectură](#-arhitectură)
- [Dashboard Web](#-dashboard-web)
- [Rularea testelor](#-rularea-testelor)
- [Contribuții](#-contribuții)

---

## 📖 Despre proiect

**GradeRemind** este un bot Python care se conectează automat la un portal academic de tip student (configurat prin `PORTAL_BASE_URL`), extrage notele și te notifică instant pe Discord de fiecare dată când apare o notă nouă sau o notă este modificată.

Aplicația include și un **dashboard web local** cu autentificare, unde poți vizualiza toate notele organizate pe ani și semestre, cu un cronometru în timp real pentru următoarea verificare automată.

---

## ✨ Funcționalități

| Funcționalitate | Detalii |
|---|---|
| 🔄 **Monitorizare automată** | Verificări periodice la intervale aleatoare configurabile |
| 🔔 **Notificări Discord** | Webhook instant la modificarea sau adăugarea oricărei note |
| 📢 **Notificări browser** | Push notifications native direct în browser (Web Notification API) |
| 🌐 **Dashboard web** | Interfață vizuală premium cu statistici și cronometru live |
| 🔐 **Autentificare** | Protecție cu sesiune persistentă (7 zile) și buton de delogare |
| 🕐 **Ore active** | Monitorizarea poate fi limitată la un interval orar configurat |
| ⚡ **Verificare manuală** | Buton în dashboard pentru a declanșa o verificare imediată |
| 💾 **Persistență locală** | Istoricul notelor salvat în JSON, cu detectarea automată a formatelor vechi |
| 📝 **Log de activitate** | Jurnal complet al tuturor verificărilor în fișier text |
| 🛡️ **Thread-safe** | Verificările manuale și automate coexistă fără a bloca interfața web |

---

## 🔧 Cerințe prealabile

- **Python 3.8+**
- Un cont activ pe portalul academic țintă
- *(Opțional)* Un webhook Discord pentru notificări

### Cerințe de resurse (RAM)
GradeRemind este o aplicație extrem de ușoară și eficientă, având un consum neglijabil de memorie:
- **Rulare nativă (pe calculator/server):** ~30 – 45 MB RAM.
- **Docker (utilizare directă):** ~35 – 50 MB RAM.
- **Pterodactyl / Pelican Panel:** Se recomandă alocarea a **128 MB RAM** pentru funcționarea stabilă. *Notă importantă:* În timpul instalării sau reinstalării, managerul de pachete `pip` poate înregistra vârfuri temporare de consum de până la ~150 MB RAM. Dacă procesul de instalare se oprește din lipsă de memorie (OOM), alocați temporar **256 MB RAM** în panou, apoi reduceți limita înapoi la 128 MB după finalizare.

---

## 🚀 Instalare

**1. Clonează repository-ul:**
```bash
git clone https://github.com/<utilizatorul-tau>/GradeRemind.git
cd GradeRemind
```

**2. Creează un mediu virtual și instalează dependențele:**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

**3. Configurează variabilele de mediu:**
```bash
cp .env.example .env
# Editează .env cu datele tale
```

---

## ⚙️ Configurare

Copiază fișierul `.env.example` în `.env` și completează câmpurile:

```env
# === Credențiale cont portal ===
PORTAL_UTILIZATOR=utilizator@email.com   # e-mail sau ID cont
PORTAL_PAROLA=parola_ta
PORTAL_ROLA=0                            # 0 = student

# === URL-uri portal (adaptează pentru orice portal universitar) ===
PORTAL_BASE_URL=https://your-portal.example.com
PORTAL_LOGIN_PATH=/login.php
PORTAL_API_PATH=/api/ver_user.json.php
PORTAL_DASHBOARD_PATH=/parcurs/dashboard.php

# === User-Agent (copiază-l din browserul tău real) ===
PORTAL_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0

# === Server web dashboard ===
PORTAL_PORT=5000

# === Notificări Discord (opțional) ===
PORTAL_DISCORD_WEBHOOK=https://discord.com/api/webhooks/...

# === Comportament la pornire ===
# true = verifică imediat, false = așteaptă primul interval
PORTAL_INITIAL_CHECK=false

# === Ore active (opțional) ===
# Format: "oră_start-oră_stop" (24h). Gol = monitorizare 24/7.
PORTAL_ACTIVE_HOURS=6-23

# === Interval de verificare (în secunde) ===
PORTAL_MIN_VERIFICATION_INTERVAL=1800   # minim 30 minute
PORTAL_MAX_VERIFICATION_INTERVAL=5400  # maxim 90 minute
```

> **Notă:** Intervalul de așteptare este ales aleator între `MIN` și `MAX` pentru a evita pattern-uri repetitive de acces.

---

## ▶️ Utilizare

```bash
python main.py
```

La pornire vei vedea:
```
🚀 Botul de monitorizare note GradeRemind a pornit.
🌐 Serverul Web Dashboard a pornit pe: http://localhost:5000
ℹ️ Verificarea inițială la pornire este dezactivată.
💤 Se așteaptă 42 minute și 17 secunde până la următoarea verificare automată...
```

Deschide [http://localhost:5000](http://localhost:5000) în browser pentru a accesa dashboard-ul.

---

## 🐳 Docker

Poți rula GradeRemind complet containerizat, fără a instala Python sau dependențele local.

### Fișiere incluse

| Fișier | Rol |
|---|---|
| `Dockerfile` | Imaginea de producție bazată pe `python:3.12-slim` |
| `.dockerignore` | Exclude `.env`, datele generate, `.venv` din build context |

### Build

```bash
# Construiește imaginea și o etichetează "graderemind:latest"
docker build -t graderemind:latest .
```

> Prima construire durează ~30s (descarcă imaginea de bază și instalează pachetele).
> Construirile ulterioare sunt **instantanee** dacă `requirements.txt` nu s-a schimbat,
> datorită cache-ului Docker pe layer-ul de dependențe.

### Run — varianta simplă (pentru testare locală)

Credențialele se transmit ca variabile de mediu la runtime — **nu** se includ în imagine.

```bash
docker run -d \
  --name graderemind \
  --restart unless-stopped \
  -p 5000:5000 \
  -e PORTAL_UTILIZATOR="utilizator@email.com" \
  -e PORTAL_PAROLA="parola_ta" \
  -e PORTAL_BASE_URL="https://your-portal.example.com" \
  -e PORTAL_DISCORD_WEBHOOK="https://discord.com/api/webhooks/..." \
  -e PORTAL_PORT=5000 \
  -e PORTAL_INITIAL_CHECK=false \
  -e PORTAL_ACTIVE_HOURS="6-23" \
  -e PORTAL_MIN_VERIFICATION_INTERVAL=1800 \
  -e PORTAL_MAX_VERIFICATION_INTERVAL=5400 \
  -v graderemind_data:/app \
  graderemind:latest
```

### Run — folosind fișierul `.env` (recomandat)

```bash
docker run -d \
  --name graderemind \
  --restart unless-stopped \
  -p 5000:5000 \
  --env-file .env \
  -v graderemind_data:/app \
  graderemind:latest
```

> `-v graderemind_data:/app` montează un **named volume** Docker la `/app`.
> Aceasta face ca `note_salvate.json`, `sessions.json` și `note_log.txt` să persiste
> între repornirile containerului. Fără volum, datele se pierd la `docker rm`.

### Comenzi utile

```bash
# Urmărește log-urile în timp real
docker logs -f graderemind

# Oprește containerul
docker stop graderemind

# Repornește
docker restart graderemind

# Șterge containerul (datele rămân în volum)
docker rm graderemind

# Inspectează starea de sănătate (health check)
docker inspect --format='{{.State.Health.Status}}' graderemind
```

### Docker Compose (recomandat pentru deployment permanent)

Creează un fișier `docker-compose.yml` în rădăcina proiectului:

```yaml
services:
  graderemind:
    build: .
    image: graderemind:latest
    container_name: graderemind
    restart: unless-stopped
    ports:
      - "5000:5000"
    env_file:
      - .env
    volumes:
      - graderemind_data:/app
    healthcheck:
      test: ["CMD", "python", "-c",
             "import urllib.request; urllib.request.urlopen('http://localhost:5000/login')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s

volumes:
  graderemind_data:
```

Then:

```bash
# Pornire (build automat dacă imaginea nu există)
docker compose up -d

# Rebuild după modificări de cod
docker compose up -d --build

# Oprire
docker compose down
```

---

## 🦚 Pterodactyl / Pelican Panel

Dacă rulezi un panou de server games / hosting, poți instala GradeRemind direct ca **Egg** — fără Docker manual și fără SSH.

### Fișierele Egg

| Fișier | Format | Compatibil cu |
|---|---|---|
| [`eggs/egg-graderemind-pterodactyl.json`](eggs/egg-graderemind-pterodactyl.json) | `PTDL_v2` | Pterodactyl 1.x și Pelican (import) |
| [`eggs/egg-graderemind-pelican.json`](eggs/egg-graderemind-pelican.json) | `PLCN_v1` | Pelican (nativ) |

> **Notă:** Pelican poate importa nativ egg-uri `PTDL_v2` de Pterodactyl, așa că ambele fișiere funcționează pe Pelican. Folosește `PLCN_v1` pentru funcționalitate completă nativă.

### Cum să instalezi Egg-ul

**Pterodactyl:**
1. Admin Panel → **Nests** → alege sau creează un Nest (e.g. "Monitorizare")
2. Click **Import Egg** → încarcă `egg-graderemind-pterodactyl.json`
3. Setează imaginea Docker: `ghcr.io/parkervcp/yolks:python_3.12`
4. Creează un server nou cu acest Egg, configurează variabilele, rulează **Reinstall**

**Pelican:**
1. Admin Panel → **Eggs** → **Import Egg**
2. Încarcă `egg-graderemind-pelican.json`
3. Creează un server nou, completează variabilele de mai jos, rulează **Reinstall**

### Variabile configurabile în panou

| Variabilă | Implicit | Descriere |
|---|---|---|
| `GIT_REPO` | — | URL-ul repository-ului GitHub (obligatoriu) |
| `BRANCH` | `main` | Branch-ul de clonat |
| `PORTAL_UTILIZATOR` | — | E-mail sau CNP cont portalul academic |
| `PORTAL_PAROLA` | — | Parola contului portalului (înregistrată ca `password`) |
| `PORTAL_PORT` | `5000` | Portul dashboard-ului web |
| `PORTAL_DISCORD_WEBHOOK` | _(gol)_ | URL Webhook Discord (opțional) |
| `PORTAL_INITIAL_CHECK` | `false` | Verifică imediat la pornire? |
| `PORTAL_ACTIVE_HOURS` | _(gol)_ | Interval orar activ, e.g. `6-23` |
| `PORTAL_MIN_VERIFICATION_INTERVAL` | `1800` | Interval minim între verificări (secunde) |
| `PORTAL_MAX_VERIFICATION_INTERVAL` | `5400` | Interval maxim între verificări (secunde) |

### Ce face scriptul de instalare

```
[1/4] Instalează git, curl, python3 și pip (apk)
[2/4] Clonează / actualizează repository-ul din GIT_REPO@BRANCH
[3/4] Creează un virtualenv Python în /mnt/server/.venv (persistă între restart-uri!)
[4/4] pip install -r requirements.txt în interiorul venv-ului
```

Startup command: `.venv/bin/python main.py`  
Panelul detectează că aplicația e pornită după ce apare linia `Serverul Web Dashboard a pornit pe` în logs.

---

## 🏛️ Arhitectură

GradeRemind a fost construit cu respectarea principiilor **SOLID** și următoarele foi de parcurs:

- **Structura proiectului** — modul/responsabilități
- **Arhitectura SOLID** — principii de design și extensibilitate
- **Data Flow** — cum se mișcă datele prin aplicație
- **Testabilitate și Thread Safety** — paralelism și testare izolată

Pentru detalii complete, consultă [**ARCHITECTURE.md**](ARCHITECTURE.md).

---

## 🌐 Dashboard Web

Accesibil la `http://localhost:<PORTAL_PORT>` după pornirea aplicației.

### Funcționalități dashboard:
- **Statistici dinamice** — numărul total de materii și media generală calculată automat
- **Cronometru live** — timp până la următoarea verificare automată (sau indicator de pauză)
- **Verificare manuală** — buton pentru a declanșa o verificare imediată fără a mai aștepta
- **Notificări browser** — activare push notifications native prin Web Notification API
- **Test Webhook Discord** — verifică că webhook-ul funcționează fără a aștepta o schimbare reală de notă
- **Delogare** — sesiunea este ștearsă din memoria serverului și cookie-ul este invalidat
- **Design responsive** — optimizat pentru desktop și mobil

### Securitate:
- Sesiunile sunt protejate cu un token `UUID` aleator, persistat criptat în `sessions.json`
- Cookie-urile sunt marcate `HttpOnly; SameSite=Lax` pentru a preveni accesul din JavaScript terț
- Expirare automată după 7 zile

---

## 🧪 Rularea testelor

```bash
.venv\Scripts\python.exe -m unittest tests\test_components.py -v
```

---

## 🤝 Contribuții

Pull requests sunt binevenite! Pași:

1. Fork repository-ul
2. Creează un branch nou: `git checkout -b feature/numele-functiei`
3. Commit modificările: `git commit -m 'feat: adaugă funcționalitate X'`
4. Push pe branch: `git push origin feature/numele-functiei`
5. Deschide un Pull Request

---

## ⚠️ Disclaimer

Acest proiect a fost realizat **exclusiv în scop educațional**, ca demonstrație de arhitectură software modulară (SOLID), automatizare web cu Python și deployment modern (Docker, Pterodactyl).

- **Nu include și nu va include niciodată date personale reale** (credențiale, note, date de identificare) — toate fișierele cu date generate local sunt excluse prin `.gitignore`.
- URL-ul portalului țintă nu este hardcodat în cod — se configurează exclusiv prin `.env` (`PORTAL_BASE_URL`).
- **Autorul nu încurajează și nu își asumă responsabilitatea** pentru utilizarea acestui script pe platforme fără acordul administratorilor acestora. Utilizați pe proprie răspundere și în conformitate cu termenii de utilizare ai platformei vizate.
- Nu stoca niciodată parole sau date personale în fișiere commituite în repository-uri publice — folosește `.gitignore` pentru a exclude `.env`.

---

<p align="center">
  Realizat cu ❤️ ca proiect educațional open-source
</p>
