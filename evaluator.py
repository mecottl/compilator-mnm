# evaluator.py - Evaluador de Expresiones Aritméticas y Lógicas
import math
from symbol_table import SymbolTable
from constants import RE_IDENTIFICADOR, RE_ENTERO, RE_DECIMAL, RE_CADENA

class Evaluator:
    """Evalúa expresiones infijas (ej: 'mnmx + 1 * 2')"""
    
    def __init__(self, symbol_table: SymbolTable, error_handler):
        self.symbol_table = symbol_table
        self.error_handler = error_handler
        self.tokens = []
        self.pos = 0
        self.linea = 0

    def evaluate(self, tokens: list[str], linea: int) -> any:
        """Punto de entrada para evaluar una lista de tokens de expresión"""
        self.tokens = [t for t in tokens if t.strip()]
        self.pos = 0
        self.linea = linea
        
        if not self.tokens:
            return None
        
        try:
            return self._parse_logical_or()
        except Exception as e:
            self.error_handler.add_error("SEMANTICO", linea, f"Error de evaluación: {e}", " ".join(self.tokens))
            return None

    def _current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _advance(self):
        self.pos += 1

    def _parse_logical_or(self):
        left = self._parse_logical_and()
        while self._current_token() == "||":
            self._advance()
            right = self._parse_logical_and()
            left = bool(left) or bool(right)
        return left

    def _parse_logical_and(self):
        left = self._parse_comparison()
        while self._current_token() == "&&":
            self._advance()
            right = self._parse_comparison()
            left = bool(left) and bool(right)
        return left

    def _parse_comparison(self):
        left = self._parse_addition_subtraction()
        
        op_map = {"<": lambda l, r: l < r,
                  "<=": lambda l, r: l <= r,
                  ">": lambda l, r: l > r,
                  ">=": lambda l, r: l >= r,
                  "==": lambda l, r: l == r,
                  "!=": lambda l, r: l != r}
        
        while self._current_token() in op_map:
            op_token = self._current_token()
            op_func = op_map[op_token]
            self._advance()
            right = self._parse_addition_subtraction()
            left = op_func(self._get_numeric_value(left), self._get_numeric_value(right))
        return left

    def _parse_addition_subtraction(self):
        left = self._parse_multiplication_division()
        while self._current_token() in ("+", "-"):
            op = self._current_token()
            self._advance()
            right = self._parse_multiplication_division()
            if op == "+":
                if isinstance(left, str) or isinstance(right, str):
                    left = str(left) + str(right)
                else:
                    left = self._get_numeric_value(left) + self._get_numeric_value(right)
            else: # op == "-"
                left = self._get_numeric_value(left) - self._get_numeric_value(right)
        return left

    def _parse_multiplication_division(self):
        left = self._parse_primary()
        while self._current_token() in ("*", "/"):
            op = self._current_token()
            self._advance()
            right = self._parse_primary()
            if op == "*":
                left = self._get_numeric_value(left) * self._get_numeric_value(right)
            else: # op == "/"
                right_val = self._get_numeric_value(right)
                if right_val == 0:
                    raise ZeroDivisionError(f"División por cero en línea {self.linea}")
                # --- ¡AQUÍ ESTABA EL ERROR! ---
                left = self._get_numeric_value(left) / right_val
        return left

    def _parse_primary(self):
        token = self._current_token()
        self._advance()
        
        if RE_ENTERO.match(token):
            return int(token)
        
        if RE_DECIMAL.match(token):
            return float(token)
            
        if RE_CADENA.match(token):
            return token[1:-1]
            
        if RE_IDENTIFICADOR.match(token):
            if not self.symbol_table.esta_declarada(token):
                raise NameError(f"Variable '{token}' no definida en línea {self.linea}")
            val = self.symbol_table.obtener_valor(token)
            if val is None:
                 raise ValueError(f"Variable '{token}' usada sin inicializar en línea {self.linea}")
            return val
            
        if token == "(":
            expr = self._parse_logical_or()
            if self._current_token() != ")":
                raise SyntaxError(f"Falta ')' en expresión en línea {self.linea}")
            self._advance()
            return expr
            
        raise SyntaxError(f"Token inesperado '{token}' en expresión en línea {self.linea}")

    def _get_numeric_value(self, val):
        """Helper para asegurar que el valor es numérico para operaciones"""
        if isinstance(val, (int, float)):
            return val
        if val is None:
            return 0
        try:
            return float(val)
        except (ValueError, TypeError):
             raise TypeError(f"Operación aritmética con tipo no numérico '{val}' (tipo {type(val)})")