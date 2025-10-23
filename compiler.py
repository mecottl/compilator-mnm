
from typing import List, Tuple, Dict, Any
from models import Token, Error, ErrorType
from lexer import Lexer
from semantic_analyzer import SemanticAnalyzer
from error_handler import ErrorHandler
from symbol_table import SymbolTable
from interpreter import Interpreter
from triplos.triplo_generator import TriploGenerator

class Compilador:
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.symbol_table = SymbolTable()
        self.lexer = Lexer()
        self.semantic_analyzer = SemanticAnalyzer(self.error_handler, self.symbol_table)
        self.interpreter = Interpreter(self.symbol_table, self.error_handler)
        self.triplo_generator = TriploGenerator(self.symbol_table, self.error_handler) 

    def analizar_codigo(self, codigo: str) -> Tuple[List[Error], List[Token], Dict[str, Any]]:
        self.error_handler.reset()
        self.symbol_table.reset()
        self.lexer.reset()
        
        tokens, tokens_por_linea = self.lexer.tokenize(codigo)
        self.semantic_analyzer.analyze(tokens_por_linea)        
        errores = self.error_handler.deduplicate_errors()
        
        salida_ejecucion = []
        lista_de_triplos = []
        
        if not self.error_handler.has_errors():
            
            try:
                salida_ejecucion = self.interpreter.execute(tokens_por_linea)
            except Exception as e:
                self.error_handler.add_error(ErrorType.SEMANTICO, 0, f"Error de ejecución: {e}", "runtime")
            try:
                self.triplo_generator = TriploGenerator(self.symbol_table, self.error_handler)
                lista_de_triplos = self.triplo_generator.generate(tokens_por_linea)
            except Exception as e:
                self.error_handler.add_error(ErrorType.SEMANTICO, 0, f"Error de generación de triplos: {e}", "triplo")
        
        errores = self.error_handler.deduplicate_errors()

        info_adicional = {
            "tabla_simbolos": self.symbol_table.get_tabla_final(),
            "salida_ejecucion": salida_ejecucion,
            "lista_triplos": lista_de_triplos  
        }
        
        return errores, tokens, info_adicional

_compilador_singleton = Compilador()


def analizar_codigo(codigo: str) -> Tuple[List[Error], List[Token], Dict[str, Any]]:
    return _compilador_singleton.analizar_codigo(codigo)


def obtener_tabla_simbolos(info_adicional: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return info_adicional.get("tabla_simbolos", {})


def obtener_salida_ejecucion(info_adicional: Dict[str, Any]) -> List[str]:
    return info_adicional.get("salida_ejecucion", [])