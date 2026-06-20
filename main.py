import os
import sys
import time
import random
from dotenv import load_dotenv

from src import __version__
from src.config import Config
from src.services import (
    GradePortalWebClient,
    GradePortalHtmlParser,
    JsonFileGradeStorage,
    TextFileGradeLogger,
    CompositeNotificationProvider,
    ConsoleNotificationProvider,
    DiscordNotificationProvider,
    GitHubUpdateChecker
)
from src.monitor import GradeMonitor
from src.web_server import BuiltInGradeWebServer, get_template

# Reconfigurare console pentru UTF-8 ca să evităm erori de afișare/Unicode (e.g. emoji pe Windows)
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Încarcă variabilele din fișierul .env (dacă există)
load_dotenv()


def main() -> None:
    print("🚀 Botul de monitorizare note GradeRemind a pornit.")
    
    # Check for updates (non-blocking)
    try:
        update_checker = GitHubUpdateChecker(__version__)
        update_info = update_checker.check_for_updates()
        if update_info:
            print(f"\n📦 ACTUALIZARE DISPONIBILĂ: v{update_info['version']}")
            print(f"   Link: {update_info['url']}")
            print("   Relanșează pentru a aplica.\n")
    except Exception:
        pass

    # Instanțiere dependencies
    config = Config()
    
    # Validare configurare
    errors, warnings = config.validate()
    
    if errors:
        print("\n" + "="*70)
        print("❌ ERORI DE CONFIGURARE — STARTUP OPRIT")
        print("="*70)
        for error in errors:
            print(error)
        print("\n📝 Rezolvă erorile de mai sus în fișierul .env și relanșează.")
        print("="*70 + "\n")
        return
    
    if warnings:
        print("\n" + "-"*70)
        print("⚠️  AVERTISMENTE DE CONFIGURARE")
        print("-"*70)
        for warning in warnings:
            print(warning)
        print("-"*70 + "\n")
    
    # Continuă cu setup-ul normal dacă nu sunt erori
    web_client = GradePortalWebClient(config)
    parser = GradePortalHtmlParser()
    storage = JsonFileGradeStorage(config.note_file)
    logger = TextFileGradeLogger(config.log_file)
    
    # Configurare notifier compus (Composite & Open/Closed)
    composite_notifier = CompositeNotificationProvider()
    composite_notifier.add_provider(ConsoleNotificationProvider())
    if config.discord_webhook:
        composite_notifier.add_provider(DiscordNotificationProvider(config.discord_webhook))
    
    # Injectare dependințe în orchestrator (DIP)
    monitor = GradeMonitor(
        web_client=web_client,
        parser=parser,
        storage=storage,
        logger=logger,
        notifier=composite_notifier
    )
    
    # Încărcăm dashboard_html de pe disc
    try:
        dashboard_html = get_template("dashboard.html")
    except Exception as e:
        print(f"❌ Nu s-a putut încărca template-ul dashboard.html: {e}")
        dashboard_html = "<h1>Eroare la încărcarea paginii principale dashboard.html</h1>"
    
    # Pornim serverul web în background (Dependency Inversion & Single Responsibility)
    web_server = BuiltInGradeWebServer(config.port, storage, dashboard_html, monitor)
    web_server.start()
    
    try:
        # Preluăm intervalul inițial generat în constructor
        interval_aleator = int(monitor.remaining_active_seconds)
        
        if config.initial_check:
            # Facem prima verificare imediat la pornire
            try:
                monitor.run_once()
            except Exception as e:
                print(f"❌ A apărut o eroare neprevăzută în bucla principală: {e}")
        else:
            print("ℹ️ Verificarea inițială la pornire este dezactivată (PORTAL_INITIAL_CHECK=false).")
            
        # Generăm un nou interval aleator imediat după prima verificare
        interval_aleator = random.randint(config.min_verification_interval, config.max_verification_interval)
        with monitor.lock:
            monitor.remaining_active_seconds = float(interval_aleator)
            monitor.last_tick_time = time.time()
        
        minute_afisate = interval_aleator // 60
        secunde_afisate = interval_aleator % 60
        if monitor.is_currently_active():
            print(f"💤 Se așteaptă {minute_afisate} minute și {secunde_afisate} secunde până la următoarea verificare automată...\n")
        else:
            active_str = f"{config.active_hours[0]:02d}:00 - {config.active_hours[1]:02d}:00" if config.active_hours else "24/7"
            print(f"💤 Intervalul active-hours este în prezent inactiv ({active_str}). Timerul este pe pauză la {minute_afisate}m {secunde_afisate}s.\n")

        while True:
            # Așteptăm până când rem <= 0
            while True:
                rem = monitor.get_next_check_in()
                if rem <= 0:
                    break
                # Așteptăm pe event cu timeout de maxim 1 secundă pentru a actualiza frecvent sau a reacționa la resetare
                reset_triggered = monitor.reset_event.wait(timeout=1.0)
                if reset_triggered:
                    monitor.reset_event.clear()
                    # A fost generat un nou timp de către verificarea manuală, continuăm așteptarea noului interval
                    continue
            
            # Când rem <= 0, înseamnă că a sosit timpul pentru verificarea automată
            try:
                monitor.run_once()
            except Exception as e:
                print(f"❌ A apărut o eroare neprevăzută în bucla principală: {e}")
                
            # După verificarea automată, generăm un nou interval aleator
            interval_aleator = random.randint(config.min_verification_interval, config.max_verification_interval)
            with monitor.lock:
                monitor.remaining_active_seconds = float(interval_aleator)
                monitor.last_tick_time = time.time()
            
            minute_afisate = interval_aleator // 60
            secunde_afisate = interval_aleator % 60
            if monitor.is_currently_active():
                print(f"💤 Verificare automată finalizată. Următoarea va avea loc în {minute_afisate} minute și {secunde_afisate} secunde...\n")
            else:
                active_str = f"{config.active_hours[0]:02d}:00 - {config.active_hours[1]:02d}:00" if config.active_hours else "24/7"
                print(f"💤 Verificare automată finalizată. Intervalul active-hours este în prezent inactiv ({active_str}). Timerul este pe pauză la {minute_afisate}m {secunde_afisate}s.\n")
    except KeyboardInterrupt:
        print("\n👋 Se oprește monitorizarea la cererea utilizatorului...")
    finally:
        web_server.stop()


if __name__ == "__main__":
    main()