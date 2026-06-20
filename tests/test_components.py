import unittest
from unittest.mock import MagicMock
from src.services import CompositeNotificationProvider, GradePortalHtmlParser
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

if __name__ == "__main__":
    unittest.main()
