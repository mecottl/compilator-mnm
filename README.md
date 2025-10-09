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

## 📦 Ventajas de la Nueva Estructura

### ✅ Separación de Responsabilidades
- Cada módulo tiene una función específica
- Fácil de entender y mantener

### ✅ Reutilización
- Los componentes pueden usarse independientemente
- Fácil crear tests unitarios

### ✅ Escalabilidad
- Agregar nuevas funcionalidades sin afectar otros módulos
- Ejemplo: agregar un parser sintáctico en `parser.py`

### ✅ Mantenibilidad
- Errores más fáciles de localizar
- Cambios en un módulo no afectan a otros

### ✅ Legibilidad
- Código más limpio y organizado
- Nombres descriptivos de archivos

## 🔧 Cómo Extender

### Agregar un nuevo tipo de análisis:
1. Crear archivo `nuevo_analisis.py`
2. Importar en `compiler.py`
3. Integrar en el método `analizar_codigo()`

### Agregar nueva pestaña en GUI:
1. Crear método `_create_nueva_tab()` en `results_panel.py`
2. Llamar desde `_create_widgets()`
3. Agregar método `show_nueva()` para mostrar datos

### Modificar estilos:
1. Editar `gui/styles.py`
2. Los cambios se aplican automáticamente

## 📝 Notas

- **Antes**: 2 archivos grandes (1400+ líneas)
- **Ahora**: 13 archivos modulares (~150-300 líneas c/u)
- **Mantenibilidad**: ⭐⭐⭐⭐⭐
- **Legibilidad**: ⭐⭐⭐⭐⭐