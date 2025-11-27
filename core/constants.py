# constants.py - Constantes, regex y configuraciones del compilador
import re

# ===== EXPRESIONES REGULARES =====
RE_IDENTIFICADOR = re.compile(r'^mnm[A-Za-z0-9_]+$')
RE_ENTERO = re.compile(r'^\d+$')
RE_DECIMAL = re.compile(r'^\d+\.\d+$')
RE_CADENA = re.compile(r'^(?:"[^"\n]*"|\'[^\'\n]*\')$')

# ===== FORMAS DE DECLARACIÓN =====
VALID_DECL_FORMS = {"\\ent", "\\dec", "\\cad"}
INVALID_DECL_FORMS = {"/ent", "/dec", "/cad"}

# ===== CONVERSIÓN DE TIPOS =====
CANONICAL_FROM_DECL = {"\\ent": "/ent", "\\dec": "/dec", "\\cad": "/cad"}
CANONICAL_TO_SOURCE = {"/ent": r"\ent", "/dec": r"\dec", "/cad": r"\cad"}

# ===== PALABRAS CLAVE =====
# 'in' y 'range' pueden quedarse, no hacen daño
KEYWORDS = {"print", "for", "in", "range"} 

# ===== PATRÓN DE TOKENIZACIÓN =====
# <--- ¡MODIFICADO! ---
# Hemos añadido '||', '&&', '==', '!=', '<=', '>=', y caracteres sueltos '<', '>', '!'
# Es CRÍTICO que los operadores de 2 caracteres (ej: '||') vayan ANTES
# que los de 1 caracter (ej: '|') en la expresión regular.
TOKEN_PATTERN = re.compile(
    r'("([^"\n]*)"|\'[^\'\n]*\')|'  # 1. Cadenas
    r'([\\/][A-Za-z]+)|'          # 2. Declaraciones (\ent, /ent)
    r'([A-Za-z_][A-Za-z0-9_]*)|'  # 3. Identificadores y Palabras Clave (mnmVar, for)
    r'(\d+\.\d+|\d+)|'            # 4. Números (10.5, 10)
    
    # 5. Operadores y Símbolos (¡NUEVO Y ORDENADO!)
    r'(\|\||&&|==|!=|<=|>=|'     # Operadores multi-caracter
    r'[=;,+\-/*()\[\]{}:<>]|'
    r'[%]|' # Operadores de un caracter
    r'[!&|])'                    # Operadores lógicos de un caracter
)

# ===== SÍMBOLOS VÁLIDOS =====
# <--- ¡MODIFICADO! ---
# Añadimos todos los nuevos operadores para que _classify_token() los reconozca
VALID_SYMBOLS = {
    # Originales
    "=", ";", "+", "-", "/", "*", "(", ")", ",", "[", "]", "{", "}", ":", "%",
    # Nuevos (Lógicos y Relacionales)
    "||", "&&", "==", "!=", "<=", ">=", "<", ">", "!"
}