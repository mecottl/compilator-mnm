# triplos/expression_translator.py
# Traduce tokens de expresión a triplos, respetando la jerarquía
# de operaciones y usando temporales de forma explícita.

from core.symbol_table import SymbolTable
from core.error_handler import ErrorHandler
from core.constants import RE_IDENTIFICADOR, RE_ENTERO, RE_DECIMAL, RE_CADENA

class ExpressionTranslator:
    def __init__(self, symbol_table: SymbolTable, error_handler: ErrorHandler):
        self.symbol_table = symbol_table
        self.error_handler = error_handler
        self.tokens = []
        self.pos = 0
        self.linea = 0
        self.triplos = []
        self.temp_count = 1

    def _new_temp(self) -> str:
        temp_name = f"T{self.temp_count}"
        self.temp_count += 1
        return temp_name

    def _add_triplo(self, op: str, arg1: str, arg2: str):
        self.triplos.append((op, arg1, arg2))

    def translate(self, tokens: list[str], linea: int, start_temp_count=1) -> tuple[list, str]:
        self.tokens = [t for t in tokens if t.strip()]
        self.pos = 0
        self.linea = linea
        self.triplos = []
        self.temp_count = start_temp_count
        
        if not self.tokens:
            return [], None

        try:
            final_arg = self._parse_logical_or()
            if not final_arg.startswith("T"):
                temp = self._new_temp()
                self._add_triplo("=", temp, final_arg)
                final_arg = temp
            
            return self.triplos, final_arg
        except Exception as e:
            self.error_handler.add_error("SEMANTICO", linea, f"Error de traducción: {e}", " ".join(self.tokens))
            return [], None

    def _current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _advance(self):
        self.pos += 1
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

    # Nivel de jerarquía: * / %
    def _parse_multiplication_division(self):
        left_arg = self._parse_primary()
        
        # --- ¡INICIO DE LA MODIFICACIÓN! ---
        while self._current_token() in ("*", "/", "%"):
        # --- FIN DE LA MODIFICACIÓN! ---
            op = self._current_token()
            self._advance()
            right_arg = self._parse_primary()
            
            # El resto de la lógica es genérica y funciona para '%'
            temp = self._new_temp()
            self._add_triplo("=", temp, left_arg)
            self._add_triplo(op, temp, right_arg)
            left_arg = temp
            
        return left_arg

 
    def _parse_primary(self) -> str:

        token = self._current_token()
        self._advance()
        
        if RE_ENTERO.match(token) or RE_DECIMAL.match(token) or \
           RE_CADENA.match(token) or RE_IDENTIFICADOR.match(token):
            return token
            
        if token == "(":
            expr_arg = self._parse_logical_or()
            if self._current_token() != ")":
                raise SyntaxError(f"Falta ')' en expresión en línea {self.linea}")
            self._advance()
            return expr_arg
            
        raise SyntaxError(f"Token inesperado '{token}' en expresión en línea {self.linea}")