# gui/editor_panel.py - Panel del editor de código
import tkinter as tk
from tkinter import ttk, scrolledtext


class EditorPanel:
    """Panel del editor de código con números de línea"""
    
    def __init__(self, parent, colors: dict):
        self.colors = colors
        self.frame = ttk.Frame(parent)
        
        # Referencias a widgets
        self.text_editor = None
        self.line_numbers = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea los widgets del editor"""
        # Configurar grid
        self.frame.rowconfigure(1, weight=1)
        self.frame.columnconfigure(0, weight=1)
        
        # Etiqueta del editor
        code_label = ttk.Label(self.frame, text="Editor de Código",
                              style='Title.TLabel')
        code_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # Frame para el editor y números de línea
        editor_frame = ttk.Frame(self.frame)
        editor_frame.grid(row=1, column=0, sticky="nsew")
        editor_frame.rowconfigure(0, weight=1)
        editor_frame.columnconfigure(1, weight=1)
        
        # Área de números de línea
        self.line_numbers = tk.Text(
            editor_frame, width=4, padx=3, takefocus=0,
            border=0, state='disabled', wrap='none',
            background=self.colors['bg_editor'],
            foreground=self.colors['fg_secondary'],
            font=('Consolas', 11)
        )
        self.line_numbers.grid(row=0, column=0, sticky="ns")
        
        # Editor de código principal
        self.text_editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.NONE,
            font=('Consolas', 11),
            background=self.colors['bg_editor'],
            foreground=self.colors['fg_text'],
            insertbackground=self.colors['fg_text'],
            selectbackground=self.colors['accent'],
            relief='flat',
            borderwidth=1
        )
        self.text_editor.grid(row=0, column=1, sticky="nsew")
        
        # Configurar tag para resaltado de errores
        self.text_editor.tag_configure('error_line',
                                      background=self.colors['error'],
                                      foreground='white')
        
        # Configurar sincronización de scroll
        self.text_editor.configure(
            yscrollcommand=lambda *args: self._on_editor_yscroll(*args)
        )
    
    def bind_events(self, on_change_callback, on_scroll_callback):
        """Vincula eventos del editor"""
        self.text_editor.bind('<KeyRelease>', on_change_callback)
        self.text_editor.bind('<Button-1>', on_change_callback)
        self.text_editor.bind('<ButtonRelease-1>', on_change_callback)
        self.text_editor.bind('<MouseWheel>', on_scroll_callback)
        self.text_editor.bind('<Return>', 
                             lambda e: (on_change_callback(e), 'break'))
        self.text_editor.bind('<Configure>', 
                             lambda e: self.update_line_numbers())
    
    def get_code(self) -> str:
        """Obtiene el código del editor"""
        return self.text_editor.get('1.0', 'end-1c')
    
    def set_code(self, code: str):
        """Establece el código en el editor"""
        self.text_editor.delete('1.0', 'end')
        self.text_editor.insert('1.0', code)
        self.update_line_numbers()
    
    def clear(self):
        """Limpia el editor"""
        self.text_editor.delete('1.0', 'end')
        self.clear_error_highlights()
    
    def update_line_numbers(self):
        """Actualiza los números de línea"""
        if not self.line_numbers or not self.text_editor:
            return
        
        try:
            self.line_numbers.config(state='normal')
            self.line_numbers.delete('1.0', 'end')
            
            # Obtener número de líneas
            num_lines = int(self.text_editor.index('end-1c').split('.')[0])
            
            # Agregar números
            line_numbers_text = '\n'.join(str(i) for i in range(1, num_lines + 1))
            self.line_numbers.insert('1.0', line_numbers_text)
            self.line_numbers.config(state='disabled')
            
            # Sincronizar scroll
            try:
                self.line_numbers.yview_moveto(self.text_editor.yview()[0])
            except:
                pass
        except Exception:
            pass
    
    def _on_editor_yscroll(self, *args):
        """Sincroniza el scroll de números de línea con el editor"""
        try:
            frac = self.text_editor.yview()[0]
            self.line_numbers.yview_moveto(frac)
        except:
            pass
    
    def highlight_error_line(self, linea: int):
        """Resalta una línea con error"""
        try:
            line_start = f"{linea}.0"
            line_end = f"{linea}.end"
            self.text_editor.tag_add('error_line', line_start, line_end)
        except:
            pass
    
    def clear_error_highlights(self):
        """Limpia todos los resaltados de error"""
        self.text_editor.tag_remove('error_line', '1.0', 'end')
    
    def goto_line(self, linea: int):
        """Va a una línea específica"""
        try:
            self.text_editor.mark_set('insert', f"{linea}.0")
            self.text_editor.see(f"{linea}.0")
            self.text_editor.focus()
        except:
            pass
    
    def get_num_lines(self) -> int:
        """Obtiene el número de líneas"""
        try:
            content = self.get_code()
            if content.strip():
                return int(self.text_editor.index('end-1c').split('.')[0])
            return 0
        except:
            return 0
    
    def pack(self, **kwargs):
        """Empaqueta el frame principal"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Coloca el frame en grid"""
        self.frame.grid(**kwargs)