# compiler.py - Clase principal del compilador
import os
from typing import List, Tuple, Dict, Any
from .models import Token, Error, ErrorType
from .lexer import Lexer
from .semantic_analyzer import SemanticAnalyzer
from .error_handler import ErrorHandler
from .symbol_table import SymbolTable
from .interpreter import Interpreter

from ensamblador.assembler_generator import AssemblerGenerator
from optimizer.text_optimizer import TextOptimizer
from triplos.triplo_generator import TriploGenerator
from utils.exporter import export_triplos_to_txt, export_triplos_to_csv

TRIPLOS_OUTPUT_FOLDER = "triplos_output"

class Compilador:    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.symbol_table = SymbolTable()
        self.lexer = Lexer()
        self.semantic_analyzer = SemanticAnalyzer(self.error_handler, self.symbol_table)
        self.interpreter = Interpreter(self.symbol_table, self.error_handler)
        self.triplo_generator = TriploGenerator(self.symbol_table, self.error_handler)
        self.compilation_count = 1
        self.assembler_generator = AssemblerGenerator()
        
        try:
            os.makedirs(TRIPLOS_OUTPUT_FOLDER, exist_ok=True)
        except Exception as e:
            print(f"Advertencia: No se pudo crear la carpeta de salida '{TRIPLOS_OUTPUT_FOLDER}': {e}")

    def analizar_codigo(self, codigo: str) -> Tuple[List[Error], List[Token], Dict[str, Any]]:
        """
        Analiza el código fuente completo
        """
        self.error_handler.reset()
        self.symbol_table.reset()
        self.lexer.reset()
        
        # Nota: 'codigo' aquí ya es el código OPTIMIZADO que viene de la GUI
        tokens, tokens_por_linea = self.lexer.tokenize(codigo)
        
        self.semantic_analyzer.analyze(tokens_por_linea) # <--- AQUÍ SE LLENA LA TABLA
        errores = self.error_handler.deduplicate_errors()
        
        salida_ejecucion = []
        lista_de_triplos = []
        
        if not self.error_handler.has_errors(): 
            try:
                salida_ejecucion = self.interpreter.execute(tokens_por_linea)
            except Exception as e:
                self.error_handler.add_error(ErrorType.SEMANTICO, 0, f"Error de ejecución: {e}", "runtime")

        try:
            # Generamos los triplos (basados en el código optimizado)
            self.triplo_generator = TriploGenerator(self.symbol_table, self.error_handler)
            triplos_sin_resolver = self.triplo_generator.generate(tokens_por_linea)
            
            # Resolvemos etiquetas para obtener la lista final
            lista_de_triplos = self.triplo_generator.resolve_labels(triplos_sin_resolver)
            
            if lista_de_triplos:
                txt_filename_base = f"triplos_{self.compilation_count}.txt"
                csv_filename_base = f"triplos_{self.compilation_count}.csv"
                
                txt_filepath = os.path.join(TRIPLOS_OUTPUT_FOLDER, txt_filename_base)
                csv_filepath = os.path.join(TRIPLOS_OUTPUT_FOLDER, csv_filename_base)
                
                export_triplos_to_txt(lista_de_triplos, txt_filepath)
                export_triplos_to_csv(lista_de_triplos, csv_filepath)

        except Exception as e:
            self.error_handler.add_error(ErrorType.SEMANTICO, 0, f"Error de generación de triplos: {e}", "triplo")
        
        self.compilation_count += 1
        errores = self.error_handler.deduplicate_errors()
        
        codigo_ensamblador = ""
            
        if lista_de_triplos:
             # Generar ASM (ya no pasamos symbol_table)
             codigo_ensamblador = self.assembler_generator.generate(lista_de_triplos)
             
        info_adicional = {
            "tabla_simbolos": self.symbol_table.get_tabla_final(), # <--- ¡ESTA LÍNEA FALTABA O ESTABA MAL!
            "lista_triplos": lista_de_triplos,
            "salida_ejecucion": salida_ejecucion,
            "codigo_ensamblador": codigo_ensamblador 
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