# gui.py - Interfaz Gráfica del Compilador Minimalista
"""
Interfaz gráfica para el compilador/intérprete minimalista usando tkinter.
Permite al usuario escribir código, compilarlo y ver los resultados en tiempo real.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import os

# Importar la lógica del compilador
try:
    from rules import analizar_codigo, obtener_tabla_simbolos, obtener_salida_ejecucion
except ImportError:
    print("Error: No se pudo importar rules.py")
    sys.exit(1)


class CompiladorGUI:
    """Interfaz gráfica principal del compilador"""

    def __init__(self, root):
        self.root = root

        # Inicializar TODAS las variables primero
        self.errores_actuales = []
        self.tokens_actuales = []
        self.info_adicional = {}

        # Variables de interfaz (inicializar como None)
        self.text_editor = None
        self.line_numbers = None
        self.status_text = None
        self.info_text = None
        self.error_tree = None
        self.token_tree = None
        self.output_text = None
        self.notebook = None

        # Configurar la aplicación
        self.setup_window()
        self.setup_styles()
        self.create_widgets()
        self.setup_layout()

        # Cargar ejemplo después de un breve delay para asegurar inicialización completa
        self.root.after(200, self.cargar_ejemplo_seguro)

    def setup_window(self):
        """Configuración inicial de la ventana"""
        self.root.title("Compilador - Lenguaje mnm ")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)

        # Configurar icono si existe
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        # Hacer la ventana redimensionable
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

    def setup_styles(self):
        """Configuración de estilos y colores"""
        self.colors = {
            'bg_main': '#2b2b2b',
            'bg_secondary': '#3c3c3c',
            'fg_text': '#ffffff',
            'fg_secondary': '#cccccc',
            'accent': '#4a90e2',
            'error': '#ff6b6b',
            'success': '#51c951',
            'warning': '#ffa726'
        }

        # Configurar estilo para ttk
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except:
            pass

        # Estilos personalizados
        self.style.configure('Title.TLabel',
                             background=self.colors['bg_main'],
                             foreground=self.colors['fg_text'],
                             font=('Arial', 12, 'bold'))

        self.style.configure('Custom.Treeview',
                             background=self.colors['bg_secondary'],
                             foreground=self.colors['fg_text'],
                             fieldbackground=self.colors['bg_secondary'])

    def create_widgets(self):
        """Crear todos los widgets de la interfaz"""
        # Frame principal
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Configurar grid del frame principal
        self.main_frame.rowconfigure(1, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        # Crear secciones paso a paso
        self.create_header()
        self.create_content_area()
        self.create_status_bar()

    def create_header(self):
        """Crear la barra de herramientas superior"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        # Título
        title_label = ttk.Label(header_frame, text="Compilador Minimalista - Lenguaje mnm",
                                style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky="w")

        # Botones
        button_frame = ttk.Frame(header_frame)
        button_frame.grid(row=0, column=1, sticky="e")

        self.btn_compilar = ttk.Button(button_frame, text="🔧 Compilar",
                                       command=self.compilar_codigo)
        self.btn_compilar.grid(row=0, column=0, padx=2)

        self.btn_limpiar = ttk.Button(button_frame, text="🗑️ Limpiar",
                                      command=self.limpiar_todo)
        self.btn_limpiar.grid(row=0, column=1, padx=2)

        self.btn_ejemplo = ttk.Button(button_frame, text="📝 Ejemplo",
                                      command=self.cargar_ejemplo)
        self.btn_ejemplo.grid(row=0, column=2, padx=2)

        # Configurar columnas del header
        header_frame.columnconfigure(1, weight=1)

    def create_content_area(self):
        """Crear el área principal de contenido"""
        # Panel principal con división horizontal
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.grid(row=1, column=0, sticky="nsew")

        # Panel izquierdo - Editor de código
        self.create_code_panel()

        # Panel derecho - Resultados y tablas
        self.create_results_panel()

    def create_code_panel(self):
        """Crear el panel del editor de código"""
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame, weight=2)

        # Configurar grid
        left_frame.rowconfigure(1, weight=1)
        left_frame.columnconfigure(0, weight=1)

        # Etiqueta del editor
        code_label = ttk.Label(left_frame, text="📝 Editor de Código",
                               style='Title.TLabel')
        code_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        # Frame para el editor y números de línea
        editor_frame = ttk.Frame(left_frame)
        editor_frame.grid(row=1, column=0, sticky="nsew")
        editor_frame.rowconfigure(0, weight=1)
        editor_frame.columnconfigure(1, weight=1)

        # Área de números de línea
        self.line_numbers = tk.Text(editor_frame, width=4, padx=3, takefocus=0,
                                    border=0, state='disabled', wrap='none',
                                    background=self.colors['bg_secondary'],
                                    foreground=self.colors['fg_secondary'],
                                    font=('Consolas', 11))
        self.line_numbers.grid(row=0, column=0, sticky="ns")

        # Editor de código principal
        self.text_editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.NONE,
            font=('Consolas', 11),
            background=self.colors['bg_secondary'],
            foreground=self.colors['fg_text'],
            insertbackground=self.colors['fg_text'],
            selectbackground=self.colors['accent'],
            relief='flat',
            borderwidth=1
        )
        self.text_editor.grid(row=0, column=1, sticky="nsew")

        # Configurar tags para resaltado de errores
        self.text_editor.tag_configure('error_line', background=self.colors['error'],
                                      foreground='white')

        # Bind eventos - con verificación de existencia
        self.text_editor.bind('<KeyRelease>', self.on_text_change_safe)
        self.text_editor.bind('<Button-1>', self.on_text_change_safe)
        self.text_editor.bind('<ButtonRelease-1>', self.on_text_change_safe)
        # Mouse wheel (Windows). En otros sistemas puede necesitar '<Button-4/5>' u otras formas.
        self.text_editor.bind('<MouseWheel>', self.on_scroll_safe)
        # Actualizar cuando se presiona Enter (evita pérdida de número de línea al crear una nueva línea)
        self.text_editor.bind('<Return>', lambda e: (self.on_text_change_safe(e), 'break'))
        self.text_editor.bind('<Configure>', self.update_line_numbers_safe)

        # Sincronizar scroll: cada vez que el editor se desplaza llamará a _on_editor_yscroll
        self.text_editor.configure(yscrollcommand=lambda *args: self._on_editor_yscroll(*args))

    def create_results_panel(self):
        """Crear el panel de resultados"""
        right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(right_frame, weight=3)

        # Notebook para pestañas
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill='both', expand=True)

        # Crear todas las pestañas (sin "Símbolos")
        self.create_errors_tab()
        self.create_tokens_tab()
        self.create_output_tab()

    def create_errors_tab(self):
        """Crear la pestaña de errores"""
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
        self.error_tree = ttk.Treeview(errors_frame, columns=columns, show='headings',
                                       style='Custom.Treeview')

        # Configurar columnas
        self.error_tree.heading('Token', text='Token')
        self.error_tree.heading('Lexema', text='Lexema')
        self.error_tree.heading('Renglón', text='Renglón')
        self.error_tree.heading('Descripción', text='Descripción')

        self.error_tree.column('Token', width=60, anchor='center')
        self.error_tree.column('Lexema', width=120, anchor='center')
        self.error_tree.column('Renglón', width=80, anchor='center')
        self.error_tree.column('Descripción', width=400, anchor='w')

        # Scrollbar para la tabla de errores
        error_scrollbar = ttk.Scrollbar(errors_frame, orient="vertical", command=self.error_tree.yview)
        self.error_tree.configure(yscrollcommand=error_scrollbar.set)

        # Grid de la tabla
        self.error_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        error_scrollbar.grid(row=1, column=1, sticky="ns", pady=5)

        # Bind doble click
        self.error_tree.bind('<Double-1>', self.ir_a_linea_error)

    def create_tokens_tab(self):
        """Crear la pestaña de tokens (variables declaradas / tabla simplificada)"""
        tokens_frame = ttk.Frame(self.notebook)
        self.notebook.add(tokens_frame, text="🔤 Tabla de símbolos (simple)")

        # Configurar grid
        tokens_frame.rowconfigure(1, weight=1)
        tokens_frame.columnconfigure(0, weight=1)

        # Etiqueta
        token_label = ttk.Label(tokens_frame, text="Tabla de símbolos (nombre, tipo):",
                                style='Title.TLabel')
        token_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        # Tabla de tokens
        columns = ('Lexema', 'Tipo de dato')
        self.token_tree = ttk.Treeview(tokens_frame, columns=columns, show='headings',
                                       style='Custom.Treeview')

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

    def create_output_tab(self):
        """Crear la pestaña de salida de ejecución"""
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
            background=self.colors['bg_secondary'],
            foreground=self.colors['success'],
            state='disabled',
            relief='flat'
        )
        self.output_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    def create_status_bar(self):
        """Crear la barra de estado"""
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))

        # Variables de estado - INICIALIZAR AQUÍ
        self.status_text = tk.StringVar()
        self.status_text.set("Listo para compilar")

        self.info_text = tk.StringVar()
        self.info_text.set("Líneas: 0 | Errores: 0 | Tokens: 0")

        # Etiqueta de estado
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_text)
        self.status_label.grid(row=0, column=0, sticky="w")

        # Información adicional
        self.info_frame = ttk.Frame(self.status_frame)
        self.info_frame.grid(row=0, column=1, sticky="e")

        self.info_label = ttk.Label(self.info_frame, textvariable=self.info_text)
        self.info_label.grid(row=0, column=0)

        # Configurar columnas
        self.status_frame.columnconfigure(1, weight=1)

    def setup_layout(self):
        """Configurar el layout final"""
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

    # Métodos "safe" para evitar errores durante inicialización
    def on_text_change_safe(self, event=None):
        """Manejar cambios en el texto de forma segura"""
        try:
            if self.line_numbers and self.info_text:
                self.update_line_numbers()
                self.update_status()
        except:
            pass

    def on_scroll_safe(self, event):
        """Sincronizar scroll de forma segura (mouse wheel)"""
        try:
            if self.line_numbers:
                # Normalizamos delta para unidades de scroll
                delta = int(-1 * (event.delta / 120))
                self.line_numbers.yview_scroll(delta, "units")
                self.text_editor.yview_scroll(delta, "units")
        except:
            pass

    def update_line_numbers_safe(self, event=None):
        """Actualizar números de línea de forma segura"""
        try:
            if self.line_numbers:
                self.update_line_numbers()
        except:
            pass

    def update_line_numbers(self):
        """Actualizar los números de línea"""
        if not self.line_numbers or not self.text_editor:
            return

        try:
            self.line_numbers.config(state='normal')
            self.line_numbers.delete('1.0', 'end')

            # Obtener número de líneas (incluyendo la última)
            num_lines = int(self.text_editor.index('end-1c').split('.')[0])

            # Agregar números (incluir la última línea con +1)
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
        """
        Callback asociado al yscrollcommand del editor.
        args suele ser ('moveto', '0.x') o ('scroll', '1', 'units').
        Aquí sincronizamos la vista de line_numbers con la del editor.
        """
        try:
            # Mover la línea verticalmente según la vista actual del editor
            frac = self.text_editor.yview()[0]
            self.line_numbers.yview_moveto(frac)
        except:
            pass

    def update_status(self):
        """Actualizar información de la barra de estado"""
        if not self.text_editor or not self.info_text:
            return

        try:
            content = self.text_editor.get('1.0', 'end-1c')
            if content.strip():
                num_lines = int(self.text_editor.index('end-1c').split('.')[0])
            else:
                num_lines = 0

            self.info_text.set(f"Líneas: {num_lines} | Errores: {len(self.errores_actuales)} | "
                               f"Tokens: {len(self.tokens_actuales)}")
        except:
            pass

    def compilar_codigo(self):
        """Compilar el código actual"""
        try:
            if not self.text_editor:
                return

            # Obtener código del editor
            codigo = self.text_editor.get('1.0', 'end-1c')

            if not codigo.strip():
                messagebox.showwarning("Advertencia", "No hay código para compilar")
                return

            # Actualizar estado
            if self.status_text:
                self.status_text.set("Compilando...")
            self.root.update()

            # Limpiar errores visuales anteriores
            self.text_editor.tag_remove('error_line', '1.0', 'end')

            # Ejecutar análisis
            # Si quieres debug temporal, descomenta:
            # print("Código enviado a analizar:\n", codigo)
            self.errores_actuales, self.tokens_actuales, self.info_adicional = analizar_codigo(codigo)

            # Actualizar interfaz con resultados
            self.mostrar_errores()
            self.mostrar_tokens()
            self.mostrar_salida()

            # Actualizar estado y pestaña
            if self.errores_actuales:
                if self.status_text:
                    self.status_text.set(f"Compilación completada con {len(self.errores_actuales)} error(es)")
                if self.notebook:
                    self.notebook.select(0)  # Errores
            else:
                if self.status_text:
                    self.status_text.set("Compilación exitosa - Código analizado")
                if self.notebook:
                    self.notebook.select(2)  # Salida

            self.update_status()

        except Exception as e:
            messagebox.showerror("Error", f"Error durante la compilación: {str(e)}")
            if self.status_text:
                self.status_text.set("Error en compilación")

    def mostrar_errores(self):
        """Mostrar errores en la tabla y resaltar líneas (Token | Lexema | Renglón | Descripción)"""
        if not self.error_tree:
            return

        # Limpiar tabla anterior
        for item in self.error_tree.get_children():
            self.error_tree.delete(item)

        # Agregar errores
        for error in self.errores_actuales:
            # En la segunda columna ponemos el lexema implicado (si existe), sino vacío
            lexema = error.lexema if getattr(error, 'lexema', None) is not None else ""
            descripcion = error.mensaje
            renglon = error.linea if getattr(error, 'linea', None) is not None else ""

            # Insertar fila: Token, Lexema, Renglón, Descripción
            self.error_tree.insert('', 'end', values=(
                error.token,
                lexema,
                renglon,
                descripcion
            ))

            # Resaltar línea con error en el editor
            if self.text_editor:
                try:
                    line_start = f"{error.linea}.0"
                    line_end = f"{error.linea}.end"
                    self.text_editor.tag_add('error_line', line_start, line_end)
                except:
                    pass


    def mostrar_tokens(self):
        """Mostrar tabla simplificada (nombre, tipo)"""
        if not self.token_tree:
            return

        # Limpiar tabla anterior
        for item in self.token_tree.get_children():
            self.token_tree.delete(item)

        # Obtener tabla de símbolos desde info_adicional
        tabla_simbolos = self.info_adicional.get('tabla_simbolos', {})

        # Importar el diccionario de conversión
        from rules import CANONICAL_TO_SOURCE

        # Mostrar solo las entradas (nombre, tipo)
        for nombre, info in tabla_simbolos.items():
            tipo_dato = info.get('tipo', '')
            # Convertir tipo interno a fuente si aplica
            tipo_dato = CANONICAL_TO_SOURCE.get(tipo_dato, tipo_dato)
            self.token_tree.insert('', 'end', values=(nombre, tipo_dato))

    def mostrar_salida(self):
        """Mostrar salida de ejecución"""
        if not self.output_text:
            return

        # Limpiar salida anterior
        self.output_text.config(state='normal')
        self.output_text.delete('1.0', 'end')

        # Mostrar nueva salida
        salida = self.info_adicional.get('salida_ejecucion', [])

        if salida:
            for linea in salida:
                self.output_text.insert('end', linea + '\n')
        else:
            if not self.errores_actuales:
                self.output_text.insert('end', "No hay salida de ejecución.\n")
            else:
                self.output_text.insert('end', "Código con errores - no se ejecutó.\n")

        self.output_text.config(state='disabled')

    def ir_a_linea_error(self, event):
        """Ir a la línea de error al hacer doble clic"""
        if not self.error_tree or not self.text_editor:
            return

        selection = self.error_tree.selection()
        if selection:
            item = self.error_tree.item(selection[0])
            try:
                linea = int(item['values'][2])
                # Ir a la línea
                self.text_editor.mark_set('insert', f"{linea}.0")
                self.text_editor.see(f"{linea}.0")
                self.text_editor.focus()
            except:
                pass

    def limpiar_todo(self):
        """Limpiar todo el contenido"""
        # Limpiar editor
        if self.text_editor:
            self.text_editor.delete('1.0', 'end')

        # Limpiar tablas
        for tree in [self.error_tree, self.token_tree]:
            if tree:
                for item in tree.get_children():
                    tree.delete(item)

        # Limpiar salida
        if self.output_text:
            self.output_text.config(state='normal')
            self.output_text.delete('1.0', 'end')
            self.output_text.config(state='disabled')

        # Limpiar tags de error
        if self.text_editor:
            self.text_editor.tag_remove('error_line', '1.0', 'end')

        # Reiniciar variables
        self.errores_actuales = []
        self.tokens_actuales = []
        self.info_adicional = {}

        # Actualizar estado
        if self.status_text:
            self.status_text.set("Todo limpiado - Listo para nuevo código")
        self.update_status()

    def cargar_ejemplo_seguro(self):
        """Cargar ejemplo de forma segura después de inicialización"""
        try:
            self.cargar_ejemplo()
        except Exception as e:
            print(f"Error cargando ejemplo: {e}")

    def cargar_ejemplo(self):
        """Cargar código de ejemplo"""
        if not self.text_editor:
            return

        ejemplo = r"""\ent mnmX , mnmoi;
\dec mnmY = 2.5;
\ent mnmZ = mnmX;
\cad mnmSaludo = "Hola mundo";
print("mnmSaludo");
print(mnmX);
mnm_val1
for mnmoi in range (5)"""

        try:
            # Limpiar editor y agregar ejemplo
            self.text_editor.delete('1.0', 'end')
            self.text_editor.insert('1.0', ejemplo)

            # Actualizar números de línea y estado
            self.update_line_numbers()
            self.update_status()

            if self.status_text:
                self.status_text.set("Ejemplo cargado - Presiona 'Compilar' para probar")
        except Exception as e:
            print(f"Error en cargar_ejemplo: {e}")


# ================================
# FUNCIÓN PRINCIPAL
# ================================

def main():
    """Función principal para ejecutar la aplicación"""
    try:
        # Crear ventana principal
        root = tk.Tk()

        # Crear aplicación
        app = CompiladorGUI(root)

        # Ejecutar loop principal
        root.mainloop()

    except KeyboardInterrupt:
        print("\nAplicación cerrada por el usuario")
    except Exception as e:
        messagebox.showerror("Error Fatal", f"Error inesperado: {str(e)}")


if __name__ == "__main__":
    main()
