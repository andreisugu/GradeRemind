import unittest
from unittest.mock import MagicMock, patch
from src.services import CompositeNotificationProvider, GradePortalHtmlParser, TextFileGradeLogger, GitHubUpdateChecker
from src.interfaces import INotificationProvider

class TestGradeRemindComponents(unittest.TestCase):
    
    def test_composite_notification_provider(self) -> None:
        """ Testează că CompositeNotificationProvider trimite notificarea la toți providerii înregistrați """
        # Arrange
        mock_provider_1 = MagicMock(spec=INotificationProvider)
        mock_provider_2 = MagicMock(spec=INotificationProvider)
        
        composite = CompositeNotificationProvider()
        composite.add_provider(mock_provider_1)
        composite.add_provider(mock_provider_2)
        
        # Act
        composite.notify("Analiza Matematica", "10")
        
        # Assert
        mock_provider_1.notify.assert_called_once_with("Analiza Matematica", "10")
        mock_provider_2.notify.assert_called_once_with("Analiza Matematica", "10")

    def test_html_parser_empty_content(self) -> None:
        """ Testează că parserul returnează un dicționar gol în absența structurii panel-default specifice """
        # Arrange
        parser = GradePortalHtmlParser()
        html = "<html><body>Nicio nota aici. Structura diferita.</body></html>"
        
        # Act
        grades = parser.parse_grades(html)
        
        # Assert
        self.assertEqual(grades, {})
    
    def test_grade_logger_only_logs_changes(self) -> None:
        """ Testează că logger-ul nu scrie nimic când nu sunt modificări """
        import tempfile
        import os
        
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            log_file = f.name
        
        try:
            logger = TextFileGradeLogger(log_file)
            empty_changes = {}  # Nicio modificăre
            
            # Act
            logger.log_changes(empty_changes)
            
            # Assert
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertEqual(content, "")  # Ar trebui să fie gol
        finally:
            os.unlink(log_file)

    @patch('src.services.requests.get')
    def test_update_checker_newer_version(self, mock_get) -> None:
        """ Testează că se detectează o versiune mai nouă disponibilă """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v1.1.0",
            "html_url": "https://github.com/andreisugu/GradeRemind/releases/tag/v1.1.0",
            "body": "Noutati in v1.1.0"
        }
        mock_get.return_value = mock_response
        
        checker = GitHubUpdateChecker(current_version="1.0.0")
        
        # Act
        update = checker.check_for_updates()
        
        # Assert
        self.assertIsNotNone(update)
        self.assertEqual(update["version"], "1.1.0")
        self.assertEqual(update["url"], "https://github.com/andreisugu/GradeRemind/releases/tag/v1.1.0")

    @patch('src.services.requests.get')
    def test_update_checker_no_update_needed(self, mock_get) -> None:
        """ Testează că nu se semnalează actualizare dacă versiunea curentă este egală sau mai mare """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v1.0.0",
            "html_url": "https://github.com/andreisugu/GradeRemind/releases/tag/v1.0.0",
            "body": ""
        }
        mock_get.return_value = mock_response
        
        checker = GitHubUpdateChecker(current_version="1.0.0")
        
        # Act
        update = checker.check_for_updates()
        
        # Assert
        self.assertIsNone(update)

    @patch('src.services.requests.get')
    def test_update_checker_failure_graceful(self, mock_get) -> None:
        """ Testează că erorile de rețea la verificarea actualizărilor sunt tratate silențios """
        # Arrange
        mock_get.side_effect = Exception("Conexiune esuata")
        
        checker = GitHubUpdateChecker(current_version="1.0.0")
        
        # Act
        update = checker.check_for_updates()
        
        # Assert
        self.assertIsNone(update)

    def test_get_template_bytes(self) -> None:
        """ Testează că get_template_bytes poate citi iconița PWA ca fișier de imagine valid """
        from src.web_server import get_template_bytes
        # Act
        icon_bytes = get_template_bytes("icon.png")
        
        # Assert
        self.assertTrue(len(icon_bytes) > 0)
        # Acceptă semnătura PNG sau JPEG (deoarece generatorul poate crea JPEG sub extensia PNG)
        is_png = icon_bytes[:4] == b'\x89PNG'
        is_jpeg = icon_bytes[:2] == b'\xff\xd8'
        self.assertTrue(is_png or is_jpeg)

if __name__ == "__main__":
    unittest.main()
