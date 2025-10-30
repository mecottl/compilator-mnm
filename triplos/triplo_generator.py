# triplos/triplo_generator.py
# Genera la lista completa de triplos para todo el programa.

from symbol_table import SymbolTable
from error_handler import ErrorHandler
from constants import VALID_DECL_FORMS, RE_IDENTIFICADOR, CANONICAL_FROM_DECL
from .expression_translator import ExpressionTranslator

class TriploGenerator:
    """
    Recorre el código tokenizado línea por línea y genera una
    lista de triplos (operador, arg1, arg2) para la ejecución.
    """
    
    def __init__(self, symbol_table: SymbolTable, error_handler: ErrorHandler):
        self.symbol_table = symbol_table
        self.error_handler = error_handler
        self.translator = ExpressionTranslator(self.symbol_table, self.error_handler)
        
        self.triplos = []
        self.lines_tokens = []
        self.line_cursor = 0
        self.temp_count = 1
        self.label_count = 1

    def _new_temp(self) -> str:
        temp_name = f"T{self.temp_count}"
        self.temp_count += 1
        return temp_name
        
    def _new_label(self) -> str:
        label_name = f"L{self.label_count}"
        self.label_count += 1
        return label_name

    def _add_triplo(self, op: str, arg1: str, arg2: str = None):
        self.triplos.append((op, arg1, arg2))

    def generate(self, tokens_por_linea: list[list[str]]) -> list:
        """Punto de entrada. Genera todos los triplos y resuelve saltos."""
        self.triplos = []
        self.lines_tokens = list(enumerate(tokens_por_linea, start=1))
        self.line_cursor = 0
        self.temp_count = 1
        self.label_count = 1
        
        self._generate_block(stop_at_line=len(self.lines_tokens) + 1)
        
        return self._resolve_labels()

    # --- INICIO DE TU CÓDIGO ESPECIAL (SIN CAMBIOS) ---
    def _generate_special_mnmoi_assignment(self, linea: int, parts: list[str]):
        """Genera la asignación mnmoi = mnmoi + mnmNat * mnmi; forzando T1 y T2."""
        
        expr_tokens = parts[2:-1] 
        var_name = parts[0]
        
        sub_expr_tokens = expr_tokens[2:]
        self.temp_count = 1 
        sub_triplos, final_sub_arg = self.translator.translate(
            sub_expr_tokens, linea, self.temp_count
        )
        self.triplos.extend(sub_triplos)
        
        temp_count_next = self.temp_count + 1
        next_temp_for_mnmoi = f"T{temp_count_next}" 
        self._add_triplo("=", next_temp_for_mnmoi, expr_tokens[0])
        
        op = expr_tokens[1]
        self._add_triplo(op, next_temp_for_mnmoi, final_sub_arg)
        
        self._add_triplo("=", var_name, next_temp_for_mnmoi)
        
        self.temp_count = 1

    def _generate_special_mnmecott_assignment(self, linea: int, parts: list[str]):
        """Genera la asignación mnmecott = mnmecott - mnmi / 2; forzando T1 y T2."""
        
        expr_tokens = parts[2:-1]
        var_name = parts[0]
        
        sub_expr_tokens = expr_tokens[2:]
        self.temp_count = 1 
        sub_triplos, final_sub_arg = self.translator.translate(
            sub_expr_tokens, linea, self.temp_count
        )
        self.triplos.extend(sub_triplos)
        
        temp_count_next = self.temp_count + 1
        next_temp_for_mnmecott = f"T{temp_count_next}" 
        self._add_triplo("=", next_temp_for_mnmecott, expr_tokens[0])
        
        op = expr_tokens[1]
        self._add_triplo(op, next_temp_for_mnmecott, final_sub_arg)
        
        self._add_triplo("=", var_name, next_temp_for_mnmecott)
        
        self.temp_count = 1
    # --- FIN DE TU CÓDIGO ESPECIAL ---


    def _generate_block(self, stop_at_line: int):
        """Ejecuta un bloque de código, línea por línea."""
        while self.line_cursor < len(self.lines_tokens) and self.line_cursor + 1 < stop_at_line:
            linea, parts = self.lines_tokens[self.line_cursor]
            self.line_cursor += 1
            
            if not parts or parts == ["}"]:
                continue
            
            # --- MANEJO ESPECIAL DE ASIGNACIONES DENTRO DEL FOR ---
            if parts[:6] == ['mnmoi', '=', 'mnmoi', '+', 'mnmNat', '*']: 
                self._generate_special_mnmoi_assignment(linea, parts)
                continue
            
            if parts[:6] == ['mnmecott', '=', 'mnmecott', '-', 'mnmi', '/']: 
                self._generate_special_mnmecott_assignment(linea, parts)
                continue
            # --- FIN MANEJO ESPECIAL ---
            
            if parts[0] in VALID_DECL_FORMS:
                continue
            
            if parts[0] == "for":
                self._generate_for(linea, parts)
                continue
            
            if parts[0] == "print":
                self._generate_print(linea, parts)
                continue
                
            if "=" in parts:
                 self._generate_assignment(linea, parts)
                 continue

    def _generate_assignment(self, linea: int, parts: list[str]):
        """Genera triplos para una asignación (ej: mnmVar = expr)"""
        try:
            eq_pos = parts.index("=")
            var_name = parts[eq_pos - 1]
            expr_tokens = parts[eq_pos + 1:]
            
            if expr_tokens and expr_tokens[-1] == ";":
                expr_tokens.pop()
            
            expr_triplos, final_arg = self.translator.translate(
                expr_tokens, linea, self.temp_count
            )
            
            self.triplos.extend(expr_triplos)
            
            self._add_triplo("=", var_name, final_arg)
            
            self.temp_count = 1 

        except Exception as e:
            self.error_handler.add_error("SEMANTICO", linea, f"Error en asignación de triplo: {e}", " ".join(parts))

    def _generate_print(self, linea: int, parts: list[str]):
        """
        Genera triplos para la *expresión* dentro de un 'print',
        sin generar un triplo 'PRINT'.
        """
        try:
            if not (len(parts) >= 3 and parts[1] == "("):
                return

            expr_tokens = parts[2:]
            if expr_tokens and expr_tokens[-1] == ";":
                expr_tokens.pop()
            if expr_tokens and expr_tokens[-1] == ")":
                expr_tokens.pop()

            if not expr_tokens:
                return

            expr_triplos, final_arg = self.translator.translate(
                expr_tokens, linea, self.temp_count
            )
            self.triplos.extend(expr_triplos)
            self.temp_count = self.translator.temp_count
        except Exception as e:
            pass

    def _generate_for(self, linea: int, parts: list[str]):
        """Genera triplos para un 'for', incluyendo saltos."""
        try:
            idx_semicolon1 = parts.index(";")
            idx_semicolon2 = parts.index(";", idx_semicolon1 + 1)
            idx_paren_close = parts.index(")")
            
            init_tokens = parts[2:idx_semicolon1]
            cond_tokens = parts[idx_semicolon1 + 1 : idx_semicolon2]
            incr_tokens = parts[idx_semicolon2 + 1 : idx_paren_close]
            
        except Exception as e:
            self.error_handler.add_error("SINTACTICO", linea, f"Sintaxis de 'for' inválida para triplo: {e}", "for")
            return

        label_cond_start = self._new_label()
        label_body_start = self._new_label()
        label_incr_start = self._new_label()
        label_loop_end = self._new_label()

        if init_tokens:
            if init_tokens[0] in VALID_DECL_FORMS:
                self._generate_assignment(linea, init_tokens[1:])
            else:
                self._generate_assignment(linea, init_tokens)

        self._add_triplo("LABEL", label_cond_start, None)
        
        # --- ¡INICIO DE LA MODIFICACIÓN! ---
        
        # CASO 1: Lógica de OR (||)
        if "||" in cond_tokens:
            or_pos = cond_tokens.index("||")
            cond1_tokens = cond_tokens[:or_pos]
            cond2_tokens = cond_tokens[or_pos + 1:]
            
            label_cond2_start = self._new_label() 
            
            cond1_triplos, final_cond1_arg = self.translator.translate(
                cond1_tokens, linea, self.temp_count
            )
            self.triplos.extend(cond1_triplos)
            self.temp_count = self.translator.temp_count
            
            self._add_triplo("True", label_body_start, None)
            self._add_triplo("False", label_cond2_start, None) 

            self._add_triplo("LABEL", label_cond2_start, None)
            
            cond2_triplos, final_cond2_arg = self.translator.translate(
                cond2_tokens, linea, self.temp_count
            )
            self.triplos.extend(cond2_triplos)
            self.temp_count = self.translator.temp_count

            self._add_triplo("True", label_body_start, None)
            self._add_triplo("False", label_loop_end, None)
        
        # CASO 2: Lógica de AND (&&)
        elif "&&" in cond_tokens:
            and_pos = cond_tokens.index("&&")
            cond1_tokens = cond_tokens[:and_pos]
            cond2_tokens = cond_tokens[and_pos + 1:]
            
            label_cond2_start = self._new_label() 
            
            # --- CONDICIÓN 1 ---
            cond1_triplos, final_cond1_arg = self.translator.translate(
                cond1_tokens, linea, self.temp_count
            )
            self.triplos.extend(cond1_triplos)
            self.temp_count = self.translator.temp_count
            
            # Lógica de cortocircuito de AND:
            # Si es FALSO, salta al final del bucle
            self._add_triplo("False", label_loop_end, None)
            # Si es VERDADERO, salta a la segunda condición
            self._add_triplo("True", label_cond2_start, None)

            # --- ETIQUETA y CONDICIÓN 2 ---
            self._add_triplo("LABEL", label_cond2_start, None)
            
            cond2_triplos, final_cond2_arg = self.translator.translate(
                cond2_tokens, linea, self.temp_count
            )
            self.triplos.extend(cond2_triplos)
            self.temp_count = self.translator.temp_count

            # Si la segunda es Verdadera (ambas lo son), salta al cuerpo
            self._add_triplo("True", label_body_start, None)
            # Si la segunda es Falsa, salta al final del bucle
            self._add_triplo("False", label_loop_end, None)
            
        # CASO 3: Lógica simple
        else:
            cond_triplos, final_cond_arg = self.translator.translate(
                cond_tokens, linea, self.temp_count
            )
            self.triplos.extend(cond_triplos)
            self.temp_count = self.translator.temp_count
            
            self._add_triplo("True", label_body_start, None)
            self._add_triplo("False", label_loop_end, None)
        
        # --- ¡FIN DE LA MODIFICACIÓN! ---

        self._add_triplo("LABEL", label_body_start, None)
        
        start_line_idx = self.line_cursor
        end_brace_line_idx = self._find_matching_brace(start_line_idx)
        
        if end_brace_line_idx == -1:
             self.error_handler.add_error("SINTACTICO", linea, "No se encontró '}' para el 'for'", "for")
             return

        self._generate_block(stop_at_line=end_brace_line_idx)
        
        self._add_triplo("LABEL", label_incr_start, None)
        if incr_tokens:
            self._generate_assignment(linea, incr_tokens)

        self._add_triplo("JMP", label_cond_start, None)

        self._add_triplo("LABEL_END_LOOP", label_loop_end, None)
        
        self.line_cursor = end_brace_line_idx

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

    def _resolve_labels(self) -> list:
        """
        Pasa final. Reemplaza etiquetas (L1) por números de línea (19)
        y añade '...' solo si un bucle termina al final del código.
        """
        label_map = {}
        end_loop_labels = set()
        final_triplos_no_labels = []
        
        current_index = 1
        for op, arg1, arg2 in self.triplos:
            if op == "LABEL":
                label_map[arg1] = current_index
            elif op == "LABEL_END_LOOP":
                label_map[arg1] = current_index
                end_loop_labels.add(arg1)
            else:
                final_triplos_no_labels.append((op, arg1, arg2))
                current_index += 1

        resolved_triplos = []
        for op, arg1, arg2 in final_triplos_no_labels:
            
            resolved_arg1 = arg1
            resolved_arg2 = arg2
            
            if op == "JMP" or op in ("True", "False"):
                resolved_arg1 = label_map.get(arg1, arg1)
                resolved_arg2 = ""
            
            resolved_triplos.append((op, resolved_arg1, resolved_arg2))
        
        end_of_code_line = len(resolved_triplos) + 1
        
        add_ellipsis = False
        for label_name in end_loop_labels:
            if label_map.get(label_name) == end_of_code_line:
                add_ellipsis = True
                break
                
        if add_ellipsis:
            resolved_triplos.append(("...", "", ""))
                
        return resolved_triplos