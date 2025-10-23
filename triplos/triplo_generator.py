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

    def _generate_block(self, stop_at_line: int):
        """Ejecuta un bloque de código, línea por línea."""
        while self.line_cursor < len(self.lines_tokens) and self.line_cursor + 1 < stop_at_line:
            linea, parts = self.lines_tokens[self.line_cursor]
            self.line_cursor += 1
            
            if not parts or parts == ["}"]:
                continue
            
            if parts[0] == "for":
                self._generate_for(linea, parts)
                continue
            
            # --- INICIO CORRECCIÓN 2: 'print' eliminado ---
            # if parts[0] == "print":
            #     self._generate_print(linea, parts)
            #     continue
            # --- FIN CORRECCIÓN 2 ---
                
            if "=" in parts and parts[0] not in VALID_DECL_FORMS:
                 self._generate_assignment(linea, parts)
                 continue
            
            if parts[0] in VALID_DECL_FORMS and "=" in parts:
                 try:
                    var_name_idx = 1
                    if parts[var_name_idx] == ",":
                        var_name_idx += 1
                    
                    parts_de_asignacion = parts[var_name_idx:]
                    self._generate_assignment(linea, parts_de_asignacion)
                 except Exception:
                     pass
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
            
            self.temp_count = self.translator.temp_count

        except Exception as e:
            self.error_handler.add_error("SEMANTICO", linea, f"Error en asignación de triplo: {e}", " ".join(parts))

    # --- INICIO CORRECCIÓN 2: 'print' eliminado ---
    # La función _generate_print() ha sido eliminada por completo.
    # --- FIN CORRECCIÓN 2 ---

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

        # 3. Generar triplos para la INICIALIZACIÓN (init)
        if init_tokens:
            if init_tokens[0] in VALID_DECL_FORMS:
                self._generate_assignment(linea, init_tokens[1:])
            else:
                self._generate_assignment(linea, init_tokens)

        # 4. Generar triplos para la CONDICIÓN (cond)
        self._add_triplo("LABEL", label_cond_start, None)
        
        cond_triplos, final_cond_arg = self.translator.translate(
            cond_tokens, linea, self.temp_count
        )
        self.triplos.extend(cond_triplos)
        self.temp_count = self.translator.temp_count
        
        self._add_triplo("True", final_cond_arg, label_body_start)
        self._add_triplo("False", final_cond_arg, label_loop_end)

        # 5. Generar triplos para el CUERPO (body)
        self._add_triplo("LABEL", label_body_start, None)
        
        start_line_idx = self.line_cursor
        end_brace_line_idx = self._find_matching_brace(start_line_idx)
        
        if end_brace_line_idx == -1:
             self.error_handler.add_error("SINTACTICO", linea, "No se encontró '}' para el 'for'", "for")
             return

        self._generate_block(stop_at_line=end_brace_line_idx)
        
        # 6. Generar triplos para el INCREMENTO (incr)
        self._add_triplo("LABEL", label_incr_start, None)
        if incr_tokens:
            self._generate_assignment(linea, incr_tokens)

        # 7. Generar Salto Incondicional
        self._add_triplo("JMP", label_cond_start, None)

        # 8. Marcar el final del bucle
        self._add_triplo("LABEL", label_loop_end, None)
        
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
        Pasa final. Reemplaza todas las etiquetas (L1, L2) por sus
        números de línea reales (índice + 1).
        """
        label_map = {}
        
        final_triplos_no_labels = []
        for triplo in self.triplos:
            if triplo[0] == "LABEL":
                label_map[triplo[1]] = len(final_triplos_no_labels) + 1
            else:
                final_triplos_no_labels.append(triplo)

        # --- INICIO CORRECCIÓN 3: Resolver JMP (arg1) y Saltos Cond (arg2) ---
        resolved_triplos = []
        for op, arg1, arg2 in final_triplos_no_labels:
            
            resolved_arg1 = arg1
            resolved_arg2 = arg2
            
            if op == "JMP":
                # JMP usa arg1 para la etiqueta
                resolved_arg1 = label_map.get(arg1, arg1)
            elif op in ("True", "False"):
                # Saltos condicionales usan arg2 para la etiqueta
                resolved_arg2 = label_map.get(arg2, arg2)
            
            resolved_triplos.append((op, resolved_arg1, resolved_arg2))
        # --- FIN CORRECCIÓN 3 ---
                
        return resolved_triplos