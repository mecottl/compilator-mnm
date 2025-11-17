# gui/editor_panel.py - Panel del editor de código
import tkinter as tk
from tkinter import ttk, scrolledtext

# Prefijo que usa el optimizador
OPTIMIZED_PREFIX = "//OPTIMIZADO: "

class EditorPanel:
    """
    Panel del editor con pestañas para "Original" y "Optimizado".
    """
    
    def __init__(self, parent, colors: dict):
        self.colors = colors
        self.frame = ttk.Frame(parent)
        
        self.notebook = None
        self.original_editor = None
        self.original_line_numbers = None
        self.optimized_editor = None
        self.optimized_line_numbers = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea los widgets del editor"""
        self.frame.rowconfigure(1, weight=1)
        self.frame.columnconfigure(0, weight=1)
        
        code_label = ttk.Label(self.frame, text="Editor de Código",
                              style='Title.TLabel')
        code_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        # Pestaña 1: Código Original
        original_frame = ttk.Frame(self.notebook)
        self.notebook.add(original_frame, text="Código Original")
        self.original_editor, self.original_line_numbers = self._create_editor_tab(original_frame, editable=True)
        
        # Pestaña 2: Código Optimizado
        optimized_frame = ttk.Frame(self.notebook)
        self.notebook.add(optimized_frame, text="Código Optimizado")
        self.optimized_editor, self.optimized_line_numbers = self._create_editor_tab(optimized_frame, editable=False)

    def _create_editor_tab(self, parent_frame, editable=True) -> (scrolledtext.ScrolledText, tk.Text):
        parent_frame.rowconfigure(0, weight=1)
        parent_frame.columnconfigure(1, weight=1)
        
        line_numbers = tk.Text(
            parent_frame, width=4, padx=3, takefocus=0,
            border=0, state='disabled', wrap='none',
            background=self.colors['bg_editor'],
            foreground=self.colors['fg_secondary'],
            font=('Consolas', 11)
        )
        line_numbers.grid(row=0, column=0, sticky="ns")
        
        text_editor = scrolledtext.ScrolledText(
            parent_frame,
            wrap=tk.NONE,
            font=('Consolas', 11),
            background=self.colors['bg_editor'],
            foreground=self.colors['fg_text'] if editable else self.colors['fg_secondary'],
            insertbackground=self.colors['fg_text'],
            selectbackground=self.colors['accent'],
            relief='flat',
            borderwidth=1
        )
        text_editor.grid(row=0, column=1, sticky="nsew")
        
        if not editable:
            text_editor.config(state='disabled')

        # --- ¡INICIO DE LA MODIFICACIÓN! ---
        # Tags para resaltado
        text_editor.tag_configure('error_line',
                                  background=self.colors['error'],
                                  foreground='white')
        
        # Nuevo tag para líneas optimizadas (eliminadas)
        text_editor.tag_configure('optimized_out',
                                  foreground=self.colors['error'],
                                  font=('Consolas', 10, 'overstrike'))
        # --- FIN DE LA MODIFICACIÓN! ---

        text_editor.configure(
            yscrollcommand=lambda *args, ln=line_numbers: self._on_editor_yscroll(ln, *args)
        )
        
        return text_editor, line_numbers

    def bind_events(self, on_change_callback, on_scroll_callback):
        """Vincula eventos al editor ORIGINAL (el único editable)"""
        editor = self.original_editor
        editor.bind('<KeyRelease>', on_change_callback)
        editor.bind('<Button-1>', on_change_callback)
        editor.bind('<ButtonRelease-1>', on_change_callback)
        editor.bind('<MouseWheel>', lambda e, ed=editor, ln=self.original_line_numbers: on_scroll_callback(e, ed, ln))
        editor.bind('<Return>', 
                         lambda e: (on_change_callback(e), 'break'))
        editor.bind('<Configure>', 
                         lambda e: self.update_line_numbers())
    
    def get_code(self) -> str:
        """Obtiene el código del editor ORIGINAL"""
        return self.original_editor.get('1.0', 'end-1c')
    
    def set_code(self, code: str):
        """Establece el código en el editor ORIGINAL"""
        self.original_editor.config(state='normal')
        self.original_editor.delete('1.0', 'end')
        self.original_editor.insert('1.0', code)
        self.update_line_numbers()
    
    # --- ¡INICIO DE LA MODIFICACIÓN! ---
    def set_optimized_code(self, code: str):
        """Establece el código en el editor OPTIMIZADO y resalta los cambios."""
        self.optimized_editor.config(state='normal')
        self.optimized_editor.delete('1.0', 'end')
        self.optimized_editor.insert('1.0', code)
        
        # Resaltar las líneas optimizadas
        self.highlight_optimized_lines()
        
        self.optimized_editor.config(state='disabled', foreground=self.colors['fg_text'])
        self.update_line_numbers(optimized=True)

    def highlight_optimized_lines(self):
        """Busca líneas con el prefijo y aplica el tag 'optimized_out'."""
        self.optimized_editor.tag_remove('optimized_out', '1.0', 'end')
        
        start = '1.0'
        while True:
            pos = self.optimized_editor.search(OPTIMIZED_PREFIX, start, 'end')
            if not pos:
                break
            
            line_start = pos.split('.')[0] + '.0'
            line_end = pos.split('.')[0] + '.end'
            self.optimized_editor.tag_add('optimized_out', line_start, line_end)
            
            start = line_end
    # --- FIN DE LA MODIFICACIÓN! ---

    def clear(self):
        """Limpia ambos editores"""
        self.original_editor.delete('1.0', 'end')
        self.optimized_editor.config(state='normal')
        self.optimized_editor.delete('1.0', 'end')
        self.optimized_editor.config(state='disabled', foreground=self.colors['fg_text'])        
        self.clear_error_highlights()
        self.update_line_numbers()
        self.update_line_numbers(optimized=True)

    def update_line_numbers(self, optimized=False):
        """Actualiza los números de línea para un editor"""
        if optimized:
            editor = self.optimized_editor
            line_numbers = self.optimized_line_numbers
        else:
            editor = self.original_editor
            line_numbers = self.original_line_numbers

        if not line_numbers or not editor:
            return
        
        try:
            line_numbers.config(state='normal')
            line_numbers.delete('1.0', 'end')
            
            num_lines = int(editor.index('end-1c').split('.')[0])
            
            line_numbers_text = '\n'.join(str(i) for i in range(1, num_lines + 1))
            line_numbers.insert('1.0', line_numbers_text)
            line_numbers.config(state='disabled')
            
            line_numbers.yview_moveto(editor.yview()[0])
        except Exception:
            pass
    
    def _on_editor_yscroll(self, line_numbers, *args):
        """Sincroniza el scroll de números de línea"""
        try:
            frac = args[0]
            line_numbers.yview_moveto(frac)
        except:
            pass
    
    # --- ¡INICIO DE LA MODIFICACIÓN! ---
    def highlight_error_line(self, linea_original: int):
        """Resalta una línea con error en el editor ORIGINAL"""
        try:
            line_start = f"{linea_original}.0"
            line_end = f"{linea_original}.end"
            self.original_editor.tag_add('error_line', line_start, line_end)
        except:
            pass
    # --- FIN DE LA MODIFICACIÓN! ---
    
    def clear_error_highlights(self):
        """Limpia todos los resaltados de error"""
        self.original_editor.tag_remove('error_line', '1.0', 'end')
        self.optimized_editor.tag_remove('error_line', '1.0', 'end')
    
    # --- ¡INICIO DE LA MODIFICACIÓN! ---
    def goto_line(self, linea_original: int):
        """Va a una línea específica en el editor ORIGINAL"""
        try:
            self.original_editor.mark_set('insert', f"{linea_original}.0")
            self.original_editor.see(f"{linea_original}.0")
            self.original_editor.focus()
            self.notebook.select(0) # Selecciona la pestaña de "Código Original"
        except:
            pass
    # --- FIN DE LA MODIFICACIÓN! ---
    
    def get_num_lines(self) -> int:
        """Obtiene el número de líneas del editor ORIGINAL"""
        try:
            content = self.get_code()
            if content.strip():
                return int(self.original_editor.index('end-1c').split('.')[0])
            return 0
        except:
            return 0
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.frame.grid(**kwargs)