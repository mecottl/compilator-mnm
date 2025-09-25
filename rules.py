# rules.py
import re
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional
from enum import Enum

# ----------------- Config / Regex -----------------
RE_IDENTIFICADOR = re.compile(r'^mnm[A-Za-z0-9_]+$')   # identificadores comienzan con mnm
RE_ENTERO = re.compile(r'^\d+$')
RE_DECIMAL = re.compile(r'^\d+\.\d+$')

# Acepta: "texto", “texto”, 'texto', ‘texto’ (sin saltos de línea)
RE_CADENA = re.compile(r'^(?:"[^"\n]*"|“[^”\n]*”|\'[^\'\n]*\'|‘[^’\n]*’)$')

# Declaraciones válidas en fuente: solo con backslash "\ent", "\dec", "\cad"
VALID_DECL_FORMS = {"\\ent", "\\dec", "\\cad"}
# Formas NO PERMITIDAS en fuente: con slash "/ent", "/dec", "/cad"
INVALID_DECL_FORMS = {"/ent", "/dec", "/cad"}

# Tipos internos canónicos
CANONICAL_FROM_DECL = {"\\ent": "/ent", "\\dec": "/dec", "\\cad": "/cad"}
CANONICAL_TO_SOURCE = {"/ent": r"\ent", "/dec": r"\dec", "/cad": r"\cad"}

# Palabras clave que tokenizamos
KEYWORDS = {"print", "for", "in", "range"}

# Tokenizador (incluye comillas rectas y curvy)
TOKEN_PATTERN = re.compile(
    r'("([^"\n]*)"|“[^”\n]*”|\'[^\'\n]*\'|‘[^’\n]*’)|([\\/][A-Za-z]+)|([A-Za-z_][A-Za-z0-9_]*)|(\d+\.\d+|\d+)|([=;,+\-/*()\[\]{}:])'
)

# ----------------- Tipos de error -----------------
class ErrorType(Enum):
    SEMANTICO = "SEMÁNTICO"
    LEXICO = "LÉXICO"
    SINTACTICO = "SINTÁCTICO"
    OTRO = "OTRO"

@dataclass
class Token:
    lexema: str
    tipo: str
    linea: int
    descripcion: str = ""

@dataclass
class Error:
    token: str
    tipo: ErrorType
    linea: int
    mensaje: str
    lexema: Optional[str] = None

