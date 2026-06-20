import unittest
from unittest.mock import MagicMock
from src.services import CompositeNotificationProvider, GradePortalHtmlParser, TextFileGradeLogger
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

if __name__ == "__main__":
    unittest.main()
