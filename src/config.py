import os
from typing import Tuple, Optional

class Config:
    """ Clasă care încapsulează configurările aplicației """
    
    def __init__(self) -> None:
        self.utilizator: str = os.getenv("PORTAL_UTILIZATOR", "introdu_aici_cnp_sau_email")
        self.parola: str = os.getenv("PORTAL_PAROLA", "introdu_aici_parola")
        self.rola_student: str = os.getenv("PORTAL_ROLA", "0")
        self.discord_webhook: str = os.getenv("PORTAL_DISCORD_WEBHOOK", "")
        
        try:
            self.port: int = int(os.getenv("PORTAL_PORT", "5000"))
        except ValueError:
            self.port = 5000
            
        try:
            self.verification_interval: int = int(os.getenv("PORTAL_VERIFICATION_INTERVAL", "1800"))
        except ValueError:
            self.verification_interval = 1800
            
        try:
            self.min_verification_interval: int = int(os.getenv("PORTAL_MIN_VERIFICATION_INTERVAL", str(self.verification_interval)))
        except ValueError:
            self.min_verification_interval = 1800
            
        try:
            self.max_verification_interval: int = int(os.getenv("PORTAL_MAX_VERIFICATION_INTERVAL", str(self.verification_interval * 3)))
        except ValueError:
            self.max_verification_interval = 5400
            
        if self.min_verification_interval > self.max_verification_interval:
            self.min_verification_interval, self.max_verification_interval = self.max_verification_interval, self.min_verification_interval
            
        active_hours_str: str = os.getenv("PORTAL_ACTIVE_HOURS", "")
        self.active_hours: Optional[Tuple[int, int]] = None
        if active_hours_str:
            try:
                parts = active_hours_str.split('-')
                if len(parts) == 2:
                    self.active_hours = (int(parts[0]), int(parts[1]))
            except ValueError:
                print("⚠️ Intervalul de ore active (PORTAL_ACTIVE_HOURS) nu a putut fi parsat. Se monitorizează 24/7.")
            
        initial_check_str: str = os.getenv("PORTAL_INITIAL_CHECK", "false").lower()
        self.initial_check: bool = initial_check_str in ("true", "1", "yes", "on")
            
        self.note_file: str = "note_salvate.json"
        self.log_file: str = "note_log.txt"

        # URLs — citite din env vars cu default-uri neutre.
        # Setează PORTAL_BASE_URL în .env pentru a adapta la orice portal universitar.
        self.base_url: str = os.getenv("PORTAL_BASE_URL", "https://your-portal.example.com")
        _login_path:     str = os.getenv("PORTAL_LOGIN_PATH",     "/login.php")
        _api_path:       str = os.getenv("PORTAL_API_PATH",       "/api/ver_user.json.php")
        _dashboard_path: str = os.getenv("PORTAL_DASHBOARD_PATH", "/parcurs/dashboard.php")

        self.login_url:     str = f"{self.base_url}{_login_path}"
        self.api_url:       str = f"{self.base_url}{_api_path}"
        self.dashboard_url: str = f"{self.base_url}{_dashboard_path}"

        # User-Agent — setat în .env cu browser-ul tău real pentru a părea trafic normal.
        # Default-ul generic este intenționat neutru; înlocuiește-l cu UA-ul real.
        self.user_agent: str = os.getenv(
            "PORTAL_USER_AGENT",
            "Mozilla/5.0 (compatible; GradeRemind/1.0)"
        )
