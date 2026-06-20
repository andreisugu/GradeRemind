import time
import random
import threading
from typing import Dict, Optional

from src.config import Config
from src.interfaces import (
    IWebClient,
    IGradeParser,
    IGradeStorage,
    IGradeLogger,
    INotificationProvider
)

class GradeMonitor:
    """ Clasă orchestratoare responsabilă de fluxul de business (SRP, OCP, DIP) """
    
    def __init__(
        self,
        web_client: IWebClient,
        parser: IGradeParser,
        storage: IGradeStorage,
        logger: IGradeLogger,
        notifier: INotificationProvider
    ) -> None:
        self.web_client: IWebClient = web_client
        self.parser: IGradeParser = parser
        self.storage: IGradeStorage = storage
        self.logger: IGradeLogger = logger
        self.notifier: INotificationProvider = notifier
        self.config: Config = web_client.config
        self.lock: threading.Lock = threading.Lock()
        self.run_lock: threading.Lock = threading.Lock()
        
        # Inițializare interval de verificare
        initial_interval = random.randint(self.config.min_verification_interval, self.config.max_verification_interval)
        self.remaining_active_seconds: float = float(initial_interval)
        self.last_tick_time: float = time.time()
        self.reset_event: threading.Event = threading.Event()

    def is_currently_active(self) -> bool:
        if not self.config.active_hours:
            return True
        start_h, end_h = self.config.active_hours
        current_hour = time.localtime().tm_hour
        if start_h <= end_h:
            return start_h <= current_hour < end_h
        else:
            return current_hour >= start_h or current_hour < end_h

    def get_next_check_in(self) -> int:
        with self.lock:
            now = time.time()
            elapsed = now - self.last_tick_time
            self.last_tick_time = now
            if self.is_currently_active():
                self.remaining_active_seconds -= elapsed
                if self.remaining_active_seconds < 0:
                    self.remaining_active_seconds = 0
            return int(self.remaining_active_seconds)

    def reschedule_automatic_check(self) -> None:
        interval_aleator = random.randint(self.config.min_verification_interval, self.config.max_verification_interval)
        with self.lock:
            self.remaining_active_seconds = float(interval_aleator)
            self.last_tick_time = time.time()
        self.reset_event.set()
        
        minute_afisate = interval_aleator // 60
        secunde_afisate = interval_aleator % 60
        print(f"🔄 Verificarea manuală a decalat programul. Următoarea verificare automată va avea loc peste {minute_afisate} minute și {secunde_afisate} secunde...\n")

    def trigger_manual_check(self) -> bool:
        # Încercăm achiziționarea lock-ului non-blocking pentru a preveni verificări paralele concurente
        acquired = self.run_lock.acquire(blocking=False)
        if not acquired:
            print("⚠️ Verificare manuală ignorată: o verificare este deja în desfășurare.")
            return False
        try:
            self.run_once_unlocked()
            self.reschedule_automatic_check()
            return True
        finally:
            self.run_lock.release()

    def run_once(self) -> None:
        with self.run_lock:
            self.run_once_unlocked()

    def run_once_unlocked(self) -> None:
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] Se încearcă autentificarea pe portalul academic...")
        
        if not self.web_client.authenticate():
            return

        html_content = self.web_client.fetch_dashboard()
        note_noi = self.parser.parse_grades(html_content)
        
        if not note_noi:
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("⚠️ Nu s-au găsit note în pagină. Structura portalului s-a schimbat. HTML-ul paginii a fost salvat în 'debug_page.html'.")
            return

        # Salvare istoric în fișierul de log
        self.logger.log(note_noi)

        # Citire istoric precedent
        note_vechi = self.storage.load_history()
        
        if note_vechi is None:
            # Prima rulare sau conversie de format
            now = time.time()
            for an, semestre in note_noi.items():
                for sem, materii in semestre.items():
                    for mat, info in materii.items():
                        info["last_modified"] = now
            self.storage.save_history(note_noi)
            print("✅ Istoricul inițial al notelor a fost salvat local. Monitorizarea a început.")
            return

        modificari_detectate = False
        now = time.time()
        
        # Comparăm notele
        for an, semestre in note_noi.items():
            for sem, materii in semestre.items():
                for mat, info in materii.items():
                    try:
                        vechi_info = note_vechi[an][sem][mat]
                        vechea_nota = vechi_info["grade"]
                        vechi_timestamp = vechi_info.get("last_modified", 0.0)
                    except (KeyError, TypeError):
                        vechea_nota = None
                        vechi_timestamp = 0.0
                    
                    if vechea_nota is None:
                        # Materie nouă
                        info["last_modified"] = now
                        self.notifier.notify(mat, info["grade"])
                        modificari_detectate = True
                    elif vechea_nota != info["grade"]:
                        # Modificare notă
                        info["last_modified"] = now
                        self.notifier.notify(mat, info["grade"])
                        modificari_detectate = True
                    else:
                        # Nicio modificare
                        if vechi_timestamp == 0.0:
                            info["last_modified"] = now
                            modificari_detectate = True
                        else:
                            info["last_modified"] = vechi_timestamp

        if modificari_detectate:
            self.storage.save_history(note_noi)
        else:
            print("✅ Verificare reușită. Nicio notă nouă adăugată.")
