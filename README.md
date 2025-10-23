# mnmCompilador - Estructura Modular

## 📁 Estructura del Proyecto

```
mnmCompilador/
│
├── main.py                    # Punto de entrada de la aplicación
│
├── constants.py               # Constantes y expresiones regulares
├── models.py                  # Clases de datos (Token, Error, ErrorType)
├── error_handler.py           # Gestión de errores
├── symbol_table.py            # Tabla de símbolos
├── lexer.py                   # Análisis léxico (tokenización)
├── semantic_analyzer.py       # Análisis semántico
├── compiler.py                # Compilador principal (coordinador)
│
└── gui/
    ├── __init__.py           # Inicialización del módulo GUI
    ├── styles.py             # Estilos y colores
    ├── editor_panel.py       # Panel del editor de código
    ├── results_panel.py      # Panel de resultados
    └── main_window.py        # Ventana principal
```

## 🎯 Descripción de Módulos

### Módulos del Compilador

#### **constants.py**
Define todas las constantes del compilador:
- Expresiones regulares (identificadores, números, cadenas)
- Formas de declaración válidas e inválidas
- Palabras clave
- Conversión de tipos

#### **models.py**
Define las clases de datos:
- `ErrorType`: Enum con tipos de errores (SEMÁNTICO, LÉXICO, SINTÁCTICO)
- `Token`: Representa un token del código
- `Error`: Representa un error encontrado

#### **error_handler.py**
Gestiona el registro y deduplicación de errores:
- `ErrorHandler`: Clase para manejar errores
- Métodos: `add_error()`, `deduplicate_errors()`, `has_errors()`

#### **symbol_table.py**
Maneja la tabla de símbolos:
- `SymbolTable`: Almacena variables y sus tipos
- Métodos: `declarar_variable()`, `esta_declarada()`, `obtener_tipo()`, etc.

#### **lexer.py**
Análisis léxico (tokenización):
- `Lexer`: Convierte código fuente en tokens
- Clasifica tokens (identificadores, constantes, símbolos, etc.)
- Deduplica tokens

#### **semantic_analyzer.py**
Análisis semántico:
- `SemanticAnalyzer`: Verifica tipos y declaraciones
- Analiza declaraciones, asignaciones
- Verifica compatibilidad de tipos
- Detecta variables no declaradas

#### **compiler.py**
Coordinador principal:
- `Compilador`: Orquesta todos los componentes
- Método principal: `analizar_codigo()`
- Retorna errores, tokens e información adicional

### Módulos de la GUI

#### **gui/styles.py**
Define estilos visuales:
- `AppStyles`: Paleta de colores y configuración de estilos ttk

#### **gui/editor_panel.py**
Panel del editor de código:
- `EditorPanel`: Editor con números de línea
- Resaltado de errores
- Sincronización de scroll

#### **gui/results_panel.py**
Panel de resultados con pestañas:
- `ResultsPanel`: Muestra errores, tabla de símbolos y salida
- Tres pestañas: Errores, Tabla de símbolos, Salida

#### **gui/main_window.py**
Ventana principal:
- `MainWindow`: Coordina toda la interfaz
- Botones de compilar, limpiar, ejemplo
- Barra de estado

## 🚀 Cómo Ejecutar

```bash
python main.py
```