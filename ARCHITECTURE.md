# 🏛️ Arhitectura și Design Patterns

Acest document detaliază structura proiectului GradeRemind și principiile SOLID pe care se bazează.

---

## 📁 Structura proiectului

```
GradeRemind/
├── main.py                     # Entry point — inițializează și pornește aplicația
├── .env                        # Configurare locală (nu se commitează!)
├── .env.example                # Template configurare
├── requirements.txt
├── note_salvate.json           # Istoricul notelor (auto-generat)
├── note_log.txt                # Jurnalul verificărilor (auto-generat)
├── sessions.json               # Sesiuni web active (auto-generat)
│
├── src/
│   ├── __init__.py
│   ├── config.py               # Citire și validare variabile .env (Config)
│   ├── interfaces.py           # Contracte abstracte ABC (DIP / ISP)
│   ├── services.py             # Implementări concrete: scraper, storage, notificări
│   ├── monitor.py              # Orchestrator GradeMonitor (logica de business)
│   ├── web_server.py           # Server HTTP multi-threaded + request handler
│   └── templates/
│       ├── dashboard.html      # UI dashboard cu statistici și cronometru
│       └── login.html          # Pagina de autentificare
│
└── tests/
    └── test_components.py      # Teste unitare (unittest + mock)
```

### Responsabilități module

