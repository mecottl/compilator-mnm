# gui/__init__.py - Inicialización del módulo GUI
from gui.main_window import MainWindow
from gui.styles import AppStyles
from gui.editor_panel import EditorPanel
from gui.results_panel import ResultsPanel

__all__ = ['MainWindow', 'AppStyles', 'EditorPanel', 'ResultsPanel']