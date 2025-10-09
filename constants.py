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
KEYWORDS = {"print", "for", "in", "range"}

# ===== PATRÓN DE TOKENIZACIÓN =====
TOKEN_PATTERN = re.compile(
    r'("([^"\n]*)"|\'[^\'\n]*\')|([\\/][A-Za-z]+)|([A-Za-z_][A-Za-z0-9_]*)|(\d+\.\d+|\d+)|([=;,+\-/*()\[\]{}:])'
)

# ===== SÍMBOLOS VÁLIDOS =====
VALID_SYMBOLS = {"=", ";", "+", "-", "/", "*", "(", ")", ",", "[", "]", "{", "}", ":"}