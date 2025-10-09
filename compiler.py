# compiler.py - Clase principal del compilador
from typing import List, Tuple, Dict, Any
from models import Token, Error
from lexer import Lexer
from semantic_analyzer import SemanticAnalyzer
from error_handler import ErrorHandler
from symbol_table import SymbolTable


class Compilador:
    """Compilador principal que coordina todos los componentes"""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.symbol_table = SymbolTable()
        self.lexer = Lexer()
        self.semantic_analyzer = SemanticAnalyzer(self.error_handler, self.symbol_table)
    
    def analizar_codigo(self, codigo: str) -> Tuple[List[Error], List[Token], Dict[str, Any]]:
        """
        Analiza el código fuente completo
        
        Args:
            codigo: Código fuente a analizar
            
        Returns:
            Tupla con:
            - Lista de errores encontrados
            - Lista de tokens
            - Diccionario con información adicional (tabla de símbolos, salida)
        """
        # Reiniciar componentes
        self.error_handler.reset()
        self.symbol_table.reset()
        self.lexer.reset()
        
        # Fase 1: Análisis léxico
        tokens, tokens_por_linea = self.lexer.tokenize(codigo)
        
        # Fase 2: Análisis semántico
        self.semantic_analyzer.analyze(tokens_por_linea)
        
        # Deduplicar errores
        errores = self.error_handler.deduplicate_errors()
        
        # Preparar información adicional
        info_adicional = {
            "tabla_simbolos": self.symbol_table.get_tabla_final(),
            "salida_ejecucion": []  # Por implementar
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