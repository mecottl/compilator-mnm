# compiler.py - Clase principal del compilador
from typing import List, Tuple, Dict, Any
from models import Token, Error, ErrorType # <-- IMPORTAR ErrorType
from lexer import Lexer
from semantic_analyzer import SemanticAnalyzer
from error_handler import ErrorHandler
from symbol_table import SymbolTable
from interpreter import Interpreter  # <-- 1. IMPORTARLO

class Compilador:
    """Compilador principal que coordina todos los componentes"""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.symbol_table = SymbolTable()
        self.lexer = Lexer()
        self.semantic_analyzer = SemanticAnalyzer(self.error_handler, self.symbol_table)
        # <-- 2. INICIALIZARLO (pasando el error_handler)
        self.interpreter = Interpreter(self.symbol_table, self.error_handler) 

    def analizar_codigo(self, codigo: str) -> Tuple[List[Error], List[Token], Dict[str, Any]]:
        # ... (el reset sigue igual) ...
        self.error_handler.reset()
        self.symbol_table.reset()
        self.lexer.reset()
        
        # Fase 1: Análisis léxico
        tokens, tokens_por_linea = self.lexer.tokenize(codigo)
        
        # Fase 2: Análisis semántico
        # ¡¡NECESITAMOS MODIFICAR EL SEMANTIC_ANALYZER!!
        # Por ahora, asumimos que el semantic_analyzer PUEDE MANEJAR
        # la sintaxis del 'for' y no la reporta como error.
        # Esta es la parte más débil ahora.
        self.semantic_analyzer.analyze(tokens_por_linea)
        
        # Deduplicar errores léxicos y semánticos
        errores = self.error_handler.deduplicate_errors()
        
        # --- 3. FASE DE EJECUCIÓN (¡NUEVO!) ---
        salida_ejecucion = []
        if not self.error_handler.has_errors(): # Solo si no hay errores de léxico/semántica
            try:
                salida_ejecucion = self.interpreter.execute(tokens_por_linea)
            except Exception as e:
                # Captura errores de *ejecución* (división por cero, etc.)
                self.error_handler.add_error(ErrorType.SEMANTICO, 0, f"Error de ejecución: {e}", "runtime")
        # --- FIN DE LA FASE DE EJECUCIÓN ---
        
        # Volvemos a deduplicar para incluir errores de ejecución
        errores = self.error_handler.deduplicate_errors()

        # Preparar información adicional
        info_adicional = {
            "tabla_simbolos": self.symbol_table.get_tabla_final(),
            "salida_ejecucion": salida_ejecucion  # <-- 4. USAR LA SALIDA REAL
        }
        
        return errores, tokens, info_adicional

# ... (El resto del archivo 'compiler.py' sigue igual) ...

# Instancia singleton del compilador
_compilador_singleton = Compilador()


def analizar_codigo(codigo: str) -> Tuple[List[Error], List[Token], Dict[str, Any]]:
    """Función de conveniencia para analizar código"""
    return _compilador_singleton.analizar_codigo(codigo)


def obtener_tabla_simbolos(info_adicional: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Extrae la tabla de símbolos de la información adicional"""
    return info_adicional.get("tabla_simbolos", {})


def obtener_salida_ejecucion(info_adicional: Dict[str, Any]) -> List[str]:
    """Extrae la salida de ejecución de la información adicional"""
    return info_adicional.get("salida_ejecucion", [])