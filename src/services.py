import os
import json
import time
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, List

from src.config import Config
from src.interfaces import (
    INotificationProvider,
    IGradeLogger,
    IGradeStorage,
    IGradeParser,
    IWebClient
)

class ConsoleNotificationProvider(INotificationProvider):
    """ Implementare concretă care afișează alertele în consolă (LSP) """
    
    def notify(self, subject: str, grade: str) -> None:
        print(f"🔔 NOTIFICARE: S-a modificat/pus nota la '{subject}' -> Nota: {grade}!")


class DiscordNotificationProvider(INotificationProvider):
    """ Trimite alerte de note pe un canal de Discord via Webhook (LSP) """
    
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url: str = webhook_url

    def notify(self, subject: str, grade: str) -> None:
        if not self.webhook_url:
            return
        
        payload = {
            "content": f"🔔 **Notificare GradeRemind**: S-a modificat/pus nota la **{subject}** -> Nota: **{grade}**!"
        }
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code not in [200, 204]:
                print(f"❌ Eroare la trimiterea către Discord: status code {response.status_code}")
        except Exception as e:
            print(f"❌ Eroare la conexiunea cu Discord Webhook: {e}")


class CompositeNotificationProvider(INotificationProvider):
    """ Distribuie notificările către mai mulți provideri (LSP, OCP) """
    
    def __init__(self) -> None:
        self._providers: List[INotificationProvider] = []

    def add_provider(self, provider: INotificationProvider) -> None:
        self._providers.append(provider)

    def notify(self, subject: str, grade: str) -> None:
        for provider in self._providers:
            provider.notify(subject, grade)


class TextFileGradeLogger(IGradeLogger):
    """ Implementare concretă care înregistrează doar modificările în fișier text (LSP) """
    
    def __init__(self, log_file: str) -> None:
        self.log_file: str = log_file

    def log_changes(self, changes: Dict) -> None:
        """Logheaț doar modificările (note noi sau actualizate) în stil git: timestamp + lista schimburi"""
        if not changes:  # Dacă nu sunt modificări, nu scriem nimic
            return
        
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] MODIFICĂRI DETECTATE:\n")
                for an, semestre in sorted(changes.items(), reverse=True):
                    for sem, materii in sorted(semestre.items()):
                        for mat, change_info in sorted(materii.items()):
                            change_type = change_info.get('type', 'unknown')
                            grade_val = change_info.get('grade', 'N/A')
                            date_val = change_info.get('date', '')
                            
                            if change_type == 'new':
                                f.write(f"  ✅ [NOU] {an} / {sem} / {mat} = {grade_val} ({date_val})\n")
                            elif change_type == 'modified':
                                old_grade = change_info.get('old_grade', '?')
                                f.write(f"  🗑️ [MODIFICAT] {an} / {sem} / {mat}: {old_grade} → {grade_val} ({date_val})\n")
                f.write("\n")
        except Exception as e:
            print(f"❌ Eroare la scrierea în fișierul de log: {e}")


