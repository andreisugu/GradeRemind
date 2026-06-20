import os
import json
import time
import uuid
import threading
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from typing import Dict, Optional, Any

from src.interfaces import IWebServer, IGradeStorage
from src.monitor import GradeMonitor

# Încărcare dinamică a template-urilor HTML din directorul local
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_template(name: str) -> str:
    path = os.path.join(BASE_DIR, "templates", name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_template_bytes(name: str) -> bytes:
    path = os.path.join(BASE_DIR, "templates", name)
    with open(path, "rb") as f:
        return f.read()

try:
    LOGIN_HTML = get_template("login.html")
except Exception as e:
    print(f"⚠️ Nu s-a putut încărca template-ul de login: {e}")
    LOGIN_HTML = "Autentificare esuata - Lipseste login.html"


class CustomThreadingHTTPServer(ThreadingHTTPServer):
    """ Subclasă pentru ThreadingHTTPServer pentru a include explicit tipurile de date """
    
    def __init__(
        self,
        server_address: tuple,
        RequestHandlerClass: type,
        storage: IGradeStorage,
        html_content: str,
        monitor: GradeMonitor,
        sessions: Dict[str, float],
        save_sessions_callable: Any
    ) -> None:
        super().__init__(server_address, RequestHandlerClass)
        self.storage: IGradeStorage = storage
        self.html_content: str = html_content
        self.monitor: GradeMonitor = monitor
        self.sessions: Dict[str, float] = sessions
        self.save_sessions: Any = save_sessions_callable


class GradeHTTPRequestHandler(BaseHTTPRequestHandler):
    """ Handler HTTP pentru rutarea cererilor dashboard-ului (LSP) """
    
    server: CustomThreadingHTTPServer

    def log_message(self, format: str, *args: Any) -> None:
        # Dezactivare logs standard în consolă pentru a nu polua output-ul
        pass

    def get_session_id(self) -> Optional[str]:
        cookie_header = self.headers.get('Cookie')
        if not cookie_header:
            return None
        try:
            cookie = SimpleCookie(cookie_header)
            if 'session_id' in cookie:
                return cookie['session_id'].value
        except Exception:
            pass
        return None

    def is_authenticated(self) -> bool:
        session_id = self.get_session_id()
        if not session_id:
            return False
        expiry = self.server.sessions.get(session_id)
        if not expiry:
            return False
        if time.time() > expiry:
            self.server.sessions.pop(session_id, None)
            self.server.save_sessions()
            return False
        return True

    def do_GET(self) -> None:
        if self.path == '/manifest.json':
            try:
                content = get_template("manifest.json")
                self.send_response(200)
                self.send_header('Content-Type', 'application/manifest+json; charset=utf-8')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except Exception:
                self.send_response(404)
                self.end_headers()
            return

        if self.path == '/sw.js':
            try:
                content = get_template("sw.js")
                self.send_response(200)
                self.send_header('Content-Type', 'application/javascript; charset=utf-8')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except Exception:
                self.send_response(404)
                self.end_headers()
            return

        if self.path in ['/icon.png', '/favicon.ico']:
            try:
                content = get_template_bytes("icon.png")
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.end_headers()
                self.wfile.write(content)
            except Exception:
                self.send_response(404)
                self.end_headers()
            return

        if self.path == '/login':
            if self.is_authenticated():
                self.send_response(302)
                self.send_header('Location', '/')
                self.end_headers()
            else:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(LOGIN_HTML.replace('{error_placeholder}', '').encode('utf-8'))
            return

        if self.path == '/logout':
            session_id = self.get_session_id()
            if session_id:
                self.server.sessions.pop(session_id, None)
                self.server.save_sessions()
            self.send_response(302)
            self.send_header('Location', '/login')
            self.send_header('Set-Cookie', 'session_id=; Max-Age=0; Path=/; HttpOnly; SameSite=Lax')
            self.end_headers()
            return

        if not self.is_authenticated():
            self.send_response(302)
            self.send_header('Location', '/login')
            self.end_headers()
            return

        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.server.html_content.encode('utf-8'))
        elif self.path == '/api/grades':
            history = self.server.storage.load_history()
            if history is None:
                history = {}
            response_data = {
                "grades": history,
                "next_check_in": self.server.monitor.get_next_check_in(),
                "is_paused": not self.server.monitor.is_currently_active(),
                "active_hours_str": f"{self.server.monitor.config.active_hours[0]:02d}:00 - {self.server.monitor.config.active_hours[1]:02d}:00" if self.server.monitor.config.active_hours else None
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    def do_POST(self) -> None:
        if self.path == '/login':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            parsed_data = parse_qs(post_data)
            
            username = parsed_data.get('username', [''])[0]
            password = parsed_data.get('password', [''])[0]
            
            config = self.server.monitor.web_client.config
            if username == config.utilizator and password == config.parola:
                session_id = uuid.uuid4().hex
                # Expirare în 7 zile
                expiry = time.time() + 7 * 24 * 3600
                self.server.sessions[session_id] = expiry
                self.server.save_sessions()
                
                self.send_response(302)
                self.send_header('Location', '/')
                cookie_str = f"session_id={session_id}; Max-Age=604800; Path=/; HttpOnly; SameSite=Lax"
                self.send_header('Set-Cookie', cookie_str)
                self.end_headers()
            else:
                error_div = '<div class="error-message">Utilizator sau parolă incorectă!</div>'
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(LOGIN_HTML.replace('{error_placeholder}', error_div).encode('utf-8'))
            return

        if not self.is_authenticated():
            self.send_response(401)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode('utf-8'))
            return

        if self.path == '/api/check':
            success = self.server.monitor.trigger_manual_check()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"success": success}).encode('utf-8'))
        elif self.path == '/api/test-discord':
            config = self.server.monitor.web_client.config
            if not config.discord_webhook:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Webhook-ul Discord nu este configurat în fișierul .env!"}).encode('utf-8'))
                return
            
            self.server.monitor.notifier.notify("Test Webhook Discord", "Succes")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")