# ----------------- Compilador -----------------
class CompiladorMinimalista:
    def __init__(self):
        self.tokens: List[Token] = []
        self.errores: List[Error] = []
        self.tabla_simbolos: Dict[str, Dict[str, Any]] = {}
        self._err_counter = 0

    def _new_err_token(self) -> str:
        name = "err" if self._err_counter == 0 else f"err{self._err_counter}"
        self._err_counter += 1
        return name

    def _add_token(self, lexema: str, tipo: str, linea: int, descripcion: str = ""):
        self.tokens.append(Token(lexema=lexema, tipo=tipo, linea=linea, descripcion=descripcion))

    def _add_error(self, tipo: ErrorType, linea: int, mensaje: str, lexema: Optional[str] = None):
        tok = self._new_err_token()
        self.errores.append(Error(token=tok, tipo=tipo, linea=linea, mensaje=mensaje, lexema=lexema))

    def analizar_codigo(self, codigo: str) -> Tuple[List[Error], List[Token], Dict[str, Any]]:
        # reset
        self.tokens = []
        self.errores = []
        self.tabla_simbolos = {}
        self._err_counter = 0

        declarados: Dict[str, str] = {}  # nombre -> '/ent' | '/dec' | '/cad'
        salida_simulada: List[str] = []

        def registrar_en_tabla(lex: str, tipo: str, valor: Optional[Any] = None):
            if lex in self.tabla_simbolos:
                if valor is not None:
                    self.tabla_simbolos[lex]["valor"] = valor
                if not self.tabla_simbolos[lex].get("tipo") and tipo:
                    self.tabla_simbolos[lex]["tipo"] = tipo
            else:
                self.tabla_simbolos[lex] = {"tipo": tipo, "valor": valor}

        lineas = codigo.splitlines()
        for idx, linea in enumerate(lineas, start=1):
            texto = linea.strip()
            if texto == "":
                continue

            parts = [m.group(0) for m in TOKEN_PATTERN.finditer(texto)]

            # tokens crudos (para la GUI)
            for p in parts:
                tok_type = "OTRO"
                p_lower = p.lower()
                if p in INVALID_DECL_FORMS:
                    tok_type = "PALABRA_RESERVADA"
                    self._add_error(ErrorType.SEMANTICO, idx,
                                    "forma de declaración inválida (use '\\ent', '\\dec' o '\\cad')",
                                    lexema=p)
                elif p in VALID_DECL_FORMS:
                    tok_type = "PALABRA_RESERVADA"
                elif p_lower in KEYWORDS:
                    tok_type = "PALABRA_RESERVADA"
                elif RE_IDENTIFICADOR.match(p):
                    tok_type = "IDENTIFICADOR"
                elif RE_ENTERO.match(p):
                    tok_type = "CONSTANTE_ENTERA"
                elif RE_DECIMAL.match(p):
                    tok_type = "CONSTANTE_DECIMAL"
                elif RE_CADENA.match(p):
                    tok_type = "CONSTANTE_CADENA"
                elif p in ("=", ";", "+", "-", "/", "*", "(", ")", ",", "[", "]", "{", "}", ":"):
                    tok_type = "SIMBOLO"
                self._add_token(p, tok_type, idx)

                # tabla de símbolos básica
                if tok_type == "SIMBOLO" or tok_type == "PALABRA_RESERVADA":
                    registrar_en_tabla(p, "", None)
                elif tok_type == "CONSTANTE_ENTERA":
                    registrar_en_tabla(p, "\ent", int(p))
                elif tok_type == "CONSTANTE_DECIMAL":
                    registrar_en_tabla(p, "\dec", float(p))
                elif tok_type == "CONSTANTE_CADENA":
                    registrar_en_tabla(p, "\cad", p[1:-1])

            # -------- Declaraciones (con posible inicialización) --------
            if parts:
                first = parts[0]
                if first in VALID_DECL_FORMS:
                    tipo_decl = CANONICAL_FROM_DECL[first]

                    def inferir_tipo_y_valor(rhs_tokens: List[str]) -> Tuple[Optional[str], Optional[Any]]:
                        # Inferencia compatible con tu bloque de asignaciones
                        if not rhs_tokens:
                            return None, None
                        if len(rhs_tokens) == 1:
                            t = rhs_tokens[0]
                            if RE_ENTERO.match(t):   return "/ent", int(t)
                            if RE_DECIMAL.match(t):  return "/dec", float(t)
                            if RE_CADENA.match(t):   return "/cad", t[1:-1]
                            if RE_IDENTIFICADOR.match(t):
                                return declarados.get(t), None
                            return None, None
                        # Expresión: presencia decide
                        has_cad = any(RE_CADENA.match(t) for t in rhs_tokens)
                        has_dec = any(RE_DECIMAL.match(t) for t in rhs_tokens)
                        has_ent = any(RE_ENTERO.match(t) for t in rhs_tokens)
                        if has_cad: return "/cad", None
                        if has_dec: return "/dec", None
                        if has_ent: return "/ent", None
                        id_types = {declarados.get(t) for t in rhs_tokens if RE_IDENTIFICADOR.match(t)}
                        id_types.discard(None)
                        if len(id_types) == 1:
                            return next(iter(id_types)), None
                        return None, None

                    pos = 1
                    while pos < len(parts):
                        tok = parts[pos]
                        if tok == ";":
                            break

                        if RE_IDENTIFICADOR.match(tok):
                            nombre = tok
                            if nombre in declarados:
                                self._add_error(ErrorType.SEMANTICO, idx, "Duplicidad de declaración", lexema=nombre)
                            else:
                                declarados[nombre] = tipo_decl
                                registrar_en_tabla(nombre, tipo_decl, None)

                            # ¿viene una inicialización?
                            j = pos + 1
                            if j < len(parts) and parts[j] == "=":
                                # recolectar RHS hasta coma o punto y coma
                                rhs_tokens: List[str] = []
                                k = j + 1
                                while k < len(parts) and parts[k] not in {",", ";"}:
                                    if parts[k].strip():
                                        rhs_tokens.append(parts[k])
                                    k += 1

                                # inferir tipo/valor del RHS
                                rhs_tipo, rhs_valor = inferir_tipo_y_valor(rhs_tokens)

                                # compatibilidad estricta
                                if rhs_tipo is not None:
                                    lhs_tipo = tipo_decl
                                    compatible = (
                                        (lhs_tipo == "/ent" and rhs_tipo == "/ent") or
                                        (lhs_tipo == "/dec" and rhs_tipo in ("/ent", "/dec")) or
                                        (lhs_tipo == "/cad" and rhs_tipo == "/cad")
                                    )
                                    if not compatible:
                                        tipo_fuente = CANONICAL_TO_SOURCE.get(lhs_tipo, lhs_tipo)
                                        # Mostrar la cadena si existe; si no, el primer token del RHS
                                        show_lex = None
                                        for t in rhs_tokens:
                                            if RE_CADENA.match(t):
                                                show_lex = t; break
                                        self._add_error(
                                            ErrorType.SEMANTICO, idx,
                                            f"Incompatibilidad de tipo {tipo_fuente}",
                                            lexema=show_lex if show_lex is not None else (rhs_tokens[0] if rhs_tokens else None)
                                        )
                                    else:
                                        # almacenar valor si es constante
                                        if rhs_valor is not None:
                                            if lhs_tipo == "/dec" and rhs_tipo == "/ent":
                                                registrar_en_tabla(nombre, lhs_tipo, float(rhs_valor))
                                            else:
                                                registrar_en_tabla(nombre, lhs_tipo, rhs_valor)

                                # saltar hasta k (ya procesamos '=' y RHS)
                                pos = k
                            else:
                                pos += 1

                            # si hay coma, consumirla aquí para continuar con el siguiente id
                            if pos < len(parts) and parts[pos] == ",":
                                pos += 1
                            continue

                        # cualquier otro token (p.ej. comas sueltas) se avanza
                        pos += 1

                    registrar_en_tabla(first, "", None)
                    continue

                if first in INVALID_DECL_FORMS:
                    # ya se reportó el error en la tokenización
                    continue


            # -------- Asignaciones --------
            if "=" in parts:
                try:
                    pos_eq = parts.index("=")
                except ValueError:
                    pos_eq = -1

                if pos_eq > 0:
                    lhs = parts[pos_eq - 1] if pos_eq - 1 >= 0 else None

                    # recolectar TODOS los tokens del RHS hasta ';'
                    rhs_tokens: List[str] = []
                    for tok in parts[pos_eq + 1:]:
                        if tok == ";":
                            break
                        if tok.strip() == "":
                            continue
                        rhs_tokens.append(tok)

                    registrar_en_tabla("=", "", None)

                    # validar LHS
                    if lhs is None or not RE_IDENTIFICADOR.match(lhs):
                        self._add_error(ErrorType.SEMANTICO, idx, "LHS inválido en asignación", lexema=str(lhs))
                    else:
                        if lhs not in declarados:
                            self._add_error(ErrorType.SEMANTICO, idx, "Variable indefinida", lexema=lhs)
                            registrar_en_tabla(lhs, "", None)
                        else:
                            registrar_en_tabla(lhs, declarados[lhs], None)

                        # --- Inferencia de tipo del RHS ---
                        rhs_tipo: Optional[str] = None
                        rhs_valor: Optional[Any] = None

                        if not rhs_tokens:
                            self._add_error(ErrorType.SEMANTICO, idx, "RHS inexistente en asignación", lexema=lhs)
                        else:
                            if len(rhs_tokens) == 1:
                                rhs = rhs_tokens[0]
                                if RE_ENTERO.match(rhs):
                                    rhs_tipo = "/ent"; rhs_valor = int(rhs)
                                elif RE_DECIMAL.match(rhs):
                                    rhs_tipo = "/dec"; rhs_valor = float(rhs)
                                elif RE_CADENA.match(rhs):
                                    rhs_tipo = "/cad"; rhs_valor = rhs[1:-1]
                                elif RE_IDENTIFICADOR.match(rhs):
                                    if rhs not in declarados:
                                        self._add_error(ErrorType.SEMANTICO, idx, "Variable indefinida", lexema=rhs)
                                        registrar_en_tabla(rhs, "", None)
                                    else:
                                        rhs_tipo = declarados[rhs]
                                else:
                                    self._add_error(ErrorType.SEMANTICO, idx, "RHS no reconocido", lexema=str(rhs))
                            else:
                                # Hay una expresión: inferimos tipo por presencia
                                has_cad = any(RE_CADENA.match(t) for t in rhs_tokens)
                                has_dec = any(RE_DECIMAL.match(t) for t in rhs_tokens)
                                has_ent = any(RE_ENTERO.match(t) for t in rhs_tokens)

                                if has_cad:
                                    rhs_tipo = "/cad"
                                    # valor solo si la expresión es exactamente una cadena, que no es el caso
                                    rhs_valor = None
                                elif has_dec:
                                    rhs_tipo = "/dec"; rhs_valor = None
                                elif has_ent:
                                    rhs_tipo = "/ent"; rhs_valor = None
                                else:
                                    # mirar tipos de identificadores (si todos coinciden, usa ese)
                                    id_types = {declarados.get(t) for t in rhs_tokens if RE_IDENTIFICADOR.match(t)}
                                    id_types.discard(None)
                                    if len(id_types) == 1:
                                        rhs_tipo = next(iter(id_types))
                                    # si no podemos inferir, lo dejamos como None y no asignamos valor

                        # --- Compatibilidad estricta ---
                        if lhs in declarados and rhs_tipo is not None:
                            lhs_tipo = declarados[lhs]
                            compatible = (
                                (lhs_tipo == "/ent" and rhs_tipo == "/ent") or
                                (lhs_tipo == "/dec" and rhs_tipo in ("/ent", "/dec")) or
                                (lhs_tipo == "/cad" and rhs_tipo == "/cad")
                            )
                            if not compatible:
                                tipo_fuente = CANONICAL_TO_SOURCE.get(lhs_tipo, lhs_tipo)
                                # lexema: si hay cadena en la expresión, intenta mostrar esa cadena
                                show_lex = None
                                for t in rhs_tokens:
                                    if RE_CADENA.match(t):
                                        show_lex = t; break
                                self._add_error(ErrorType.SEMANTICO, idx,
                                                f"Incompatibilidad de tipo {tipo_fuente}",
                                                lexema=show_lex if show_lex is not None else (rhs_tokens[0] if rhs_tokens else None))
                            else:
                                if rhs_valor is not None:
                                    if lhs_tipo == "/dec" and rhs_tipo == "/ent":
                                        registrar_en_tabla(lhs, lhs_tipo, float(rhs_valor))
                                    else:
                                        registrar_en_tabla(lhs, lhs_tipo, rhs_valor)

            # -------- variables no declaradas usadas en la línea --------
            for p in parts:
                if RE_IDENTIFICADOR.match(p) and p not in declarados:
                    self._add_error(ErrorType.SEMANTICO, idx, "Variable indefinida", lexema=p)
                    registrar_en_tabla(p, "", None)

            for tok in parts:
                if isinstance(tok, str) and tok.lower() in KEYWORDS:
                    registrar_en_tabla(tok.lower(), "", None)

        # ---- Deduplicado de errores ----
        errores_unicos: List[Error] = []
        seen = set()
        for e in self.errores:
            key = (e.lexema if e.lexema is not None else "", e.linea, e.mensaje)
            if key in seen: 
                continue
            seen.add(key); errores_unicos.append(e)
        self.errores = errores_unicos

        # ---- Deduplicado de tokens ----
        tokens_unicos: List[Token] = []
        seen_t = set()
        for t in self.tokens:
            key = (t.lexema, t.tipo, t.linea)
            if key in seen_t: 
                continue
            seen_t.add(key); tokens_unicos.append(t)
        self.tokens = tokens_unicos

        # ---- Tabla de símbolos final ordenada ----
        tabla_final: Dict[str, Dict[str, Any]] = {}
        for nombre, info in self.tabla_simbolos.items():
            if (RE_IDENTIFICADOR.match(nombre)
                or RE_ENTERO.match(nombre)
                or RE_DECIMAL.match(nombre)
                or RE_CADENA.match(nombre)
                or info.get("tipo") in ("SIMBOLO", "PALABRA_RESERVADA", "IDENTIFICADOR", "")):
                tabla_final[nombre] = {"tipo": info.get("tipo"), "valor": info.get("valor")}
            else:
                if nombre.lower() in KEYWORDS or nombre in VALID_DECL_FORMS or nombre in INVALID_DECL_FORMS:
                    tabla_final[nombre] = {"tipo": info.get("tipo"), "valor": info.get("valor")}
        tabla_final = dict(sorted(tabla_final.items(), key=lambda kv: kv[0]))

        info_adicional = {"tabla_simbolos": tabla_final, "salida_ejecucion": salida_simulada}
        return self.errores, self.tokens, info_adicional

