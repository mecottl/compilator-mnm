# interpreter.py - Módulo de ejecución de código
from symbol_table import SymbolTable
from evaluator import Evaluator
from error_handler import ErrorHandler
from constants import VALID_DECL_FORMS

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
        # Aplanamos los tokens por línea a una lista de (num_linea, tokens)
        self.lines_tokens = list(enumerate(tokens_por_linea, start=1))
        self.line_cursor = 0
        
        # Ejecutamos el "ámbito global"
        self._execute_block(stop_at_line=len(self.lines_tokens) + 1)
        
        return self.output

    def _execute_block(self, stop_at_line: int):
        """
        Ejecuta un bloque de código, línea por línea, hasta
        encontrar 'stop_at_line' (usado para delimitar el cuerpo de un 'for').
        """
        while self.line_cursor < len(self.lines_tokens) and self.line_cursor + 1 < stop_at_line:
            linea, parts = self.lines_tokens[self.line_cursor]
            self.line_cursor += 1 # Avanzamos ANTES de procesar
            
            if not parts:
                continue
            
            # --- Lógica de Instrucciones ---
            
            # 1. Instrucción FOR
            if parts[0] == "for":
                self._execute_for(linea, parts)
                continue
                
            # 2. Instrucción de ASIGNACIÓN (simple)
            # (El analizador semántico ya manejó las declaraciones)
            if "=" in parts and parts[0] not in VALID_DECL_FORMS: # (Necesitarías importar VALID_DECL_FORMS)
                 # Asumimos que es una asignación simple, ej: mnmx = mnmx + 1
                 self._execute_assignment(linea, parts)
                 continue

            # 3. Instrucción PRINT
            if parts[0] == "print":
                self._execute_print(linea, parts)
                continue
                
            # (Omitimos declaraciones, ya las procesó el semantic_analyzer)

    def _execute_assignment(self, linea: int, parts: list[str]):
        """Ejecuta una asignación, ej: mnmx = mnmx + 1"""
        try:
            eq_pos = parts.index("=")
            var_name = parts[eq_pos - 1]
            expr_tokens = parts[eq_pos + 1:]
            
            if not self.symbol_table.esta_declarada(var_name):
                self.error_handler.add_error("SEMANTICO", linea, f"Asignación a variable no declarada '{var_name}'", var_name)
                return
            
            # Usamos el evaluador
            value = self.evaluator.evaluate(expr_tokens, linea)
            
            if value is not None:
                # (Aquí iría la comprobación de tipos, pero el evaluador ya la hace)
                self.symbol_table.actualizar_valor(var_name, value)
                
        except Exception as e:
            self.error_handler.add_error("SEMANTICO", linea, f"Error en asignación: {e}", " ".join(parts))
            
    def _execute_for(self, linea: int, parts: list[str]):
        """Ejecuta un bucle FOR estilo C: for(init; cond; incr): { ... }"""
        
        # 1. Parsear la cabecera del FOR: for( ... ; ... ; ... ): {
        try:
            header_str = "".join(parts[1:]) # Une todo después de 'for'
            
            # Extraer las 3 partes
            if not header_str.startswith("(") or not header_str.endswith("):{"):
                raise SyntaxError("Formato de 'for' inválido. Se esperaba 'for(init; cond; incr):{'")
            
            content = header_str[1:-3] # Quita ( y ):{
            
            init_str, cond_str, incr_str = content.split(";")
            
            # Convertir las partes a listas de tokens (esto es una simplificación,
            # aquí deberíamos re-tokenizar)
            # Asumimos que el lexer ya separó bien los tokens en 'parts'
            # Esta parte es la más compleja. Necesitamos un parser de verdad.
            
            # --- SIMPLIFICACIÓN FORZADA ---
            # Necesitamos encontrar los tokens exactos para init, cond, incr
            # El 'parts' original: ['for', '(', 'mnmx', '=', '1', ';', 'mnmx', '<', '10', ';', 'mnmx', '=', 'mnmx', '+', '1', ')', ':', '{']
            
            if parts[1] != "(":
                 raise SyntaxError("Falta '(' después de 'for'")
            
            idx_semicolon1 = parts.index(";")
            idx_semicolon2 = parts.index(";", idx_semicolon1 + 1)
            idx_paren_close = parts.index(")")
            
            init_tokens = parts[2:idx_semicolon1]
            cond_tokens = parts[idx_semicolon1 + 1 : idx_semicolon2]
            incr_tokens = parts[idx_semicolon2 + 1 : idx_paren_close]
            
            if parts[idx_paren_close + 1] != ":" or parts[idx_paren_close + 2] != "{":
                 raise SyntaxError("Se esperaba '):{' después de la cabecera del 'for'")
            
        except Exception as e:
            self.error_handler.add_error("SINTACTICO", linea, f"Sintaxis de 'for' inválida: {e}", "for")
            return

        # 2. Encontrar el cuerpo del bucle (la '}' correspondiente)
        start_line_idx = self.line_cursor # La línea *después* del 'for'
        body_end_line_idx = self._find_matching_brace(start_line_idx)
        
        if body_end_line_idx == -1:
            self.error_handler.add_error("SINTACTICO", linea, "No se encontró '}' para el 'for'", "for")
            return
            
        # 3. Ejecutar el bucle
        
        # a. Ejecutar inicialización
        self._execute_assignment(linea, init_tokens) # Reutilizamos la lógica de asignación

        # b. Iniciar el bucle de condición
        loop_count = 0
        while True:
            if loop_count > 10000: # Límite de seguridad
                 self.error_handler.add_error("SEMANTICO", linea, "Posible bucle infinito detectado", "for")
                 break
                 
            # c. Evaluar condición
            condition_result = self.evaluator.evaluate(cond_tokens, linea)
            if not condition_result:
                break # Salir del bucle

            # d. Ejecutar el cuerpo del bucle
            # Guardamos el cursor actual, ejecutamos el bloque, y restauramos
            cursor_before_body = self.line_cursor
            self.line_cursor = start_line_idx # Apuntamos al inicio del cuerpo
            self._execute_block(stop_at_line=body_end_line_idx)
            self.line_cursor = cursor_before_body # Restauramos
            
            # e. Ejecutar incremento
            self._execute_assignment(linea, incr_tokens) # Reutilizamos
            
            loop_count += 1
            
        # 4. Mover el cursor principal para que salte el bloque del 'for'
        self.line_cursor = body_end_line_idx

    def _find_matching_brace(self, start_line_idx: int) -> int:
        """Encuentra la '}' que cierra el bloque. Devuelve el índice de la línea *después* del '}'."""
        nesting_level = 1
        cursor = start_line_idx
        
        while cursor < len(self.lines_tokens):
            _linea, parts = self.lines_tokens[cursor]
            
            if "{" in parts: # (Esto es simplificado, idealmente es ':{' al final)
                nesting_level += 1
            
            if "}" in parts:
                nesting_level -= 1
                if nesting_level == 0:
                    return cursor + 1 # Devolvemos la línea *siguiente*
                    
            cursor += 1
        
        return -1 # No se encontró
    