class BuiltInGradeWebServer(IWebServer):
    """ Implementare concretă a serverului web multi-threaded (LSP, SRP) """
    
    def __init__(self, port: int, storage: IGradeStorage, html_content: str, monitor: GradeMonitor) -> None:
        self.port: int = port
        self.storage: IGradeStorage = storage
        self.html_content: str = html_content
        self.monitor: GradeMonitor = monitor
        self.sessions: Dict[str, float] = self.load_sessions()
        self.server: Optional[CustomThreadingHTTPServer] = None
        self.thread: Optional[threading.Thread] = None

    def load_sessions(self) -> Dict[str, float]:
        sessions_file = "sessions.json"
        if not os.path.exists(sessions_file):
            return {}
        try:
            with open(sessions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            now = time.time()
            valid_sessions = {sid: float(exp) for sid, exp in data.items() if float(exp) > now}
            return valid_sessions
        except Exception as e:
            print(f"⚠️ Eroare la încărcarea sesiunilor persistate: {e}")
            return {}

    def save_sessions(self) -> None:
        sessions_file = "sessions.json"
        try:
            with open(sessions_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=4)
        except Exception as e:
            print(f"⚠️ Eroare la salvarea sesiunilor persistate: {e}")

    def start(self) -> None:
        def run_server() -> None:
            try:
                self.server = CustomThreadingHTTPServer(
                    ('0.0.0.0', self.port),
                    GradeHTTPRequestHandler,
                    storage=self.storage,
                    html_content=self.html_content,
                    monitor=self.monitor,
                    sessions=self.sessions,
                    save_sessions_callable=self.save_sessions
                )
                print(f"🌐 Serverul Web Dashboard a pornit pe: http://localhost:{self.port}")
                self.server.serve_forever()
            except Exception as e:
                print(f"❌ Eroare la pornirea serverului web: {e}")

        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("🌐 Serverul Web Dashboard a fost oprit.")