# ----------------- API pública -----------------
_compilador_singleton = CompiladorMinimalista()

def analizar_codigo(codigo: str) -> Tuple[List[Error], List[Token], Dict[str, Any]]:
    return _compilador_singleton.analizar_codigo(codigo)

def obtener_tabla_simbolos(info_adicional: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return info_adicional.get("tabla_simbolos", {})

def obtener_salida_ejecucion(info_adicional: Dict[str, Any]) -> List[str]:
    return info_adicional.get("salida_ejecucion", [])

# ----------------- prueba rápida (opcional) -----------------
if __name__ == "__main__":
    ejemplo = r"""\ent mnmE; \dec mnmD; \cad mnmS;
mnmE = 10;                 // OK
mnmD = 100;                // OK -> 100.0
mnmD = 2.5;                // OK
mnmS = “hola”;             // OK (curvy)
mnmE = “10”;               // ERROR: \ent no acepta cadenas
mnmE = 33 + “1”;           // ERROR: expresión con cadena => incompatible con \ent
mnmD = 33 + 7;             // OK (se infiere numérica, no se calcula)
mnmS = 1 + “x”;            // ERROR: incompatible con \cad
"""
    errs, toks, info = analizar_codigo(ejemplo)
    print("ERRORES:")
    for e in errs:
        print(f"{e.token} | {e.lexema} | L{e.linea} | {e.mensaje}")
    print("\nTABLA SIMBOLOS:")
    for k, v in info["tabla_simbolos"].items():
        print(k, v)
