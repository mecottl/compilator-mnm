# compiler.py - Clase principal del compilador
from typing import List, Tuple, Dict, Any
from models import Token, Error, ErrorType
from lexer import Lexer
from semantic_analyzer import SemanticAnalyzer
from error_handler import ErrorHandler
from symbol_table import SymbolTable
from interpreter import Interpreter
from triplos.triplo_generator import TriploGenerator
from utils.exporter import export_triplos_to_txt, export_triplos_to_csv

class Compilador:
    """Compilador principal que coordina todos los componentes"""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.symbol_table = SymbolTable()
        self.lexer = Lexer()
        self.semantic_analyzer = SemanticAnalyzer(self.error_handler, self.symbol_table)
        self.interpreter = Interpreter(self.symbol_table, self.error_handler)
        self.triplo_generator = TriploGenerator(self.symbol_table, self.error_handler)
        # --- 1. AÑADIR EL CONTADOR DE COMPILACIÓN ---
        self.compilation_count = 1

    def analizar_codigo(self, codigo: str) -> Tuple[List[Error], List[Token], Dict[str, Any]]:
        """
        Analiza el código fuente completo
        """
        # Reiniciar componentes
        self.error_handler.reset()
        self.symbol_table.reset()
        self.lexer.reset()
        
        # Fase 1: Análisis léxico
        tokens, tokens_por_linea = self.tokenize(codigo)
        
        # Fase 2: Análisis semántico
        self.semantic_analyzer.analyze(tokens_por_linea)
        
        # Deduplicar errores
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
            
            if lista_de_triplos:
                txt_filename = f"triplos_{self.compilation_count}.txt"
                csv_filename = f"triplos_{self.compilation_count}.csv"
                
                export_triplos_to_txt(lista_de_triplos, txt_filename)
                export_triplos_to_csv(lista_de_triplos, csv_filename)

        except Exception as e:
            self.error_handler.add_error(ErrorType.SEMANTICO, 0, f"Error de generación de triplos: {e}", "triplo")
        
        self.compilation_count += 1
        
        errores = self.error_handler.deduplicate_errors()

        info_adicional = {
            "tabla_simbolos": self.get_tabla_final(),
            "salida_ejecucion": salida_ejecucion,
            "lista_triplos": lista_de_triplos
        }
        
        return errores, tokens, info_adicional

# ... (El resto del archivo no necesita cambios) ...