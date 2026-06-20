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
    
    def validate(self) -> Tuple[list, list]:
        """
        Validează configurația și returnează lista de erori și avertismente.
        
        Returns:
            Tuple[list, list] — (errori, avertismente)
        """
        errors = []
        warnings = []
        
        # Validări CRITICE
        if self.utilizator.startswith("introdu_aici"):
            errors.append("❌ PORTAL_UTILIZATOR nu este setat. Setează email/CNP-ul tău în .env")
        
        if self.parola.startswith("introdu_aici"):
            errors.append("❌ PORTAL_PAROLA nu este setată. Setează parola în .env")
        
        if self.base_url.startswith("https://your-portal"):
            errors.append("❌ PORTAL_BASE_URL nu este setat sau e generic. Setează URL-ul real al portalului")
        
        if not self.base_url.startswith(("http://", "https://")):
            errors.append(f"❌ PORTAL_BASE_URL trebuie să înceapă cu http:// sau https://. Găsit: {self.base_url}")
        
        # Validări pentru intervale
        if self.min_verification_interval < 60:
            errors.append(f"❌ PORTAL_MIN_VERIFICATION_INTERVAL trebuie să fie >= 60 secunde. Găsit: {self.min_verification_interval}s")
        
        if self.max_verification_interval < 60:
            errors.append(f"❌ PORTAL_MAX_VERIFICATION_INTERVAL trebuie să fie >= 60 secunde. Găsit: {self.max_verification_interval}s")
        
        if self.min_verification_interval > self.max_verification_interval:
            errors.append(f"❌ PORTAL_MIN_VERIFICATION_INTERVAL ({self.min_verification_interval}s) > MAX ({self.max_verification_interval}s)")
        
        # Validări port
        if not (1024 <= self.port <= 65535):
            errors.append(f"❌ PORTAL_PORT trebuie să fie între 1024-65535. Găsit: {self.port}")
        
        # Validări ore active
        if self.active_hours:
            start_h, end_h = self.active_hours
            if not (0 <= start_h <= 23):
                errors.append(f"❌ Ora de start (PORTAL_ACTIVE_HOURS) trebuie să fie 0-23. Găsit: {start_h}")
            if not (0 <= end_h <= 23):
                errors.append(f"❌ Ora de end (PORTAL_ACTIVE_HOURS) trebuie să fie 0-23. Găsit: {end_h}")
        
        # AVERTISMENTE (nu blochează, dar informează)
        if self.user_agent.startswith("Mozilla/5.0 (compatible; GradeRemind"):
            warnings.append(f"⚠️  User-Agent-ul este generic default. Recomandare: setează PORTAL_USER_AGENT cu UA real din browser (F12 → Network → Headers) pentru a pare trafic normal.")
        
        if not self.discord_webhook:
            warnings.append("ℹ️  PORTAL_DISCORD_WEBHOOK nu este setat. Notificări Discord sunt dezactivate (opcional).")
        
        if self.initial_check:
            warnings.append("ℹ️  PORTAL_INITIAL_CHECK=true — va rula o verificare imediat la startup.")
        
        if self.active_hours:
            start_h, end_h = self.active_hours
            if start_h == end_h:
                warnings.append(f"⚠️  PORTAL_ACTIVE_HOURS are start == end ({start_h}:00). Monitorizare efectiv DEZACTIVATĂ.")
        
        return errors, warnings
