# compiler.py - Clase principal del compilador
from typing import List, Tuple, Dict, Any
from models import Token, Error, ErrorType
from lexer import Lexer
from semantic_analyzer import SemanticAnalyzer
from error_handler import ErrorHandler
from symbol_table import SymbolTable
from interpreter import Interpreter
# Hacemos la importación absoluta (funciona desde main.py)
from triplos.triplo_generator import TriploGenerator

class Compilador:
    """Compilador principal que coordina todos los componentes"""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.symbol_table = SymbolTable()
        self.lexer = Lexer()
        self.semantic_analyzer = SemanticAnalyzer(self.error_handler, self.symbol_table)
        self.interpreter = Interpreter(self.symbol_table, self.error_handler)
        self.triplo_generator = TriploGenerator(self.symbol_table, self.error_handler)

    def analizar_codigo(self, codigo: str) -> Tuple[List[Error], List[Token], Dict[str, Any]]:
        """
        Analiza el código fuente completo
        """
        # Reiniciar componentes
        self.error_handler.reset()
        self.symbol_table.reset()
        self.lexer.reset()
        
        # Fase 1: Análisis léxico
        tokens, tokens_por_linea = self.lexer.tokenize(codigo)
        
        # Fase 2: Análisis semántico
        self.semantic_analyzer.analyze(tokens_por_linea)
        
        # Deduplicar errores léxicos y semánticos
        errores = self.error_handler.deduplicate_errors()
        
        salida_ejecucion = []
        lista_de_triplos = []
        
        # --- INICIO DE LA MODIFICACIÓN ---

        # --- 3A. FASE DE EJECUCIÓN (Solo si NO hay errores) ---
        if not self.error_handler.has_errors(): 
            try:
                # Solo ejecutamos si no hay errores semánticos
                salida_ejecucion = self.interpreter.execute(tokens_por_linea)
            except Exception as e:
                # Captura por si algo falla en la ejecución
                self.error_handler.add_error(ErrorType.SEMANTICO, 0, f"Error de ejecución: {e}", "runtime")

        # --- 3B. FASE DE GENERACIÓN DE TRIPLOS (Se ejecuta SIEMPRE) ---
        # (Movido fuera del 'if not has_errors')
        try:
            # Reiniciamos el generador para una ejecución limpia
            self.triplo_generator = TriploGenerator(self.symbol_table, self.error_handler)
            lista_de_triplos = self.triplo_generator.generate(tokens_por_linea)
        except Exception as e:
            # Captura errores *durante* la generación de triplos
            self.error_handler.add_error(ErrorType.SEMANTICO, 0, f"Error de generación de triplos: {e}", "triplo")
        
        # --- FIN DE LA MODIFICACIÓN ---
        
        # Volvemos a deduplicar para incluir errores de ejecución/generación
        errores = self.error_handler.deduplicate_errors()

        # Preparar información adicional
        info_adicional = {
            "tabla_simbolos": self.symbol_table.get_tabla_final(),
            "salida_ejecucion": salida_ejecucion,
            "lista_triplos": lista_de_triplos
        }
        
        return errores, tokens, info_adicional


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