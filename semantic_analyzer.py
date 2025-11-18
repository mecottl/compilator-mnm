# semantic_analyzer.py - Análisis semántico (Corregido)

from typing import List, Tuple, Optional, Any
from models import ErrorType
from error_handler import ErrorHandler
from symbol_table import SymbolTable
from constants import (
    RE_IDENTIFICADOR, RE_ENTERO, RE_DECIMAL, RE_CADENA,
    VALID_DECL_FORMS, INVALID_DECL_FORMS, CANONICAL_FROM_DECL, CANONICAL_TO_SOURCE
)


class SemanticAnalyzer:
    """Analizador semántico - verifica tipos y declaraciones"""

    def __init__(self, error_handler: ErrorHandler, symbol_table: SymbolTable):
        self.error_handler = error_handler
        self.symbol_table = symbol_table

    def analyze(self, tokens_por_linea: List[List[str]]):
        """Analiza la semántica del código (Versión 2, soporta bloques)"""
        line_index = 0
        while line_index < len(tokens_por_linea):
            linea_actual = line_index + 1
            parts = tokens_por_linea[line_index]
            
            if not parts:
                line_index += 1
                continue
            
            self._process_basic_tokens(parts, linea_actual)
            
            # 1. Es un 'for'?
            if self._is_for_loop(parts):
                if not (len(parts) > 2 and parts[-1] == "{" and parts[-2] == ":"):
                    self.error_handler.add_error(
                        ErrorType.SINTACTICO, linea_actual,
                        "El 'for' debe terminar en '):{'", " ".join(parts)
                    )
                
                # --- Validar la cabecera del for ---
                self._analyze_for_header(parts, linea_actual)

                end_brace_line_idx = self._find_matching_brace(tokens_por_linea, line_index + 1)
                
                if end_brace_line_idx == -1:
                    self.error_handler.add_error(
                        ErrorType.SINTACTICO, linea_actual,
                        "No se encontró '}' para el 'for'", "for"
                    )
                    line_index += 1
                    continue
                
                line_index = end_brace_line_idx + 1
                continue

            # 2. Es una declaración inválida?
            if self._is_invalid_declaration(parts):
                line_index += 1
                continue

            # 3. Es una declaración válida?
            if self._is_declaration(parts):
                self._analyze_declaration(parts, linea_actual)
                line_index += 1
                continue
                
            # 4. Es una asignación?
            if self._is_assignment(parts):
                self._analyze_assignment(parts, linea_actual)
                line_index += 1
                continue
            
            # 5. Es un 'print'?
            if parts[0] == "print":
                self._analyze_print(parts, linea_actual)
                line_index += 1
                continue

            # 6. Es una línea '}' suelta?
            if parts == ["}"]:
                self.error_handler.add_error(
                    ErrorType.SINTACTICO, linea_actual,
                    "'}' inesperado fuera de un bloque", "}"
                )
                line_index += 1
                continue

            # 7. Si no es nada de lo anterior, checar variables
            # (Esto solo captura variables sueltas, no usadas en asignaciones)
            self._check_undeclared_variables(parts, linea_actual)
            
            line_index += 1

    def _find_matching_brace(self, tokens_por_linea: List[List[str]], start_line_idx: int) -> int:
        """Encuentra el '}' que cierra un bloque."""
        nesting_level = 1
        cursor = start_line_idx
        
        while cursor < len(tokens_por_linea):
            parts = tokens_por_linea[cursor]
            
            if "{" in parts:
                nesting_level += 1
            
            if "}" in parts:
                nesting_level -= 1
                if nesting_level == 0:
                    return cursor
                    
            cursor += 1
        
        return -1

    def _is_for_loop(self, parts: List[str]) -> bool:
        """Verifica si la línea es una cabecera de 'for'"""
        return parts and parts[0] == "for"

    def _process_basic_tokens(self, parts: List[str], linea: int):
        """Procesa tokens básicos y los registra en la tabla"""
        for p in parts:
            if RE_ENTERO.match(p):
                self.symbol_table.registrar(p, "\\ent", int(p))
            elif RE_DECIMAL.match(p):
                self.symbol_table.registrar(p, "\\dec", float(p))
            elif RE_CADENA.match(p):
                self.symbol_table.registrar(p, "\\cad", p[1:-1])

    def _is_declaration(self, parts: List[str]) -> bool:
        """Verifica si la línea es una declaración"""
        return len(parts) > 0 and parts[0] in VALID_DECL_FORMS

    def _is_invalid_declaration(self, parts: List[str]) -> bool:
        """Verifica si la línea usa declaración inválida"""
        if len(parts) > 0 and parts[0] in INVALID_DECL_FORMS:
            return True
        return False

    def _analyze_declaration(self, parts: List[str], linea: int):
        """Analiza una declaración de variable"""
        first = parts[0]
        tipo_decl = CANONICAL_FROM_DECL[first]
        
        self.symbol_table.registrar(first, "", None)
        
        pos = 1
        while pos < len(parts):
            tok = parts[pos]
            
            if tok == ";":
                break
            
            if RE_IDENTIFICADOR.match(tok):
                nombre = tok
                
                if self.symbol_table.esta_declarada(nombre):
                    self.error_handler.add_error(
                        ErrorType.SEMANTICO, linea,
                        "Duplicidad de declaración", 
                        lexema=nombre
                    )
                else:
                    self.symbol_table.declarar_variable(nombre, tipo_decl)
                
                j = pos + 1
                if j < len(parts) and parts[j] == "=":
                    rhs_tokens = self._extract_rhs(parts, j + 1)
                    
                    # --- Verificar indefinidas en el RHS antes de inferir ---
                    self._check_undeclared_variables(rhs_tokens, linea)
                    
                    rhs_tipo, rhs_valor = self._inferir_tipo_y_valor(rhs_tokens, linea)
                    
                    if rhs_tipo is not None:
                        self._check_type_compatibility(
                            tipo_decl, rhs_tipo, rhs_tokens, linea, nombre
                        )
                        
                    if rhs_valor is not None:
                        rhs_tipo_norm = CANONICAL_FROM_DECL.get(rhs_tipo, rhs_tipo)
                        
                        if tipo_decl == "/dec" and rhs_tipo_norm == "/ent":
                            self.symbol_table.actualizar_valor(nombre, float(rhs_valor))
                        elif tipo_decl == rhs_tipo_norm:
                            self.symbol_table.actualizar_valor(nombre, rhs_valor)
                    
                    pos = self._skip_to_delimiter(parts, j + 1)
                else:
                    pos += 1
                
                if pos < len(parts) and parts[pos] == ",":
                    pos += 1
                continue
            
            pos += 1

    def _is_assignment(self, parts: List[str]) -> bool:
        """Verifica si la línea es una asignación."""
        if "=" not in parts:
            return False
        
        if self._is_declaration(parts):
            return False
            
        if RE_IDENTIFICADOR.match(parts[0]):
             return True
             
        return False

    def _analyze_assignment(self, parts: List[str], linea: int):
        """Analiza una asignación"""
        try:
            pos_eq = parts.index("=")
        except ValueError:
            return
        
        if pos_eq <= 0:
            return
        
        lhs = parts[pos_eq - 1]
        rhs_tokens = self._extract_rhs(parts, pos_eq + 1)
        
        self.symbol_table.registrar("=", "", None)
        
        if not RE_IDENTIFICADOR.match(lhs):
            self.error_handler.add_error(
                ErrorType.SEMANTICO, linea,
                "LHS inválido en asignación", lexema=str(lhs)
            )
            return
        
        if not self.symbol_table.esta_declarada(lhs):
            self.error_handler.add_error(
                ErrorType.SEMANTICO, linea,
                "Variable indefinida", lexema=lhs
            )
            self.symbol_table.registrar(lhs, "", None)
            return
        
        if not rhs_tokens:
            self.error_handler.add_error(
                ErrorType.SEMANTICO, linea,
                "RHS inexistente en asignación", lexema=lhs
            )
            return
        
        # --- ¡INICIO DE LA CORRECCIÓN! ---
        # Verificar indefinidas en el RHS ANTES de inferir
        self._check_undeclared_variables(rhs_tokens, linea)
        # --- FIN DE LA CORRECCIÓN! ---

        rhs_tipo, rhs_valor = self._inferir_tipo_y_valor(rhs_tokens, linea)
        
        if rhs_tipo is not None:
            lhs_tipo = self.symbol_table.obtener_tipo(lhs)
            if lhs_tipo:
                self._check_type_compatibility(
                    lhs_tipo, rhs_tipo, rhs_tokens, linea, lhs
                )
                
                if rhs_valor is not None:
                    lhs_tipo_norm = CANONICAL_FROM_DECL.get(lhs_tipo, lhs_tipo)
                    rhs_tipo_norm = CANONICAL_FROM_DECL.get(rhs_tipo, rhs_tipo)
                    
                    if lhs_tipo_norm == "/dec" and rhs_tipo_norm == "/ent":
                        self.symbol_table.actualizar_valor(lhs, float(rhs_valor))
                    elif lhs_tipo_norm == rhs_tipo_norm:
                        self.symbol_table.actualizar_valor(lhs, rhs_valor)

    def _analyze_print(self, parts: List[str], linea: int):
        """Valida la sintaxis de la instrucción 'print'"""
        if len(parts) < 3 or parts[1] != "(":
            self.error_handler.add_error(
                ErrorType.SINTACTICO, linea,
                "Sintaxis de 'print' inválida. Se esperaba 'print(...)'",
                lexema="print"
            )
            return
        
        expr_tokens = parts[2:-1]
        if parts[-1] == ";":
            expr_tokens = parts[2:-2]
        
        self._check_undeclared_variables(expr_tokens, linea)
        
    def _analyze_for_header(self, parts: List[str], linea: int):
        """Valida las expresiones dentro de la cabecera del 'for'"""
        try:
            idx_semicolon1 = parts.index(";")
            idx_semicolon2 = parts.index(";", idx_semicolon1 + 1)
            idx_paren_close = parts.index(")")
            
            init_tokens = parts[2:idx_semicolon1]
            cond_tokens = parts[idx_semicolon1 + 1 : idx_semicolon2]
            incr_tokens = parts[idx_semicolon2 + 1 : idx_paren_close]
            
            self._check_undeclared_variables(init_tokens, linea)
            self._check_undeclared_variables(cond_tokens, linea)
            self._check_undeclared_variables(incr_tokens, linea)
            
        except Exception:
            # El error de sintaxis ya fue (o será) reportado
            pass

    def _check_undeclared_variables(self, parts: List[str], linea: int):
        """Verifica variables no declaradas en la línea"""
        for p in parts:
            if RE_IDENTIFICADOR.match(p) and not self.symbol_table.esta_declarada(p):
                self.error_handler.add_error(
                    ErrorType.SEMANTICO, linea,
                    "Variable indefinida", lexema=p
                )
                self.symbol_table.registrar(p, "", None)

    def _extract_rhs(self, parts: List[str], start_pos: int) -> List[str]:
        """Extrae tokens del lado derecho de una asignación"""
        rhs_tokens = []
        for tok in parts[start_pos:]:
            if tok in {",", ";"}:
                break
            if tok.strip():
                rhs_tokens.append(tok)
        return rhs_tokens

    def _skip_to_delimiter(self, parts: List[str], start_pos: int) -> int:
        """Salta tokens hasta encontrar delimitador"""
        k = start_pos
        while k < len(parts) and parts[k] not in {",", ";"}:
            k += 1
        return k

    def _inferir_tipo_y_valor(self, rhs_tokens: List[str], linea: int) -> Tuple[Optional[str], Optional[Any]]:
        """Infiere el tipo y valor de una expresión"""
        if not rhs_tokens:
            return None, None
        
        if len(rhs_tokens) == 1:
            t = rhs_tokens[0]
            if RE_ENTERO.match(t):
                return "\\ent", int(t)
            if RE_DECIMAL.match(t):
                return "\\dec", float(t)
            if RE_CADENA.match(t):
                return "\\cad", t[1:-1]
            if RE_IDENTIFICADOR.match(t):
                if not self.symbol_table.esta_declarada(t):
                    return None, None # Error ya reportado
                return self.symbol_table.obtener_tipo(t), None
            return None, None
        
        # --- Lógica de Inferencia de Expresión Compleja ---
        tipos_en_expresion = set()
        has_cad = False
        has_dec = False
        has_ent = False
        # --- ¡INICIO DE LA MODIFICACIÓN! ---
        has_mod = "%" in rhs_tokens
        # --- FIN DE LA MODIFICACIÓN! ---

        for t in rhs_tokens:
            tipo = None
            if RE_ENTERO.match(t):
                tipo = "\\ent"
                has_ent = True
            elif RE_DECIMAL.match(t):
                tipo = "\\dec"
                has_dec = True
            elif RE_CADENA.match(t):
                tipo = "\\cad"
                has_cad = True
            elif RE_IDENTIFICADOR.match(t):
                if self.symbol_table.esta_declarada(t):
                    tipo = self.symbol_table.obtener_tipo(t)
                    if tipo == "\\ent": has_ent = True
                    elif tipo == "\\dec": has_dec = True
                    elif tipo == "\\cad": has_cad = True
                else:
                    tipos_en_expresion.add(None)
            
            if tipo:
                tipos_en_expresion.add(CANONICAL_FROM_DECL.get(tipo, tipo))

        # --- ¡INICIO DE LA MODIFICACIÓN! ---
        # Regla: El módulo (%) solo funciona con enteros
        if has_mod and (has_cad or has_dec):
            self.error_handler.add_error(ErrorType.SEMANTICO, linea, "La operación de módulo '%' solo es válida entre enteros (\\ent)", "%")
            return None, None
        # --- FIN DE LA MODIFICACIÓN! ---

        if "/cad" in tipos_en_expresion and (len(tipos_en_expresion) > 1 or any(op in rhs_tokens for op in ['-','*','/','%'])):
             self.error_handler.add_error(ErrorType.SEMANTICO, linea, "Incompatibilidad de tipos en expresión aritmética/cadena", " ".join(rhs_tokens))
             return None, None
        elif "/cad" in tipos_en_expresion:
             return "\\cad", None
        
        if "/dec" in tipos_en_expresion:
            return "\\dec", None
        
        if "/ent" in tipos_en_expresion:
            return "\\ent", None
        
        return None, None

    def _check_type_compatibility(self, lhs_tipo: str, rhs_tipo: str,
                                    rhs_tokens: List[str], linea: int, lhs_name: str = ""):
        """Verifica compatibilidad de tipos"""
        
        lhs_tipo_norm = CANONICAL_FROM_DECL.get(lhs_tipo, lhs_tipo)
        rhs_tipo_norm = CANONICAL_FROM_DECL.get(rhs_tipo, rhs_tipo)
        
        compatible = (
            # CAMBIO AQUÍ: Permitimos asignar /dec a /ent (truncamiento implícito)
            (lhs_tipo_norm == "/ent" and rhs_tipo_norm in ("/ent", "/dec")) or
            (lhs_tipo_norm == "/dec" and rhs_tipo_norm in ("/ent", "/dec")) or
            (lhs_tipo_norm == "/cad" and rhs_tipo_norm == "/cad")
        )
        
        if not compatible:
            tipo_fuente = CANONICAL_TO_SOURCE.get(lhs_tipo, lhs_tipo)
            
            show_lex = None
            for t in rhs_tokens:
                if RE_CADENA.match(t) or RE_DECIMAL.match(t) or RE_ENTERO.match(t) or RE_IDENTIFICADOR.match(t):
                    show_lex = t
                    break
            
            if show_lex is None and rhs_tokens:
                show_lex = rhs_tokens[0]
            
            self.error_handler.add_error(
                ErrorType.SEMANTICO, linea,
                f"Incompatibilidad de tipo {tipo_fuente}",
                lexema=show_lex
            )