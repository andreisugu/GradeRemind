from abc import ABC, abstractmethod
from typing import Dict, Optional
from src.config import Config

class INotificationProvider(ABC):
    """ Interfață pentru transmiterea alertelor (ISP, DIP) """
    
    @abstractmethod
    def notify(self, subject: str, grade: str) -> None:
        """ Trimite o alertă când s-a modificat/pus o notă """
        pass


class IGradeLogger(ABC):
    """ Interfață pentru jurnalizarea activității / notelor curente (ISP, DIP) """
    
    @abstractmethod
    def log_changes(self, changes: Dict) -> None:
        """ Jurnalizează doar modificările detectate (note noi sau actualizate) """
        pass


class IGradeStorage(ABC):
    """ Interfață pentru stocarea persistenței istoricului notelor (ISP, DIP) """
    
    @abstractmethod
    def load_history(self) -> Optional[Dict]:
        """ Încarcă istoricul notelor salvate local """
        pass

    @abstractmethod
    def save_history(self, grades: Dict) -> None:
        """ Salvează istoricul notelor local """
        pass


class IGradeParser(ABC):
    """ Interfață pentru prelucrarea și extragerea notelor din pagină (ISP, DIP) """
    
    @abstractmethod
    def parse_grades(self, html_content: str) -> Dict:
        """ Extrage notele structurate pe ani și semestre din HTML-ul paginii """
        pass


class IWebClient(ABC):
    """ Interfață pentru interactiunea cu rețeaua/platforma academică (ISP, DIP) """
    
    @property
    @abstractmethod
    def config(self) -> Config:
        """ Returnează obiectul de configurare """
        pass

    @abstractmethod
    def authenticate(self) -> bool:
        """ Realizează autentificarea pe platformă """
        pass

    @abstractmethod
    def fetch_dashboard(self) -> str:
        """ Returnează conținutul HTML al dashboard-ului """
        pass


class IWebServer(ABC):
    """ Interfață pentru serverul web al dashboard-ului (ISP, DIP) """
    
    @abstractmethod
    def start(self) -> None:
        """ Pornește serverul web """
        pass

    @abstractmethod
    def stop(self) -> None:
        """ Oprește serverul web """
        pass
