# gui/styles.py - Estilos y colores de la interfaz
from tkinter import ttk


class AppStyles:
    """Gestiona los estilos visuales de la aplicación"""
    
    def __init__(self):
        self.colors = {
            'bg_editor': '#80445b',   # Verde medio
            'fg_text': "#fff",           # Blanco para texto
            'fg_title': "#ffffff",       # Verde oscuro para títulos
            'fg_secondary': '#FB5C87',   # Verde pálido para secundarios
            'accent': '#43a047',         # Verde acento
            'error': '#B8052B',          # Rojo para errores
            'success': "#ffffff",        # Blanco para éxito
            'warning': '#ffa726'         # Naranja para advertencias
        }
    
    def setup_ttk_styles(self, style: ttk.Style):
        """Configura los estilos de ttk"""
        try:
            style.theme_use('clam')
        except:
            pass
        
        # Estilo para títulos
        style.configure('Title.TLabel',
                       foreground=self.colors['fg_title'],
                       font=('Arial', 12, 'bold'))
        
        # Estilo para Treeview
        style.configure('Custom.Treeview',
                       background=self.colors['bg_editor'],
                       foreground=self.colors['fg_text'],
                       fieldbackground=self.colors['bg_editor'])
    
    def get_color(self, key: str) -> str:
        """Obtiene un color por su clave"""
        return self.colors.get(key, '#000000')