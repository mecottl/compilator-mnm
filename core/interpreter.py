# interpreter.py - Módulo de ejecución de código
from .symbol_table import SymbolTable
from .evaluator import Evaluator
from .error_handler import ErrorHandler
from .constants import VALID_DECL_FORMS, RE_IDENTIFICADOR, CANONICAL_FROM_DECL

class Interpreter:
    """Ejecuta el código estructurado (con bloques)"""
    
    def __init__(self, symbol_table: SymbolTable, error_handler: ErrorHandler):
        self.symbol_table = symbol_table
        self.error_handler = error_handler
        self.evaluator = Evaluator(self.symbol_table, self.error_handler)
        self.output = []
        self.lines_tokens = []
        self.line_cursor = 0

    def execute(self, tokens_por_linea: list[list[str]]) -> list[str]:
        """Punto de entrada para la ejecución"""
        self.output = []
        self.lines_tokens = list(enumerate(tokens_por_linea, start=1))
        self.line_cursor = 0
        
        self._execute_block(stop_at_line=len(self.lines_tokens) + 1)
        
        return self.output

    # --- ¡INICIO DE LA MODIFICACIÓN! ---
    def _execute_block(self, stop_at_line: int):
        """
        Ejecuta un bloque de código, línea por línea, hasta
        encontrar 'stop_at_line'.
        """
        while self.line_cursor < len(self.lines_tokens) and self.line_cursor + 1 < stop_at_line:
            linea, parts = self.lines_tokens[self.line_cursor]
            self.line_cursor += 1
            
            if not parts or parts == ["}"]:
                continue
            
            # 0. Declaración CON Asignación (ej: \ent mnmI = 0)
            if parts[0] in VALID_DECL_FORMS and "=" in parts:
                try:
                    # Encontrar el índice del nombre de la variable
                    var_name_idx = 1
                    if parts[var_name_idx] == ",": # Ignorar comas (sintaxis antigua)
                        var_name_idx += 1
                    
                    # Crear una lista de tokens solo con la asignación
                    # ej: de [\ent, mnmX, =, 100, -, 2] -> [mnmX, =, 100, -, 2]
                    parts_de_asignacion = parts[var_name_idx:]
                    self._execute_assignment(linea, parts_de_asignacion)
                except Exception:
                    pass # El analizador semántico ya reportó este error
                continue
            
            # Si es una declaración sin asignación (ej: \ent mnmI;),
            # la saltamos.

            # 1. Instrucción FOR
            if parts[0] == "for":
                self._execute_for(linea, parts)
                continue
                
            # 2. Instrucción de ASIGNACIÓN (simple)
            if "=" in parts and parts[0] not in VALID_DECL_FORMS:
                 self._execute_assignment(linea, parts)
                 continue

            # 3. Instrucción PRINT
            if parts[0] == "print":
                self._execute_print(linea, parts)
                continue
    # --- FIN DE LA MODIFICACIÓN! ---

    def _execute_for_init(self, linea: int, init_tokens: list[str]):
        """Ejecuta la sección de inicialización de un bucle 'for'."""
        if not init_tokens:
            return

        # Caso 1: Es una declaración (ej: \ent mnmI = 1)
        if init_tokens[0] in VALID_DECL_FORMS:
            try:
                tipo_str = init_tokens[0]
                tipo_canon = CANONICAL_FROM_DECL[tipo_str]
                var_name = init_tokens[1]
                
                if not RE_IDENTIFICADOR.match(var_name):
                    raise SyntaxError(f"Identificador inválido en declaración de 'for': {var_name}")
                
                if self.symbol_table.esta_declarada(var_name):
                    self.error_handler.add_error("SEMANTICO", linea, f"Duplicidad de variable en 'for'", var_name)
                    return

                self.symbol_table.declarar_variable(var_name, tipo_canon)
                
                if len(init_tokens) > 2 and init_tokens[2] == "=":
                    expr_tokens = init_tokens[3:]
                    if not expr_tokens:
                        raise SyntaxError("Valor faltante en asignación de 'for'")
                    
                    value = self.evaluator.evaluate(expr_tokens, linea)
                    self.symbol_table.actualizar_valor(var_name, value)
                
            except Exception as e:
                self.error_handler.add_error("SINTACTICO", linea, f"Error en inicialización de 'for': {e}", " ".join(init_tokens))
        
        # Caso 2: Es una asignación simple (ej: mnmI = 1)
        else:
            self._execute_assignment(linea, init_tokens)

    def _execute_assignment(self, linea: int, parts: list[str]):
        """Ejecuta una asignación, ej: mnmx = mnmx + 1"""
        try:
            eq_pos = parts.index("=")
            var_name = parts[eq_pos - 1]
            expr_tokens = parts[eq_pos + 1:]

            if expr_tokens and expr_tokens[-1] == ";":
                expr_tokens.pop()
            
            if not self.symbol_table.esta_declarada(var_name):
                self.error_handler.add_error("SEMANTICO", linea, f"Asignación a variable no declarada '{var_name}'", var_name)
                return
            
            value = self.evaluator.evaluate(expr_tokens, linea)
            
            if value is not None:
                self.symbol_table.actualizar_valor(var_name, value)
                
        except Exception as e:
            self.error_handler.add_error("SEMANTICO", linea, f"Error en asignación: {e}", " ".join(parts))
            
    def _execute_for(self, linea: int, parts: list[str]):
        """Ejecuta un bucle FOR estilo C: for(init; cond; incr): { ... }"""
        
        try:
            idx_semicolon1 = parts.index(";")
            idx_semicolon2 = parts.index(";", idx_semicolon1 + 1)
            idx_paren_close = parts.index(")")
            
            init_tokens = parts[2:idx_semicolon1]
            cond_tokens = parts[idx_semicolon1 + 1 : idx_semicolon2]
            incr_tokens = parts[idx_semicolon2 + 1 : idx_paren_close]
            
            if parts[1] != "(" or parts[idx_paren_close + 1] != ":" or parts[idx_paren_close + 2] != "{":
                 raise SyntaxError("Se esperaba '):{' después de la cabecera del 'for'")
            
        except Exception as e:
            self.error_handler.add_error("SINTACTICO", linea, f"Sintaxis de 'for' inválida: {e}", "for")
            return

        start_line_idx = self.line_cursor
        body_end_line_idx = self._find_matching_brace(start_line_idx)
        
        if body_end_line_idx == -1:
            self.error_handler.add_error("SINTACTICO", linea, "No se encontró '}' para el 'for'", "for")
            return
            
        self._execute_for_init(linea, init_tokens)

        loop_count = 0
        while True:
            if loop_count > 10000:
                 self.error_handler.add_error("SEMANTICO", linea, "Posible bucle infinito detectado", "for")
                 break
                 
            condition_result = self.evaluator.evaluate(cond_tokens, linea)
            if not condition_result:
                break

            cursor_before_body = self.line_cursor
            self.line_cursor = start_line_idx
            self._execute_block(stop_at_line=body_end_line_idx)
            self.line_cursor = cursor_before_body
            
            self._execute_assignment(linea, incr_tokens)
            
            loop_count += 1
            
        self.line_cursor = body_end_line_idx

    def _find_matching_brace(self, start_line_idx: int) -> int:
        """Encuentra la '}' que cierra el bloque."""
        nesting_level = 1
        cursor = start_line_idx
        
        while cursor < len(self.lines_tokens):
            _linea, parts = self.lines_tokens[cursor]
            
            if "{" in parts:
                nesting_level += 1
            
            if "}" in parts:
                nesting_level -= 1
                if nesting_level == 0:
                    return cursor + 1
                    
            cursor += 1
        
        return -1

    def _execute_print(self, linea: int, parts: list[str]):
        """Ejecuta una instrucción print. Sintaxis: print(expresion);"""
        
        try:
            clean_parts = list(parts)
            
            if clean_parts and clean_parts[-1] == ";":
                clean_parts.pop()
            
            if not (len(clean_parts) >= 3 and clean_parts[1] == "(" and clean_parts[-1] == ")"):
                self.error_handler.add_error(
                    "SINTACTICO", linea, 
                    "Sintaxis de 'print' inválida. Se esperaba 'print(expresion)'", 
                    "print"
                )
                return

            expr_tokens = clean_parts[2:-1]
            
            if not expr_tokens:
                self.output.append("")
                return

            value = self.evaluator.evaluate(expr_tokens, linea)
            
            if value is None:
                self.output.append("None")
            else:
                self.output.append(str(value))

        except Exception as e:
            self.error_handler.add_error("SEMANTICO", linea, f"Error en 'print': {e}", "print")