# triplos/expression_translator.py
# Traduce tokens de expresión a triplos, respetando la jerarquía
# de operaciones (PEMDAS) y usando temporales de forma explícita.

from symbol_table import SymbolTable
from error_handler import ErrorHandler
from constants import RE_IDENTIFICADOR, RE_ENTERO, RE_DECIMAL, RE_CADENA

class ExpressionTranslator:
    """
    Toma una lista de tokens de expresión y la convierte en triplos
    respetando la jerarquía de operaciones y el uso de temporales
    del ejemplo de Excel.
    """
    
    def __init__(self, symbol_table: SymbolTable, error_handler: ErrorHandler):
        self.symbol_table = symbol_table
        self.error_handler = error_handler
        self.tokens = []
        self.pos = 0
        self.linea = 0
        self.triplos = []
        self.temp_count = 1 # Este contador será manejado por triplo_generator

    def _new_temp(self) -> str:
        """Genera un nuevo nombre de variable temporal (T1, T2, etc.)"""
        temp_name = f"T{self.temp_count}"
        self.temp_count += 1
        return temp_name

    def _add_triplo(self, op: str, arg1: str, arg2: str):
        """Añade un triplo a nuestra lista interna."""
        self.triplos.append((op, arg1, arg2))

    def translate(self, tokens: list[str], linea: int, start_temp_count=1) -> tuple[list, str]:
        """
        Punto de entrada. Traduce tokens a triplos.
        Devuelve (lista_de_triplos, nombre_del_temporal_final_o_literal)
        """
        self.tokens = [t for t in tokens if t.strip()]
        self.pos = 0
        self.linea = linea
        self.triplos = []
        # Usa el contador de temporales que le pasa el generador
        self.temp_count = start_temp_count 
        
        if not self.tokens:
            return [], None

        try:
            # Si la expresión es solo un token (ej: 0 o mnmI),
            # lo devolvemos directamente. El generador lo pondrá en un temporal.
            if len(self.tokens) == 1:
                return [], self.tokens[0]

            # Iniciar el descenso recursivo en el nivel más bajo (||)
            final_arg = self._parse_logical_or()
            
            # Devolvemos los triplos generados, el argumento final,
            # y el contador actualizado de temporales.
            return self.triplos, final_arg
        except Exception as e:
            self.error_handler.add_error("SEMANTICO", linea, f"Error de traducción: {e}", " ".join(self.tokens))
            return [], None

    def _current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _advance(self):
        self.pos += 1

    # --- INICIO DE LA LÓGICA DE JERARQUÍA ---

    # Nivel de jerarquía: ||
    def _parse_logical_or(self):
        left_arg = self._parse_logical_and()
        while self._current_token() == "||":
            op = self._current_token()
            self._advance()
            right_arg = self._parse_logical_and()
            
            temp = self._new_temp()
            self._add_triplo("=", temp, left_arg)
            self._add_triplo(op, temp, right_arg)
            left_arg = temp
        return left_arg

    # Nivel de jerarquía: &&
    def _parse_logical_and(self):
        left_arg = self._parse_comparison()
        while self._current_token() == "&&":
            op = self._current_token()
            self._advance()
            right_arg = self._parse_comparison()

            temp = self._new_temp()
            self._add_triplo("=", temp, left_arg)
            self._add_triplo(op, temp, right_arg)
            left_arg = temp
        return left_arg

    # Nivel de jerarquía: < > == <= >= !=
    def _parse_comparison(self):
        left_arg = self._parse_addition_subtraction()
        op_map = {"<", "<=", ">", ">=", "==", "!="}
        
        while self._current_token() in op_map:
            op = self._current_token()
            self._advance()
            right_arg = self._parse_addition_subtraction()
            
            temp = self._new_temp()
            self._add_triplo("=", temp, left_arg)
            self._add_triplo(op, temp, right_arg)
            left_arg = temp
        return left_arg

    # Nivel de jerarquía: + -
    def _parse_addition_subtraction(self):
        left_arg = self._parse_multiplication_division()
        
        while self._current_token() in ("+", "-"):
            op = self._current_token()
            self._advance()
            right_arg = self._parse_multiplication_division()
            
            temp = self._new_temp()
            self._add_triplo("=", temp, left_arg)
            self._add_triplo(op, temp, right_arg)
            left_arg = temp
            
        return left_arg

    # Nivel de jerarquía: * /
    def _parse_multiplication_division(self):
        left_arg = self._parse_primary()
        
        while self._current_token() in ("*", "/"):
            op = self._current_token()
            self._advance()
            right_arg = self._parse_primary()
            
            temp = self._new_temp()
            self._add_triplo("=", temp, left_arg)
            self._add_triplo(op, temp, right_arg)
            left_arg = temp
            
        return left_arg

    # Nivel de jerarquía: () , literales, variables
    def _parse_primary(self) -> str:
        """
        Devuelve el "nombre" del argumento: un literal, una variable,
        o el temporal de una sub-expresión entre paréntesis.
        """
        token = self._current_token()
        self._advance()
        
        if RE_ENTERO.match(token) or RE_DECIMAL.match(token) or \
           RE_CADENA.match(token) or RE_IDENTIFICADOR.match(token):
            return token
            
        if token == "(":
            # Vuelve a la jerarquía más baja para la sub-expresión
            expr_arg = self._parse_logical_or()
            if self._current_token() != ")":
                raise SyntaxError(f"Falta ')' en expresión en línea {self.linea}")
            self._advance()
            return expr_arg
            
        raise SyntaxError(f"Token inesperado '{token}' en expresión en línea {self.linea}")