class JsonFileGradeStorage(IGradeStorage):
    """ Implementare concretă pentru stocare persistentei în fișiere JSON (LSP) """
    
    def __init__(self, note_file: str) -> None:
        self.note_file: str = note_file

    def load_history(self) -> Optional[Dict]:
        if not os.path.exists(self.note_file):
            return None
        try:
            with open(self.note_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Detecție și auto-migrare format vechi plat
            is_old_format = False
            if isinstance(data, dict):
                for k, v in data.items():
                    if not isinstance(v, dict):
                        is_old_format = True
                        break
            else:
                is_old_format = True
                
            if is_old_format:
                print("🔄 Formatul vechi al notelor a fost detectat local. Se va auto-migra la prima salvare...")
                return None  # Îl forțăm să se rescrie în format nou
                
            return data
        except Exception as e:
            print(f"❌ Eroare la citirea istoricului local: {e}")
            return None

    def save_history(self, grades: Dict) -> None:
        try:
            with open(self.note_file, 'w', encoding='utf-8') as f:
                json.dump(grades, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"❌ Eroare la salvarea istoricului local: {e}")


class GradePortalHtmlParser(IGradeParser):
    """ Implementare concretă ce utilizează BeautifulSoup pentru a parseza structura portalului academic (LSP) """
    
    def parse_grades(self, html_content: str) -> Dict:
        soup = BeautifulSoup(html_content, 'html.parser')
        note_structurate: Dict = {}
        
        panels = soup.select('div.panel.panel-default')
        for panel in panels:
            heading_tag = panel.find('div', class_='panel-heading')
            if not heading_tag:
                continue
            
            heading_id = heading_tag.get('id', '')
            if not heading_id or not heading_id.startswith('panelHeading'):
                continue
            
            suffix = heading_id[len('panelHeading'):]
            body_id = f'collapseHeading{suffix}'
            body_tag = soup.find('div', id=body_id)
            if not body_tag:
                continue
                
            heading_text = heading_tag.get_text(separator=" ", strip=True)
            year_match = re.search(r'(\d{4}\s*-\s*\d{4})', heading_text)
            an_match = re.search(r'Anul:\s*(\d+)', heading_text)
            
            if year_match and an_match:
                nume_an = f"{year_match.group(1).strip()} (Anul {an_match.group(1).strip()})"
            elif year_match:
                nume_an = year_match.group(1).strip()
            else:
                nume_an = heading_text.split(',')[0].strip()
                
            note_structurate[nume_an] = {}
            
            content_container = body_tag.find('div', class_='content-container')
            if not content_container:
                continue
                
            current_semester = "Semestrul Necunoscut"
            for child in content_container.children:
                if not child.name:
                    continue
                
                classes = child.get('class', [])
                if 'adm-card' not in classes:
                    continue
                    
                text_complet = child.get_text(separator="||")
                linii = [l.strip() for l in text_complet.split("||") if l.strip()]
                
                if "Semestrul:" in linii:
                    try:
                        idx_sem = linii.index("Semestrul:")
                        sem_val = linii[idx_sem + 1]
                        current_semester = f"Semestrul {sem_val}"
                    except (ValueError, IndexError):
                        current_semester = "Semestrul Necunoscut"
                    
                    if current_semester not in note_structurate[nume_an]:
                        note_structurate[nume_an][current_semester] = {}
                    continue
                
                if "Denumire:" in linii and "Nota:" in linii:
                    try:
                        idx_mat = linii.index("Denumire:")
                        materie = linii[idx_mat + 1]
                    except (ValueError, IndexError):
                        continue
                        
                    try:
                        idx_date = linii.index("Data examinării:")
                        date_val = linii[idx_date + 1]
                        if date_val == "Nota:":
                            date_val = ""
                    except (ValueError, IndexError):
                        date_val = ""
                        
                    try:
                        idx_nota = linii.index("Nota:")
                        nota_val = linii[idx_nota + 1]
                        if nota_val == "Credite:":
                            nota_val = "Neexaminat"
                    except (ValueError, IndexError):
                        nota_val = "Neexaminat"
                    
                    if current_semester not in note_structurate[nume_an]:
                        note_structurate[nume_an][current_semester] = {}
                        
                    note_structurate[nume_an][current_semester][materie] = {
                        "date": date_val,
                        "grade": nota_val
                    }
                    
        return note_structurate


class GradePortalWebClient(IWebClient):
    """ Client HTTP care interacționează cu rețeaua și sesiunile portalului academic (LSP) """
    
    def __init__(self, config: Config) -> None:
        self._config: Config = config
        self.session: requests.Session = requests.Session()
        self.session.headers.update({
            'User-Agent': self._config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': self._config.base_url,
            'Referer': self._config.login_url
        })

    @property
    def config(self) -> Config:
        return self._config

    def authenticate(self) -> bool:
        # Pasul 1: Inițializăm session/cookie accesând pagina de login
        self.session.get(self._config.login_url, timeout=15)
        
        api_headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        # Pasul 2: Trimitem CNP/Utilizator
        payload_pas_1 = {
            'step': 'cnp',
            'type': '',
            'inputCNP': self._config.utilizator
        }
        r2 = self.session.post(self._config.api_url, data=payload_pas_1, headers=api_headers, timeout=15)
        try:
            res2 = r2.json()
            if res2.get("code") != "200-OK" or res2.get("next_action") != "pass":
                msg = res2.get("msgcode", "Eroare la verificarea utilizatorului.")
                clean_msg = BeautifulSoup(msg, "html.parser").get_text(separator=" ")
                print(f"❌ Verificare Utilizator Eșuată: {clean_msg.strip()}")
                return False
        except Exception as e:
            print(f"❌ Eroare la citirea răspunsului API (Pas 1): {e}")
            return False
            
        # Pasul 3: Trimitem parola
        payload_pas_2 = {
            'step': 'pass',
            'type': self._config.rola_student,
            'inputCNP': self._config.utilizator,
            'inputType': self._config.rola_student,
            'inputPass': self._config.parola
        }
        r3 = self.session.post(self._config.api_url, data=payload_pas_2, headers=api_headers, timeout=15)
        try:
            res3 = r3.json()
            if res3.get("code") == "200-OK" and res3.get("next_action") == "dashboard":
                return True
            else:
                msg = res3.get("msgcode", "Parolă incorectă sau eroare de autentificare.")
                clean_msg = BeautifulSoup(msg, "html.parser").get_text(separator=" ")
                print(f"❌ Autentificare Eșuată: {clean_msg.strip()}")
                return False
        except Exception as e:
            print(f"❌ Eroare la citirea răspunsului API (Pas 2): {e}")
            return False

    def fetch_dashboard(self) -> str:
        r = self.session.get(self._config.dashboard_url, timeout=15)
        return r.text


class GitHubUpdateChecker:
    """Checks for new GradeRemind releases on GitHub"""
    
    def __init__(self, current_version: str, owner: str = "andreisugu", repo: str = "GradeRemind"):
        self.current_version = current_version
        self.owner = owner
        self.repo = repo
    
    def check_for_updates(self) -> Optional[Dict[str, str]]:
        """
        Checks GitHub releases API for newer version.
        Returns: {version: "x.y.z", url: "https://github.com/..."} or None
        """
        try:
            response = requests.get(
                f"https://api.github.com/repos/{self.owner}/{self.repo}/releases/latest",
                headers={"User-Agent": "GradeRemind-Update-Checker"},
                timeout=5
            )
            if response.status_code == 200:
                latest = response.json()
                latest_version = latest["tag_name"].lstrip("v")
                
                if self._is_newer(latest_version):
                    return {
                        "version": latest_version,
                        "url": latest["html_url"],
                        "notes": latest.get("body", "")
                    }
        except Exception:
            # Silently fail - don't block startup
            pass
        return None
    
    def _is_newer(self, other: str) -> bool:
        """Compare semantic versions: current < other?"""
        try:
            current_parts = list(map(int, self.current_version.split(".")))
            other_parts = list(map(int, other.split(".")))
            max_len = max(len(current_parts), len(other_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            other_parts.extend([0] * (max_len - len(other_parts)))
            return tuple(other_parts) > tuple(current_parts)
        except Exception:
            return False

