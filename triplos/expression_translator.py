# triplos/expression_translator.py
# Traduce tokens de expresión a triplos, usando un modelo
# "acumulador" de un solo temporal (sin jerarquía de operaciones).

from symbol_table import SymbolTable
from error_handler import ErrorHandler
from constants import RE_IDENTIFICADOR, RE_ENTERO, RE_DECIMAL, RE_CADENA

class ExpressionTranslator:
    """
    Toma una lista de tokens de expresión y la convierte en triplos
    usando un único temporal acumulador, siguiendo el formato
    de la hoja de Excel (evaluación izquierda a derecha).
    """
    
    def __init__(self, symbol_table: SymbolTable, error_handler: ErrorHandler):
        self.symbol_table = symbol_table
        self.error_handler = error_handler
        self.triplos = []
        self.temp_count = 1
        self.linea = 0

    def _new_temp(self) -> str:
        """Obtiene el nombre del temporal actual"""
        # En este modelo, reusamos el mismo temporal
        temp_name = f"T{self.temp_count}"
        return temp_name
    
    def _reset_temp_counter(self, start_count):
        """Reinicia el contador de temporales."""
        self.temp_count = start_count

    def _add_triplo(self, op: str, arg1: str, arg2: str):
        """Añade un triplo a nuestra lista interna."""
        self.triplos.append((op, arg1, arg2))

    def translate(self, tokens: list[str], linea: int, start_temp_count=1) -> tuple[list, str]:
        """
        Punto de entrada. Traduce tokens a triplos usando un solo
        temporal acumulador (estilo L-R, sin jerarquía).
        """
        self.triplos = []
        self._reset_temp_counter(start_temp_count)
        self.linea = linea
        
        if not tokens:
            return [], None

        try:
            # 1. Manejar paréntesis (evaluación recursiva)
            if tokens[0] == "(":
                # Lógica simplificada si toda la expresión está entre paréntesis
                return self.translate(tokens[1:-1], linea, self.temp_count)

            # 2. Crear el temporal principal y cargar el primer operando.
            current_temp = self._new_temp()
            
            # (ej: =, T1, mnmNat)
            self._add_triplo("=", current_temp, tokens[0])
            
            # 3. Iterar por el resto de la expresión (operador, operando)
            pos = 1
            while pos < len(tokens):
                op = tokens[pos]
                arg2 = tokens[pos + 1]
                
                # Aplicar la operación al temporal actual
                self._add_triplo(op, current_temp, arg2)
                
                pos += 2 # Saltar el operador y el operando
                
            # El resultado final está en el temporal que hemos estado usando
            return self.triplos, current_temp

        except IndexError:
             self.error_handler.add_error("SINTACTICO", linea, "Expresión mal formada", " ".join(tokens))
             return [], None
        except Exception as e:
            self.error_handler.add_error("SEMANTICO", linea, f"Error de traducción: {e}", " ".join(tokens))
            return [], None