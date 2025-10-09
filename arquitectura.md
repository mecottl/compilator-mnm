# Arquitectura del mnmCompilador

## 🏗️ Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                          main.py                            │
│                    (Punto de entrada)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   gui/main_window.py                        │
│              (Coordinador de la interfaz)                   │
└──────┬─────────────────┬────────────────────┬───────────────┘
       │                 │                    │
       ▼                 ▼                    ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────────┐
│gui/styles.py│  │gui/editor    │  │gui/results       │
│             │  │_panel.py     │  │_panel.py         │
│ (Estilos)   │  │              │  │                  │
│             │  │ - Editor     │  │ - Errores        │
│ - Colores   │  │ - Líneas     │  │ - Símbolos       │
│ - Temas     │  │ - Resaltado  │  │ - Salida         │
└─────────────┘  └──────────────┘  └──────────────────┘
       │                 │                    │
       │                 └────────┬───────────┘
       │                          │
       │                          │ (al compilar)
       │                          ▼
       │         ┌────────────────────────────────┐
       │         │       compiler.py              │
       │         │   (Coordinador del análisis)   │
       │         └─────────┬──────────────────────┘
       │                   │
       │         ┌─────────┼─────────┬────────────┐
       │         │         │         │            │
       │         ▼         ▼         ▼            ▼
       │    ┌────────┐ ┌────────┐ ┌──────────┐ ┌───────────┐
       │    │ lexer  │ │semantic│ │  error   │ │  symbol   │
       │    │  .py   │ │_analyzer│ │ _handler │ │  _table   │
       │    │        │ │  .py   │ │   .py    │ │   .py     │
       │    └────────┘ └────────┘ └──────────┘ └───────────┘
       │         │         │         │            │
       │         └─────────┴─────────┴────────────┘
       │                   │
       │                   ▼
       │         ┌──────────────────┐
       │         │   models.py      │
       │         │                  │
       │         │ - Token          │
       │         │ - Error          │
       │         │ - ErrorType      │
       │         └──────────────────┘
       │                   │
       └───────────────────┴──────────────────────┐
                                                  │
                           ┌──────────────────────▼─┐
                           │   constants.py         │
                           │                        │
                           │ - Regex                │
                           │ - Keywords             │
                           │ - Tipos                │
                           └────────────────────────┘
```

## 🔄 Flujo de Ejecución

### 1. Inicio de la Aplicación
```
main.py → gui/main_window.py → Inicialización de componentes
```

### 2. Compilación de Código
```
Usuario presiona "Compilar"
         │
         ▼
MainWindow.compile_code()
         │
         ▼
compiler.analizar_codigo(codigo)
         │
         ├─→ lexer.tokenize()          # Fase 1: Tokenización
         │        │
         │        └─→ Retorna: tokens, tokens_por_linea
         │
         ├─→ semantic_analyzer.analyze() # Fase 2: Semántica
         │        │
         │        ├─→ Procesa declaraciones
         │        ├─→ Verifica asignaciones
         │        ├─→ Detecta variables no declaradas
         │        └─→ Verifica tipos
         │
         └─→ error_handler.deduplicate_errors()
                  │
                  └─→ Retorna: errores, tokens, info_adicional
```

### 3. Visualización de Resultados
```
MainWindow._show_results()
         │
         ├─→ results_panel.show_errors()
         ├─→ results_panel.show_symbols()
         ├─→ results_panel.show_output()
         └─→ editor_panel.highlight_error_line()
```

## 📊 Responsabilidades por Módulo

### Capa de Datos
- **models.py**: Define estructuras de datos
- **constants.py**: Configuración y constantes

### Capa de Análisis
- **lexer.py**: Tokenización del código fuente
- **semantic_analyzer.py**: Validación semántica
- **error_handler.py**: Gestión de errores
- **symbol_table.py**: Gestión de símbolos

### Capa de Coordinación
- **compiler.py**: Orquesta el proceso de compilación

### Capa de Presentación
- **gui/main_window.py**: Ventana principal
- **gui/editor_panel.py**: Editor de código
- **gui/results_panel.py**: Visualización de resultados
- **gui/styles.py**: Apariencia visual

### Punto de Entrada
- **main.py**: Inicialización de la aplicación