# ... (dentro de la clase Interpreter en interpreter.py) ...

    def _execute_print(self, linea: int, parts: list[str]):
        """Ejecuta una instrucción print. Sintaxis: print(expresion) o print(expresion);"""
        
        try:
            # --- ¡INICIO DE LA MODIFICACIÓN! ---
            
            # Copiamos la lista de tokens para no modificar la original
            clean_parts = list(parts)
            
            # 1. Ignorar el punto y coma opcional al final
            if clean_parts and clean_parts[-1] == ";":
                clean_parts.pop() # Elimina el ';'
            
            # 2. Validar la sintaxis con los tokens limpios
            if not (len(clean_parts) >= 3 and clean_parts[1] == "(" and clean_parts[-1] == ")"):
                self.error_handler.add_error(
                    "SINTACTICO", linea, 
                    "Sintaxis de 'print' inválida. Se esperaba 'print(expresion)'", 
                    "print"
                )
                return

            # 3. Extraer la expresión (lo que está entre los paréntesis)
            expr_tokens = clean_parts[2:-1]
            
            # --- FIN DE LA MODIFICACIÓN! ---

            if not expr_tokens:
                # Caso: print() - Imprime una línea vacía
                self.output.append("")
                return

            # Usamos el evaluador para calcular el resultado de la expresión
            value = self.evaluator.evaluate(expr_tokens, linea)
            
            if value is None:
                self.output.append("None")
            else:
                self.output.append(str(value))

        except Exception as e:
            self.error_handler.add_error("SEMANTICO", linea, f"Error en 'print': {e}", "print")