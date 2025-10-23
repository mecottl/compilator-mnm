# gui/results_panel.py - Panel de resultados (errores, tokens, salida)
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import List, Dict, Any
from models import Error


class ResultsPanel:
    """Panel con pestañas para mostrar resultados de compilación"""
    
    def __init__(self, parent, colors: dict):
        self.colors = colors
        self.frame = ttk.Frame(parent)
        
        # Referencias a widgets
        self.notebook = None
        self.error_tree = None
        self.token_tree = None
        self.output_text = None
        self.triple_tree = None   # <-- añadido
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea los widgets del panel"""
        # Notebook para pestañas
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Crear pestañas
        self._create_errors_tab()
        self._create_tokens_tab()
        self._create_output_tab()
        self.create_triploss_tab() # pestaña de triplos
    
    def _create_errors_tab(self):
        """Crea la pestaña de errores"""
        errors_frame = ttk.Frame(self.notebook)
        self.notebook.add(errors_frame, text="❌ Errores")
        
        # Configurar grid
        errors_frame.rowconfigure(1, weight=1)
        errors_frame.columnconfigure(0, weight=1)
        
        # Etiqueta
        error_label = ttk.Label(errors_frame, text="Tabla de errores:",
                               style='Title.TLabel')
        error_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Tabla de errores
        columns = ('Token', 'Lexema', 'Renglón', 'Descripción')
        self.error_tree = ttk.Treeview(errors_frame, columns=columns,
                                      show='headings', style='Custom.Treeview')
        
        # Configurar columnas
        self.error_tree.heading('Token', text='Token')
        self.error_tree.heading('Lexema', text='Lexema')
        self.error_tree.heading('Renglón', text='Renglón')
        self.error_tree.heading('Descripción', text='Descripción')
        
        self.error_tree.column('Token', width=60, anchor='center')
        self.error_tree.column('Lexema', width=120, anchor='center')
        self.error_tree.column('Renglón', width=80, anchor='center')
        self.error_tree.column('Descripción', width=400, anchor='w')
        
        # Scrollbar
        error_scrollbar = ttk.Scrollbar(errors_frame, orient="vertical",
                                       command=self.error_tree.yview)
        self.error_tree.configure(yscrollcommand=error_scrollbar.set)
        
        # Grid
        self.error_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        error_scrollbar.grid(row=1, column=1, sticky="ns", pady=5)
    
    def _create_tokens_tab(self):
        """Crea la pestaña de tabla de símbolos"""
        tokens_frame = ttk.Frame(self.notebook)
        self.notebook.add(tokens_frame, text="🔤 Tabla de símbolos")
        
        # Configurar grid
        tokens_frame.rowconfigure(1, weight=1)
        tokens_frame.columnconfigure(0, weight=1)
        
        # Etiqueta
        token_label = ttk.Label(tokens_frame,
                               text="Tabla de símbolos (nombre, tipo):",
                               style='Title.TLabel')
        token_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Tabla de tokens
        columns = ('Lexema', 'Tipo de dato')
        self.token_tree = ttk.Treeview(tokens_frame, columns=columns,
                                      show='headings', style='Custom.Treeview')
        
        # Configurar columnas
        for col in columns:
            self.token_tree.heading(col, text=col)
        
        self.token_tree.column('Lexema', width=180, anchor='center')
        self.token_tree.column('Tipo de dato', width=120, anchor='center')
        
        # Scrollbar
        token_scrollbar = ttk.Scrollbar(tokens_frame, orient="vertical",
                                       command=self.token_tree.yview)
        self.token_tree.configure(yscrollcommand=token_scrollbar.set)
        
        # Grid
        self.token_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        token_scrollbar.grid(row=1, column=1, sticky="ns", pady=5)
    
    def _create_output_tab(self):
        """Crea la pestaña de salida"""
        output_frame = ttk.Frame(self.notebook)
        self.notebook.add(output_frame, text="▶️ Salida")
        
        # Configurar grid
        output_frame.rowconfigure(1, weight=1)
        output_frame.columnconfigure(0, weight=1)
        
        # Etiqueta
        output_label = ttk.Label(output_frame, text="Salida de ejecución:",
                                style='Title.TLabel')
        output_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Área de salida
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            background=self.colors['bg_editor'],
            foreground=self.colors['success'],
            state='disabled',
            relief='flat'
        )
        self.output_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
    
    def create_triploss_tab(self):
        """Crea la pestaña de triplos"""
        triplos_frame = ttk.Frame(self.notebook)
        self.notebook.add(triplos_frame, text="🔁 Triplos")
        
        # Configurar grid
        triplos_frame.rowconfigure(1, weight=1)
        triplos_frame.columnconfigure(0, weight=1)
        
        # Etiqueta
        triplos_label = ttk.Label(triplos_frame, text="Lista de triplos (índice, operador, arg1, arg2, resultado):",
                                 style='Title.TLabel')
        triplos_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Tabla de triplos
        columns = ('#', 'Operador', 'Arg1', 'Arg2', 'Resultado')
        self.triple_tree = ttk.Treeview(triplos_frame, columns=columns,
                                        show='headings', style='Custom.Treeview')
        
        for col, w, anchor in (('#', 60, 'center'),
                               ('Operador', 120, 'center'),
                               ('Arg1', 120, 'center'),
                               ('Arg2', 120, 'center'),
                               ('Resultado', 180, 'w')):
            self.triple_tree.heading(col, text=col)
            self.triple_tree.column(col, width=w, anchor=anchor)
        
        # Scrollbar
        triple_scrollbar = ttk.Scrollbar(triplos_frame, orient="vertical",
                                         command=self.triple_tree.yview)
        self.triple_tree.configure(yscrollcommand=triple_scrollbar.set)
        
        # Grid
        self.triple_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        triple_scrollbar.grid(row=1, column=1, sticky="ns", pady=5)

    def show_errors(self, errores: List[Error]):
        """Muestra errores en la tabla"""
        # Limpiar tabla
        for item in self.error_tree.get_children():
            self.error_tree.delete(item)
        
        # Agregar errores
        for error in errores:
            lexema = error.lexema if hasattr(error, 'lexema') and error.lexema is not None else ""
            descripcion = error.mensaje
            renglon = error.linea if hasattr(error, 'linea') and error.linea is not None else ""
            
            self.error_tree.insert('', 'end', values=(
                error.token,
                lexema,
                renglon,
                descripcion
            ))
    
    def show_symbols(self, tabla_simbolos: Dict[str, Dict[str, Any]]):
        """Muestra la tabla de símbolos"""
        from constants import CANONICAL_TO_SOURCE
        
        # Limpiar tabla
        for item in self.token_tree.get_children():
            self.token_tree.delete(item)
        
        # Mostrar símbolos
        for nombre, info in tabla_simbolos.items():
            tipo_dato = info.get('tipo', '')
            # Convertir tipo interno a fuente
            tipo_dato = CANONICAL_TO_SOURCE.get(tipo_dato, tipo_dato)
            self.token_tree.insert('', 'end', values=(nombre, tipo_dato))
    
    def show_output(self, salida: List[str], has_errors: bool):
        """Muestra la salida de ejecución"""
        self.output_text.config(state='normal')
        self.output_text.delete('1.0', 'end')
        
        if salida:
            for linea in salida:
                self.output_text.insert('end', linea + '\n')
        else:
            if not has_errors:
                self.output_text.insert('end', "No hay salida de ejecución.\n")
            else:
                self.output_text.insert('end', "Código con errores - no se ejecutó.\n")
        
        self.output_text.config(state='disabled')
    
    def clear_all(self):
        """Limpia todos los resultados"""
        # Limpiar errores
        for item in self.error_tree.get_children():
            self.error_tree.delete(item)
        
        # Limpiar tokens
        for item in self.token_tree.get_children():
            self.token_tree.delete(item)
        
        # Limpiar triplos (si existe)
        if self.triple_tree:
            for item in self.triple_tree.get_children():
                self.triple_tree.delete(item)
        
        # Limpiar salida
        self.output_text.config(state='normal')
        self.output_text.delete('1.0', 'end')
        self.output_text.config(state='disabled')

    def select_tab(self, index: int):
        """Selecciona una pestaña por índice"""
        self.notebook.select(index)
    
    def bind_error_double_click(self, callback):
        """Vincula evento de doble click en errores"""
        self.error_tree.bind('<Double-1>', callback)
    
    def get_selected_error_line(self) -> int:
        """Obtiene la línea del error seleccionado"""
        selection = self.error_tree.selection()
        if selection:
            item = self.error_tree.item(selection[0])
            try:
                return int(item['values'][2])
            except:
                pass
        return 0
    
    def pack(self, **kwargs):
        """Empaqueta el frame principal"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Coloca el frame en grid"""
        self.frame.grid(**kwargs)