| Modul | Scop |
|---|---|
| **config.py** | Citire variabile de mediu din `.env`, validare, conversie tipuri |
| **interfaces.py** | Definire contracte abstracte pentru toți actorii majori (ABC) |
| **services.py** | Implementări concrete: HTTP client, parser HTML, storage JSON, notifiers |
| **monitor.py** | Orchestrator central — coordonează verificări, gestionează timer-ul activ |
| **web_server.py** | Server HTTP multi-threaded cu request routing și render template-uri |
| **templates/** | HTML cu CSS/JS pentru dashboard și login page |

---

## 🏛️ Principiile SOLID

Proiectul a fost construit respectând integral principiile **SOLID**, un set de directrii pentru cod extensibil, testabil și ușor de întreținut.

### **S — Single Responsibility Principle**

Fiecare clasă/modul are o singură responsabilitate bine definită:

- **`Config`** → **doar** citire și validare configurare din mediu
- **`GradePortalWebClient`** → **doar** gestionare sesiune HTTP și request-uri
- **`GradePortalHtmlParser`** → **doar** parsare HTML din răspunsuri
- **`JsonFileGradeStorage`** → **doar** persistență și citire fișier JSON
- **`TextFileGradeLogger`** → **doar** logging cronologic în fișier text
- **`GradeMonitor`** → **doar** orchestrare logică de business și timer
- **`BuiltInGradeWebServer`** → **doar** serving HTTP și render template-uri

**Beneficii:**
- Testare ușoară — fiecare clasă are un singur motiv de schimbare
- Reutilizare — componentele sunt decuplate și pot fi folosite independent
- Debugging — erori sunt izolate în zone specifice

### **O — Open/Closed Principle**

Codul este **deschis pentru extensie**, dar **închis pentru modificare**.

**Exemplu:** Adăugarea unui nou canal de notificare (Telegram, Email, SMS):

```python
class TelegramNotificationProvider(INotificationProvider):
    def notify(self, subject: str, grade: str) -> None:
        # Trimitere pe Telegram...
        pass

# În main.py, fără a modifica cod existent:
composite_notifier.add_provider(TelegramNotificationProvider(...))
```

**Nu trebuie modificat** niciun fișier existent; doar adunăm o nouă implementare a interfaței.

### **L — Liskov Substitution Principle**

Orice implementare concretă a unei interfețe poate **înlocui tipul abstract fără a afecta comportamentul**.

```python
def test_any_notifier():
    notifier: INotificationProvider = ConsoleNotificationProvider()
    notifier.notify("Math", "A")  # Funcționează
    
    notifier = DiscordNotificationProvider("https://...")
    notifier.notify("Math", "A")  # Funcționează la fel

    notifier = TelegramNotificationProvider("token")
    notifier.notify("Math", "A")  # Funcționează în continuare
```

### **I — Interface Segregation Principle**

Interfețele sunt **mici, specifice și focusate** — nu forțează implementatori să depindă de metode pe care nu le folosesc.

```python
# ❌ Prost — interfață monolitică
class IGradeSystem(ABC):
    @abstractmethod
    def parse(self) -> Dict: pass
    @abstractmethod
    def store(self) -> None: pass
    @abstractmethod
    def notify(self) -> None: pass
    @abstractmethod
    def log(self) -> None: pass

# ✅ Bine — interfețe segregate
class IGradeParser(ABC):
    @abstractmethod
    def parse_grades(self, html: str) -> Dict: pass

class IGradeStorage(ABC):
    @abstractmethod
    def save_history(self, grades: Dict) -> None: pass

class INotificationProvider(ABC):
    @abstractmethod
    def notify(self, subject: str, grade: str) -> None: pass

class IGradeLogger(ABC):
    @abstractmethod
    def log(self, grades: Dict) -> None: pass
```

### **D — Dependency Inversion Principle**

Clasele de nivel înalt **nu depind de detalii de implementare**, ci de **abstracții (interfețe)**.

```python
class GradeMonitor:
    def __init__(
        self,
        web_client: IWebClient,        # Abstracție, nu implementare!
        parser: IGradeParser,           # Abstracție, nu implementare!
        storage: IGradeStorage,         # Abstracție, nu implementare!
        logger: IGradeLogger,           # Abstracție, nu implementare!
        notifier: INotificationProvider # Abstracție, nu implementare!
    ):
        self.web_client = web_client
        self.parser = parser
        self.storage = storage
        self.logger = logger
        self.notifier = notifier
```

**Avantaje:**
- Testare ușoară cu mock-uri
- Swappable implementations — poți înlocui `GradePortalWebClient` cu altul
- Flexibilitate — configurația e injectată la runtime

**Exemplu de testare:**

```python
def test_monitor_with_mocks():
    mock_web_client = MagicMock(spec=IWebClient)
    mock_parser = MagicMock(spec=IGradeParser)
    mock_storage = MagicMock(spec=IGradeStorage)
    
    monitor = GradeMonitor(
        web_client=mock_web_client,
        parser=mock_parser,
        storage=mock_storage,
        logger=MagicMock(spec=IGradeLogger),
        notifier=MagicMock(spec=INotificationProvider)
    )
    
    # Testarea e trivială — nu depinde de implementări reale!
```

---

## 🔄 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│  main.py — Entry Point                                      │
│  Inițializează Config, dependențe, și pornește aplicația    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  GradeMonitor — Orchestrator                                │
│  Coordonează verificări, gestionează timer și interval activ│
└──────────┬──────────────────────────────────┬───────────────┘
           │                                  │
           ▼                                  ▼
   ┌───────────────────┐           ┌──────────────────────┐
   │ GradePortalWeb    │           │ BuiltInGradeWebServer│
   │ Client (IWebC.)   │           │ (IWebServer)         │
   │                   │           │                      │
   │ • authenticate()  │           │ • start()            │
   │ • fetch_dashb()   │           │ • handle requests    │
   └─────────┬─────────┘           │ • render templates   │
             │                     └──────────────────────┘
             ▼
   ┌───────────────────┐
   │ GradePor talHTML  │
   │ Parser (IGradeP.) │
   │                   │
   │ • parse_grades()  │
   └─────────┬─────────┘
             │
             ▼
   ┌───────────────────┐
   │ JsonFileGrade     │
   │ Storage (IGradeS.)│
   │                   │
   │ • save_history()  │
   │ • load_history()  │
   └─────────┬─────────┘
             │
             ├──────────────┬──────────────────┐
             │              │                  │
             ▼              ▼                  ▼
      ┌─────────┐   ┌──────────┐    ┌──────────────┐
      │ Console │   │ Discord  │    │ TextFileGrade│
      │ Notifier│   │ Notifier │    │ Logger       │
      │(INotif.)│   │(INotif.) │    │(IGradeLogger)│
      │         │   │          │    │              │
      │ • notify│   │ • notify │    │ • log()      │
      └─────────┘   └──────────┘    └──────────────┘
```

---

## 🧪 Testabilitate

Arhitectura SOLID permite testare izolată ușoară:

```bash
.venv\Scripts\python.exe -m unittest tests/test_components.py -v
```

Fiecare componentă poate fi testată cu mock-uri fără a depinde de implemen­tări externe:

- **Nu necesită** cont real pe portal
- **Nu necesită** webhook Discord real
- **Nu necesită** fișiere temporare
- **Rulează** instant și repetat

---

## 🔐 Thread Safety

`GradeMonitor` folosește `threading.Lock` pentru a sincroniza:

- Accesul la `remaining_active_seconds` (timer)
- Accesul la `last_tick_time` (timp ultima actualizare)

Aceasta permite:
- Verificări automate rulând în background
- Verificări manuale declanșate din dashboard
- Ambele să coexiste fără **race conditions**

---

## 🚀 Extensibilitate

### Exemplu: Adăugare nouă sursă de date

1. Implementează `IGradeParser`:
   ```python
   class MyUniversityParser(IGradeParser):
       def parse_grades(self, html: str) -> Dict:
           # Logica ta specifică
           pass
   ```

2. Injectează în `GradeMonitor`:
   ```python
   monitor = GradeMonitor(
       parser=MyUniversityParser(),
       # ...alte dependențe
   )
   ```

**Nicio modificare** în codul existent!

### Exemplu: Adăugare nouă metodă de notificare

1. Implementează `INotificationProvider`:
   ```python
   class EmailNotificationProvider(INotificationProvider):
       def notify(self, subject: str, grade: str) -> None:
           # Trimitere email
           pass
   ```

2. Adaug la notifier compus:
   ```python
   composite_notifier.add_provider(EmailNotificationProvider(...))
   ```

**Nicio modificare** în codul existent!

---

## 📊 Diagrama Dependențelor

```
interfaces.py (Abstracții)
    ▲
    │ (implementează)
    │
services.py (Implementări concrete)
    │
    │ (injectate în)
    │
monitor.py (Orchestrator)
    │
    │ (instanțiat și configurat în)
    │
main.py (Entry point)
```

**Direcția dependențelor merge de jos în sus (spre abstracții)**, nu opusul. Asta e esența **Dependency Inversion**.

---

<p align="center">
  Arhitectura SOLID asigură cod modular, testabil și extensibil
</p>
