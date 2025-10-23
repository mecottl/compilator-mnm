# semantic_analyzer.py - Análisis semántico
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
        """
        Analiza la semántica del código
        
        Args:
            tokens_por_linea: Lista de tokens por cada línea
        """
        for idx, parts in enumerate(tokens_por_linea, start=1):
            if not parts:
                continue
            
            # Procesar tokens básicos
            self._process_basic_tokens(parts, idx)
            
            # Analizar declaraciones
            if self._is_declaration(parts):
                self._analyze_declaration(parts, idx)
                continue
            
            # Analizar declaraciones inválidas
            if self._is_invalid_declaration(parts):
                continue
            
            # Analizar asignaciones
            if "=" in parts:
                self._analyze_assignment(parts, idx)
            
            # Verificar variables no declaradas
            self._check_undeclared_variables(parts, idx)
    
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
                
                # Verificar duplicidad
                if self.symbol_table.esta_declarada(nombre):
                    self.error_handler.add_error(
                        ErrorType.SEMANTICO, linea,
                        "Duplicidad de declaración", lexema=nombre
                    )
                else:
                    self.symbol_table.declarar_variable(nombre, tipo_decl)
                
                # Verificar inicialización
                j = pos + 1
                if j < len(parts) and parts[j] == "=":
                    rhs_tokens = self._extract_rhs(parts, j + 1)
                    rhs_tipo, rhs_valor = self._inferir_tipo_y_valor(rhs_tokens)
                    
                    # Verificar compatibilidad
                    if rhs_tipo is not None:
                        self._check_type_compatibility(
                            tipo_decl, rhs_tipo, rhs_tokens, linea, nombre
                        )
                        
                        # Almacenar valor si es compatible
                        if rhs_valor is not None:
                            if tipo_decl == "/dec" and rhs_tipo == "/ent":
                                self.symbol_table.actualizar_valor(nombre, float(rhs_valor))
                            else:
                                self.symbol_table.actualizar_valor(nombre, rhs_valor)
                    
                    # Saltar tokens procesados
                    pos = self._skip_to_delimiter(parts, j + 1)
                else:
                    pos += 1
                
                # Continuar si hay coma
                if pos < len(parts) and parts[pos] == ",":
                    pos += 1
                continue
            
            pos += 1
    
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
        
        # Validar LHS
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
        
        # Inferir tipo del RHS
        if not rhs_tokens:
            self.error_handler.add_error(
                ErrorType.SEMANTICO, linea,
                "RHS inexistente en asignación", lexema=lhs
            )
            return
        
        rhs_tipo, rhs_valor = self._inferir_tipo_y_valor(rhs_tokens)
        
        # Verificar compatibilidad
        if rhs_tipo is not None:
            lhs_tipo = self.symbol_table.obtener_tipo(lhs)
            if lhs_tipo:
                self._check_type_compatibility(
                    lhs_tipo, rhs_tipo, rhs_tokens, linea, lhs
                )
                
                # Actualizar valor
                if rhs_valor is not None:
                    if lhs_tipo == "/dec" and rhs_tipo == "/ent":
                        self.symbol_table.actualizar_valor(lhs, float(rhs_valor))
                    else:
                        self.symbol_table.actualizar_valor(lhs, rhs_valor)
    
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
    
    def _inferir_tipo_y_valor(self, rhs_tokens: List[str]) -> Tuple[Optional[str], Optional[Any]]:
        """Infiere el tipo y valor de una expresión"""
        if not rhs_tokens:
            return None, None
        
        # Caso simple: un solo token
        if len(rhs_tokens) == 1:
            t = rhs_tokens[0]
            if RE_ENTERO.match(t):
                return "/ent", int(t)
            if RE_DECIMAL.match(t):
                return "/dec", float(t)
            if RE_CADENA.match(t):
                return "/cad", t[1:-1]
            if RE_IDENTIFICADOR.match(t):
                return self.symbol_table.obtener_tipo(t), None
            return None, None
        
        # Expresión compleja: inferir por presencia
        has_cad = any(RE_CADENA.match(t) for t in rhs_tokens)
        has_dec = any(RE_DECIMAL.match(t) for t in rhs_tokens)
        has_ent = any(RE_ENTERO.match(t) for t in rhs_tokens)
        
        if has_cad:
            return "/cad", None
        if has_dec:
            return "/dec", None
        if has_ent:
            return "/ent", None
        
        # Inferir de identificadores
        id_types = {
            self.symbol_table.obtener_tipo(t)
            for t in rhs_tokens
            if RE_IDENTIFICADOR.match(t)
        }
        id_types.discard(None)
        
        if len(id_types) == 1:
            return next(iter(id_types)), None
        
        return None, None
    
    def _check_type_compatibility(self, lhs_tipo: str, rhs_tipo: str,
                                   rhs_tokens: List[str], linea: int, lhs_name: str = ""):
        """Verifica compatibilidad de tipos"""
        compatible = (
            (lhs_tipo == "/ent" and rhs_tipo == "/ent") or
            (lhs_tipo == "/dec" and rhs_tipo in ("/ent", "/dec")) or
            (lhs_tipo == "/cad" and rhs_tipo == "/cad")
        )
        
        if not compatible:
            tipo_fuente = CANONICAL_TO_SOURCE.get(lhs_tipo, lhs_tipo)
            
            # Buscar lexema a mostrar
            show_lex = None
            
            if rhs_tipo == "/cad":
                for t in rhs_tokens:
                    if RE_CADENA.match(t):
                        show_lex = t
                        break
                    
            if show_lex is None and rhs_tipo == "/dec":
                for t in rhs_tokens:
                    if RE_DECIMAL.match(t):
                        show_lex = t
                        break
                    
            if show_lex is None and lhs_tipo == "/ent":
                for t in rhs_tokens:
                    if RE_DECIMAL.match(t):
                        show_lex = t
                        break
                
            if show_lex is None and lhs_tipo == "/cad":
                for t in rhs_tokens:
                    if not RE_CADENA.match(t):
                        show_lex = t
                        break
            
            if show_lex is None and rhs_tokens:
                show_lex = rhs_tokens[0]
            
            self.error_handler.add_error(
                ErrorType.SEMANTICO, linea,
                f"Incompatibilidad de tipo {tipo_fuente}",
                lexema=show_lex
            )