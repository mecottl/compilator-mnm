# gui/results_panel.py - Panel de resultados
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import List, Dict, Any
from models import Error


class ResultsPanel:
    """Panel con pestañas para mostrar resultados de compilación"""
    
    def __init__(self, parent, colors: dict):
        self.colors = colors
        self.frame = ttk.Frame(parent)
        
        self.notebook = None
        self.error_tree = None
        self.token_tree = None
        self.output_text = None
        self.triple_tree = None # Volvemos a un solo árbol
        
        self._create_widgets()
    
    def _create_widgets(self):
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill='both', expand=True)
        
        self._create_errors_tab()
        self._create_tokens_tab()
        self._create_output_tab()
        self._create_triplos_tab() # Solo una pestaña
    
    def _create_errors_tab(self):
        # (Igual que antes...)
        errors_frame = ttk.Frame(self.notebook)
        self.notebook.add(errors_frame, text="❌ Errores")
        errors_frame.rowconfigure(1, weight=1)
        errors_frame.columnconfigure(0, weight=1)
        
        error_label = ttk.Label(errors_frame, text="Tabla de errores:", style='Title.TLabel')
        error_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        columns = ('Token', 'Lexema', 'Renglón', 'Descripción')
        self.error_tree = ttk.Treeview(errors_frame, columns=columns, show='headings', style='Custom.Treeview')
        self.error_tree.heading('Token', text='Token')
        self.error_tree.heading('Lexema', text='Lexema')
        self.error_tree.heading('Renglón', text='Renglón')
        self.error_tree.heading('Descripción', text='Descripción')
        
        self.error_tree.column('Token', width=60, anchor='center')
        self.error_tree.column('Lexema', width=120, anchor='center')
        self.error_tree.column('Renglón', width=80, anchor='center')
        self.error_tree.column('Descripción', width=400, anchor='w')
        
        error_scrollbar = ttk.Scrollbar(errors_frame, orient="vertical", command=self.error_tree.yview)
        self.error_tree.configure(yscrollcommand=error_scrollbar.set)
        self.error_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        error_scrollbar.grid(row=1, column=1, sticky="ns", pady=5)
    
    def _create_tokens_tab(self):
        # (Igual que antes...)
        tokens_frame = ttk.Frame(self.notebook)
        self.notebook.add(tokens_frame, text="🔤 Tabla de símbolos")
        tokens_frame.rowconfigure(1, weight=1)
        tokens_frame.columnconfigure(0, weight=1)
        
        token_label = ttk.Label(tokens_frame, text="Tabla de símbolos (nombre, tipo):", style='Title.TLabel')
        token_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        columns = ('Lexema', 'Tipo de dato')
        self.token_tree = ttk.Treeview(tokens_frame, columns=columns, show='headings', style='Custom.Treeview')
        for col in columns:
            self.token_tree.heading(col, text=col)
        
        self.token_tree.column('Lexema', width=180, anchor='center')
        self.token_tree.column('Tipo de dato', width=120, anchor='center')
        
        token_scrollbar = ttk.Scrollbar(tokens_frame, orient="vertical", command=self.token_tree.yview)
        self.token_tree.configure(yscrollcommand=token_scrollbar.set)
        self.token_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        token_scrollbar.grid(row=1, column=1, sticky="ns", pady=5)
    
    def _create_output_tab(self):
        # (Igual que antes...)
        output_frame = ttk.Frame(self.notebook)
        self.notebook.add(output_frame, text="▶️ Salida")
        output_frame.rowconfigure(1, weight=1)
        output_frame.columnconfigure(0, weight=1)
        
        output_label = ttk.Label(output_frame, text="Salida de ejecución:", style='Title.TLabel')
        output_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, font=('Consolas', 10),
                                                     background=self.colors['bg_editor'], foreground=self.colors['success'],
                                                     state='disabled', relief='flat')
        self.output_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    # --- VOLVEMOS A UNA SOLA PESTAÑA DE TRIPLOS ---
    def _create_triplos_tab(self):
        triplos_frame = ttk.Frame(self.notebook)
        self.notebook.add(triplos_frame, text="📜 Triplos")
        
        triplos_frame.rowconfigure(1, weight=1)
        triplos_frame.columnconfigure(0, weight=1)
        
        triplos_label = ttk.Label(triplos_frame, text="Lista de triplos (índice, operador, DO, DF):", style='Title.TLabel')
        triplos_label.grid(row=0, column=0, sticky="w", padx=4, pady=4)
        
        columns = ('#', 'Operador', 'DO', 'DF')
        self.triple_tree = ttk.Treeview(triplos_frame, columns=columns, show='headings', style='Custom.Treeview')
        
        for col, w, anchor in (('#', 60, 'center'), ('Operador', 120, 'center'), ('DO', 120, 'center'), ('DF', 120, 'center')):
            self.triple_tree.heading(col, text=col)
            self.triple_tree.column(col, width=w, anchor=anchor)
        
        triple_scrollbar = ttk.Scrollbar(triplos_frame, orient="vertical", command=self.triple_tree.yview)
        self.triple_tree.configure(yscrollcommand=triple_scrollbar.set)
        self.triple_tree.grid(row=1, column=0, sticky="nsew", padx=4, pady=5)
        triple_scrollbar.grid(row=1, column=1, sticky="ns", pady=4)

    def show_triplos(self, lista_triplos: List[tuple]):
        """Muestra la lista de triplos en la tabla"""
        if not self.triple_tree: return
        for item in self.triple_tree.get_children():
            self.triple_tree.delete(item)
        
        for idx, triplo in enumerate(lista_triplos, start=1):
            op, arg1, arg2 = triplo
            arg1_display = arg1 if arg1 is not None else ""
            arg2_display = arg2 if arg2 is not None else ""
            self.triple_tree.insert('', 'end', values=(idx, op, arg1_display, arg2_display))
    # ----------------------------------------------

    def show_errors(self, errores: List[Error]):
        for item in self.error_tree.get_children(): self.error_tree.delete(item)
        for error in errores:
            lexema = error.lexema if hasattr(error, 'lexema') and error.lexema is not None else ""
            descripcion = error.mensaje
            renglon = error.linea if hasattr(error, 'linea') and error.linea is not None else ""
            self.error_tree.insert('', 'end', values=(error.token, lexema, renglon, descripcion))
    
    def show_symbols(self, tabla_simbolos: Dict[str, Dict[str, Any]]):
        from constants import CANONICAL_TO_SOURCE
        for item in self.token_tree.get_children(): self.token_tree.delete(item)
        for nombre, info in tabla_simbolos.items():
            tipo_dato = info.get('tipo', '')
            tipo_dato = CANONICAL_TO_SOURCE.get(tipo_dato, tipo_dato)
            self.token_tree.insert('', 'end', values=(nombre, tipo_dato))
    
    def show_output(self, salida: List[str], has_errors: bool):
        self.output_text.config(state='normal')
        self.output_text.delete('1.0', 'end')
        if salida:
            for linea in salida: self.output_text.insert('end', linea + '\n')
        else:
            if not has_errors: self.output_text.insert('end', "No hay salida de ejecución.\n")
            else: self.output_text.insert('end', "Código con errores - no se ejecutó.\n")
        self.output_text.config(state='disabled')
    
    def clear_all(self):
        for item in self.error_tree.get_children(): self.error_tree.delete(item)
        for item in self.token_tree.get_children(): self.token_tree.delete(item)
        if self.triple_tree:
            for item in self.triple_tree.get_children(): self.triple_tree.delete(item)
        self.output_text.config(state='normal')
        self.output_text.delete('1.0', 'end')
        self.output_text.config(state='disabled')

    def select_tab(self, index: int): self.notebook.select(index)
    def bind_error_double_click(self, callback): self.error_tree.bind('<Double-1>', callback)
    def get_selected_error_line(self) -> int:
        selection = self.error_tree.selection()
        if selection:
            item = self.error_tree.item(selection[0])
            try: return int(item['values'][2])
            except: pass
        return 0
    def pack(self, **kwargs): self.frame.pack(**kwargs)
    def grid(self, **kwargs): self.frame.grid(**kwargs)