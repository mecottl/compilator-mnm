# gui/main_window.py - Ventana principal de la aplicación
import tkinter as tk
from tkinter import ttk, messagebox
from gui.styles import AppStyles
from gui.editor_panel import EditorPanel
from gui.results_panel import ResultsPanel
from compiler import analizar_codigo


class MainWindow:
    """Ventana principal del compilador"""
    
    def __init__(self, root):
        self.root = root
        self.styles = AppStyles()
        # Variables de estado
        self.errores_actuales = []
        self.tokens_actuales = []
        self.info_adicional = {}
        
        # Componentes de la interfaz
        self.editor_panel = None
        self.results_panel = None
        self.status_text = None
        self.info_text = None
        
        # Configurar aplicación
        self._setup_window()
        self._setup_styles()
        self._create_widgets()
        
        # Cargar ejemplo después de inicialización
        self.root.after(200, self._load_example_safe)
    
    def _setup_window(self):
        """Configuración inicial de la ventana"""
        self.root.title("mnmCompilador")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
    
    def _setup_styles(self):
        """Configuración de estilos"""
        style = ttk.Style()
        self.styles.setup_ttk_styles(style)
        fondo_general = "#683144"  
        
        style.configure("TFrame", background=fondo_general)
        style.configure("TPanedwindow", background=fondo_general)
        style.configure("TNotebook", background=fondo_general)
        style.configure("TNotebook.Tab", background=fondo_general)
        style.configure("CustomPaned.TPanedwindow", background=fondo_general)
        
        # Opcional: estilo para etiquetas y botones (tema oscuro)
        style.configure("TLabel", background=fondo_general, foreground="white")
        style.configure("TButton", background="#2d2d2d", foreground="white")
        style.map("TButton",
                  background=[("active", "#3c3c3c")],
                  foreground=[("active", "white")])
    
    def _create_widgets(self):
        """Crea todos los widgets de la interfaz"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Crear secciones
        self._create_header(main_frame)
        self._create_content_area(main_frame)
        self._create_status_bar(main_frame)
    
    def _create_header(self, parent):
        """Crea la barra de herramientas superior"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Título
        title_label = ttk.Label(header_frame, text="mnmCompilador",
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky="w")
        
        # Botones
        button_frame = ttk.Frame(header_frame)
        button_frame.grid(row=0, column=1, sticky="e")
        
        ttk.Button(button_frame, text="Compilar",
                  command=self.compile_code).grid(row=0, column=0, padx=2)
        
        ttk.Button(button_frame, text="Limpiar",
                  command=self.clear_all).grid(row=0, column=1, padx=2)
        
        ttk.Button(button_frame, text="Ejemplo",
                  command=self.load_example).grid(row=0, column=2, padx=2)
        
        header_frame.columnconfigure(1, weight=1)
    
    def _create_content_area(self, parent):
        """Crea el área principal de contenido"""
        paned_window = ttk.PanedWindow(parent, orient=tk.HORIZONTAL, style="CustomPaned.TPanedwindow")
        paned_window.grid(row=1, column=0, sticky="nsew")
        
        # Panel izquierdo - Editor
        self.editor_panel = EditorPanel(paned_window, self.styles.colors)
        paned_window.add(self.editor_panel.frame, weight=2)
        
        # Vincular eventos del editor
        self.editor_panel.bind_events(
            self._on_text_change,
            self._on_scroll
        )
        
        # Panel derecho - Resultados
        self.results_panel = ResultsPanel(paned_window, self.styles.colors)
        paned_window.add(self.results_panel.frame, weight=3)
        
        # Vincular doble click en errores
        self.results_panel.bind_error_double_click(self._goto_error_line)
    
    def _create_status_bar(self, parent):
        """Crea la barra de estado"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        
        # Variables de estado
        self.status_text = tk.StringVar()
        self.status_text.set("Listo para compilar")
        
        self.info_text = tk.StringVar()
        self.info_text.set("Líneas: 0 | Errores: 0 | Tokens: 0")
        
        # Etiquetas
        ttk.Label(status_frame, textvariable=self.status_text).grid(
            row=0, column=0, sticky="w"
        )
        
        info_frame = ttk.Frame(status_frame)
        info_frame.grid(row=0, column=1, sticky="e")
        
        ttk.Label(info_frame, textvariable=self.info_text).grid(
            row=0, column=0
        )
        
        status_frame.columnconfigure(1, weight=1)
    
    # ========== EVENTOS ==========
    
    def _on_text_change(self, event=None):
        """Maneja cambios en el texto"""
        try:
            self.editor_panel.update_line_numbers()
            self._update_status()
        except:
            pass
    
    def _on_scroll(self, event):
        """Maneja el scroll del mouse"""
        try:
            delta = int(-1 * (event.delta / 120))
            self.editor_panel.line_numbers.yview_scroll(delta, "units")
            self.editor_panel.text_editor.yview_scroll(delta, "units")
        except:
            pass
    
    def _goto_error_line(self, event):
        """Va a la línea del error al hacer doble click"""
        linea = self.results_panel.get_selected_error_line()
        if linea > 0:
            self.editor_panel.goto_line(linea)
    
    # ========== ACCIONES ==========
    
    def compile_code(self):
        """Compila el código actual"""
        try:
            codigo = self.editor_panel.get_code()
            
            if not codigo.strip():
                messagebox.showwarning("Advertencia", "No hay código para compilar")
                return
            
            # Actualizar estado
            self.status_text.set("Compilando...")
            self.root.update()
            
            # Limpiar errores visuales anteriores
            self.editor_panel.clear_error_highlights()
            
            # Ejecutar análisis
            self.errores_actuales, self.tokens_actuales, self.info_adicional = \
                analizar_codigo(codigo)
            
            # Actualizar interfaz
            self._show_results()
            
            # Actualizar estado
            if self.errores_actuales:
                self.status_text.set(
                    f"Compilación completada con {len(self.errores_actuales)} error(es)"
                )
                self.results_panel.select_tab(0)  # Pestaña de errores
            else:
                self.status_text.set("Compilación exitosa - Código analizado")
                self.results_panel.select_tab(2)  # Pestaña de salida
            
            self._update_status()
        
        except Exception as e:
            messagebox.showerror("Error", f"Error durante la compilación: {str(e)}")
            self.status_text.set("Error en compilación")
    
    def _show_results(self):
        """Muestra los resultados de la compilación"""
        # Mostrar errores
        self.results_panel.show_errors(self.errores_actuales)
        
        # Resaltar líneas con error
        for error in self.errores_actuales:
            if hasattr(error, 'linea') and error.linea:
                self.editor_panel.highlight_error_line(error.linea)
        
        # Mostrar tabla de símbolos
        tabla_simbolos = self.info_adicional.get('tabla_simbolos', {})
        self.results_panel.show_symbols(tabla_simbolos)
        
        # Mostrar salida
        salida = self.info_adicional.get('salida_ejecucion', [])
        self.results_panel.show_output(salida, len(self.errores_actuales) > 0)
    
    def clear_all(self):
        """Limpia todo el contenido"""
        # Limpiar editor
        self.editor_panel.clear()
        
        # Limpiar resultados
        self.results_panel.clear_all()
        
        # Reiniciar variables
        self.errores_actuales = []
        self.tokens_actuales = []
        self.info_adicional = {}
        
        # Actualizar estado
        self.status_text.set("Todo limpiado - Listo para nuevo código")
        self._update_status()
    
    def load_example(self):
        """Carga código de ejemplo"""
        ejemplo = r"""\ent mnmI = 0;

print("--- Inicio del bucle ---");

for(mnmI = 1; mnmI <= 3; mnmI = mnmI + 1):{
    print("Iteracion numero:");
    print(mnmI);
}

print("--- Fin del bucle ---");"""
        
        self.editor_panel.set_code(ejemplo)
        self.status_text.set("Ejemplo cargado - Presiona 'Compilar' para probar")
        self._update_status()
    
    def _load_example_safe(self):
        """Carga ejemplo de forma segura"""
        try:
            self.load_example()
        except Exception as e:
            print(f"Error cargando ejemplo: {e}")
    
    def _update_status(self):
        """Actualiza la información de la barra de estado"""
        try:
            num_lines = self.editor_panel.get_num_lines()
            self.info_text.set(
                f"Líneas: {num_lines} | "
                f"Errores: {len(self.errores_actuales)} | "
                f"Tokens: {len(self.tokens_actuales)}"
            )
        except:
            pass
