# lexer.py - Análisis léxico (tokenización)
from typing import List, Tuple
from .models import Token
from .constants import (
    TOKEN_PATTERN, RE_IDENTIFICADOR, RE_ENTERO, RE_DECIMAL, RE_CADENA,
    VALID_DECL_FORMS, INVALID_DECL_FORMS, KEYWORDS, VALID_SYMBOLS
)


class Lexer:
    """Analizador léxico - convierte código fuente en tokens"""
    
    def __init__(self):
        self.tokens: List[Token] = []
    
    def reset(self):
        """Reinicia el lexer"""
        self.tokens = []
    
    def tokenize(self, codigo: str) -> Tuple[List[Token], List[List[str]]]:
        """
        Tokeniza el código fuente
        
        Returns:
            Tuple con:
            - Lista de tokens identificados
            - Lista de listas de strings (tokens por línea)
        """
        self.reset()
        lineas = codigo.splitlines()
        tokens_por_linea: List[List[str]] = []
        
        for idx, linea in enumerate(lineas, start=1):
            
            # --- ¡INICIO DE LA MODIFICACIÓN! ---
            # 1. Separar la línea por el delimitador de comentario '//'
            #    y tomar solo la primera parte (el código).
            linea_sin_comentarios = linea.split('//', 1)[0]
            
            # 2. Limpiar espacios en blanco de la línea ya sin comentarios
            texto = linea_sin_comentarios.strip()
            # --- FIN DE LA MODIFICACIÓN! ---
            
            if texto == "":
                tokens_por_linea.append([])
                continue
            
            # Extraer tokens de la línea
            parts = [m.group(0) for m in TOKEN_PATTERN.finditer(texto)]
            tokens_por_linea.append(parts)
            
            # Clasificar cada token
            for p in parts:
                tok_type = self._classify_token(p)
                self._add_token(p, tok_type, idx)
        
        # Deduplicar tokens
        self._deduplicate_tokens()
        
        return self.tokens, tokens_por_linea
    
    def _classify_token(self, token: str) -> str:
        """Clasifica un token según su tipo"""
        token_lower = token.lower()
        
        # Declaraciones inválidas
        if token in INVALID_DECL_FORMS:
            return "PALABRA_RESERVADA"
        
        # Declaraciones válidas
        if token in VALID_DECL_FORMS:
            return "PALABRA_RESERVADA"
        
        # Palabras clave
        if token_lower in KEYWORDS:
            return "PALABRA_RESERVADA"
        
        # Identificadores
        if RE_IDENTIFICADOR.match(token):
            return "IDENTIFICADOR"
        
        # Constantes numéricas
        if RE_ENTERO.match(token):
            return "CONSTANTE_ENTERA"
        
        if RE_DECIMAL.match(token):
            return "CONSTANTE_DECIMAL"
        
        # Cadenas
        if RE_CADENA.match(token):
            return "CONSTANTE_CADENA"
        
        # Símbolos
        if token in VALID_SYMBOLS:
            return "SIMBOLO"
        
        return "OTRO"
    
    def _add_token(self, lexema: str, tipo: str, linea: int, descripcion: str = ""):
        """Agrega un token a la lista"""
        self.tokens.append(Token(lexema=lexema, tipo=tipo, linea=linea, descripcion=descripcion))
    
    def _deduplicate_tokens(self):
        """Elimina tokens duplicados"""
        tokens_unicos: List[Token] = []
        seen = set()
        
        for t in self.tokens:
            key = (t.lexema, t.tipo, t.linea)
            if key in seen:
                continue
            seen.add(key)
            tokens_unicos.append(t)
        
        self.tokens = tokens_unicos
    
    def get_tokens(self) -> List[Token]:
        """Retorna todos los tokens"""
        return self.tokens