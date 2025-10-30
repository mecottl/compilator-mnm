# compiler.py - Clase principal del compilador
import os # <-- 1. IMPORTAR OS
from typing import List, Tuple, Dict, Any
from models import Token, Error, ErrorType
from lexer import Lexer
from semantic_analyzer import SemanticAnalyzer
from error_handler import ErrorHandler
from symbol_table import SymbolTable
from interpreter import Interpreter
from triplos.triplo_generator import TriploGenerator
from utils.exporter import export_triplos_to_txt, export_triplos_to_csv

# --- 2. DEFINIR EL NOMBRE DE LA CARPETA DE SALIDA ---
TRIPLOS_OUTPUT_FOLDER = "triplos.txt"

class Compilador:
    """Compilador principal que coordina todos los componentes"""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.symbol_table = SymbolTable()
        self.lexer = Lexer()
        self.semantic_analyzer = SemanticAnalyzer(self.error_handler, self.symbol_table)
        self.interpreter = Interpreter(self.symbol_table, self.error_handler)
        self.triplo_generator = TriploGenerator(self.symbol_table, self.error_handler)
        self.compilation_count = 1
        
        # --- 3. CREAR LA CARPETA DE SALIDA SI NO EXISTE ---
        try:
            os.makedirs(TRIPLOS_OUTPUT_FOLDER, exist_ok=True)
        except Exception as e:
            print(f"Advertencia: No se pudo crear la carpeta de salida '{TRIPLOS_OUTPUT_FOLDER}': {e}")

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
        
        # Deduplicar errores
        errores = self.error_handler.deduplicate_errors()
        
        salida_ejecucion = []
        lista_de_triplos = []
        
        # Fase de Ejecución (Solo si NO hay errores)
        if not self.error_handler.has_errors(): 
            try:
                salida_ejecucion = self.interpreter.execute(tokens_por_linea)
            except Exception as e:
                self.error_handler.add_error(ErrorType.SEMANTICO, 0, f"Error de ejecución: {e}", "runtime")

        # Fase de Generación de Triplos (Se ejecuta SIEMPRE)
        try:
            self.triplo_generator = TriploGenerator(self.symbol_table, self.error_handler)
            lista_de_triplos = self.triplo_generator.generate(tokens_por_linea)
            
            # --- 4. MODIFICAR LA RUTA DE EXPORTACIÓN ---
            if lista_de_triplos:
                # Crear nombres de archivo base
                txt_filename_base = f"triplos_{self.compilation_count}.txt"
                csv_filename_base = f"triplos_{self.compilation_count}.csv"
                
                # Unir la carpeta con el nombre de archivo
                txt_filepath = os.path.join(TRIPLOS_OUTPUT_FOLDER, txt_filename_base)
                csv_filepath = os.path.join(TRIPLOS_OUTPUT_FOLDER, csv_filename_base)
                
                export_triplos_to_txt(lista_de_triplos, txt_filepath)
                export_triplos_to_csv(lista_de_triplos, csv_filepath)

        except Exception as e:
            self.error_handler.add_error(ErrorType.SEMANTICO, 0, f"Error de generación de triplos: {e}", "triplo")
        
        self.compilation_count += 1
        
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