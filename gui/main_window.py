# gui/main_window.py - Ventana principal de la aplicación
import tkinter as tk
from tkinter import ttk, messagebox
from gui.styles import AppStyles
from gui.editor_panel import EditorPanel
from gui.results_panel import ResultsPanel
from compiler import analizar_codigo
from text_optimizer import TextOptimizer # Asegúrate de que esta importación esté


class MainWindow:
    """Ventana principal del compilador"""
    
    def __init__(self, root):
        self.root = root
        self.styles = AppStyles()
        # Variables de estado
        self.errores_actuales = []
        self.tokens_actuales = []
        self.info_adicional = {}
        
        # --- ¡INICIO DE LA MODIFICACIÓN! ---
        self.line_map = {} # Guardará el mapa de líneas del optimizador
        # --- FIN DE LA MODIFICACIÓN! ---
        
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
        style = ttk.Style()
        self.styles.setup_ttk_styles(style)
        fondo_general = "#683144"  
        
        style.configure("TFrame", background=fondo_general)
        style.configure("TPanedwindow", background=fondo_general)
        style.configure("TNotebook", background=fondo_general)
        style.configure("TNotebook.Tab", background=fondo_general)
        style.configure("CustomPaned.TPanedwindow", background=fondo_general)
        
        style.configure("TLabel", background=fondo_general, foreground="white")
        style.configure("TButton", background="#2d2d2d", foreground="white")
        style.map("TButton",
                  background=[("active", "#3c3c3c")],
                  foreground=[("active", "white")])
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        self._create_header(main_frame)
        self._create_content_area(main_frame)
        self._create_status_bar(main_frame)
    
    def _create_header(self, parent):
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        title_label = ttk.Label(header_frame, text="mnmCompilador",
                                style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky="w")
        
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
        paned_window = ttk.PanedWindow(parent, orient=tk.HORIZONTAL, style="CustomPaned.TPanedwindow")
        paned_window.grid(row=1, column=0, sticky="nsew")
        
        self.editor_panel = EditorPanel(paned_window, self.styles.colors)
        paned_window.add(self.editor_panel.frame, weight=2)
        
        self.editor_panel.bind_events(
            self._on_text_change,
            self._on_scroll 
        )
        
        self.results_panel = ResultsPanel(paned_window, self.styles.colors)
        paned_window.add(self.results_panel.frame, weight=3)
        
        self.results_panel.bind_error_double_click(self._goto_error_line)
    
    def _create_status_bar(self, parent):
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        
        self.status_text = tk.StringVar()
        self.status_text.set("Listo para compilar")
        self.info_text = tk.StringVar()
        self.info_text.set("Líneas: 0 | Errores: 0 | Tokens: 0")
        
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
        try:
            self.editor_panel.update_line_numbers(optimized=False)
            self._update_status()
        except:
            pass
    
    def _on_scroll(self, event, editor, line_numbers):
        try:
            delta = int(-1 * (event.delta / 120))
            line_numbers.yview_scroll(delta, "units")
            editor.yview_scroll(delta, "units")
        except:
            pass
    
    def _goto_error_line(self, event):
        """Va a la línea del error, mapeándola al código original."""
        linea_optimizada = self.results_panel.get_selected_error_line()
        
        linea_original = self.line_map.get(linea_optimizada, 0)
        
        if linea_original > 0:
            self.editor_panel.goto_line(linea_original)
            
    
    # ========== ACCIONES ==========
    
    def compile_code(self):
        """Compila el código actual"""
        try:
            codigo_original = self.editor_panel.get_code()
            
            if not codigo_original.strip():
                messagebox.showwarning("Advertencia", "No hay código para compilar")
                return
            
            self.status_text.set("Optimizando y compilando...")
            self.root.update()
            
            self.editor_panel.clear_error_highlights()
            
            # --- PASO 1: OPTIMIZACIÓN DE TEXTO ---
            optimizer = TextOptimizer(codigo_original)
            codigo_optimizado, self.line_map = optimizer.optimize()
            
            self.editor_panel.set_optimized_code(codigo_optimizado)
            
            # --- PASO 2: ANÁLISIS (SOBRE EL CÓDIGO OPTIMIZADO) ---
            self.errores_actuales, self.tokens_actuales, self.info_adicional = \
                analizar_codigo(codigo_optimizado)
            
            self._show_results()
            
            if self.errores_actuales:
                self.status_text.set(
                    f"Compilación completada con {len(self.errores_actuales)} error(es)"
                )
                self.results_panel.select_tab(0)
            else:
                self.status_text.set("Compilación exitosa - Código analizado")
                self.results_panel.select_tab(2)
            
            self._update_status()
        
        except Exception as e:
            messagebox.showerror("Error", f"Error durante la compilación: {str(e)}")
            self.status_text.set("Error en compilación")
    
    def _show_results(self):
        """Muestra los resultados de la compilación"""
        self.results_panel.show_errors(self.errores_actuales)
        
        for error in self.errores_actuales:
            if hasattr(error, 'linea') and error.linea:
                linea_original = self.line_map.get(error.linea, 0)
                if linea_original > 0:
                    self.editor_panel.highlight_error_line(linea_original)
        
        tabla_simbolos = self.info_adicional.get('tabla_simbolos', {})
        self.results_panel.show_symbols(tabla_simbolos)
        
        salida = self.info_adicional.get('salida_ejecucion', [])
        self.results_panel.show_output(salida, len(self.errores_actuales) > 0)
        
        # --- MODIFICACIÓN ---
        # Solo mostramos una lista de triplos (la optimizada)
        lista_triplos = self.info_adicional.get('lista_triplos', [])
        self.results_panel.show_triplos(lista_triplos)
        # --------------------
    
    def clear_all(self):
        """Limpia todo el contenido"""
        self.editor_panel.clear()
        self.results_panel.clear_all()
        
        self.errores_actuales = []
        self.tokens_actuales = []
        self.info_adicional = {}
        self.line_map = {}
        
        self.status_text.set("Todo limpiado - Listo para nuevo código")
        self._update_status()
    
    def load_example(self):
        """Carga código de ejemplo"""
        ejemplo = r"""\ent mnmA, mnmB, mnmC, mnmD, mnmContador, mnmVal; 
 
\dec mnmX, mnmY, mnmZ,mnml; 
 
\cad mnmS1, mnmS2, mnmS3; 
 
mnmA = 13 
mnmB = 105 
mnmC =  mnmA + mnmB;  
 
mnmX = 100-2 
mnmY = 0.05 
 
mnmS1 = "Hola" 
mnmS2 = "Mundo" 
  
mnmVal= 100-2; 
 
mnmD = mnmA + mnmB;  
 
mnmS3 = "Hola"; 
 
print(mnmS3); 
 
mnmZ = 66 * mnmVal;  
 
for(mnmContador = 1; mnmContador <= mnmD; mnmContador = mnmContador + 1):{ 
    print(mnmZ)
}
"""
        
        self.editor_panel.set_code(ejemplo)
        self.status_text.set("Ejemplo de optimización cargado - Presiona 'Compilar'")
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