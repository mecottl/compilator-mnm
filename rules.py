# rules.py
import re
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional
from enum import Enum

# ----------------- Config / Regex -----------------
RE_IDENTIFICADOR = re.compile(r'^mnm[A-Za-z0-9_]+$')   # identificadores comienzan con mnm
RE_ENTERO = re.compile(r'^\d+$')
RE_DECIMAL = re.compile(r'^\d+\.\d+$')
RE_CADENA = re.compile(r'^".*"$')

# Declaraciones válidas en fuente: sólo con backslash "\ent", "\dec", "\cad"
VALID_DECL_FORMS = {"\\ent", "\\dec", "\\cad"}
# Formas NO PERMITIDAS en fuente: con slash "/ent", "/dec", "/cad"
INVALID_DECL_FORMS = {"/ent", "/dec", "/cad"}

# Internal canonical type names (usadas internamente para comparar tipos)
# Usamos las formas internas '/ent', '/dec', '/cad' para comparar tipos,
# pero en las descripciones mostramos la forma de fuente con backslash.
CANONICAL_FROM_DECL = {
    "\\ent": "/ent",
    "\\dec": "/dec",
    "\\cad": "/cad"
}
CANONICAL_TO_SOURCE = {
    "/ent": r"\ent",
    "/dec": r"\dec",
    "/cad": r"\cad"
}

# Palabras clave adicionales que quieres ver en la tabla
KEYWORDS = {"print", "for", "in", "range"}

# Patrón para tokenizar: cadenas, formas con slash/backslash, ids, números, operadores/símbolos, palabras
TOKEN_PATTERN = re.compile(
    r'(".*?")|([\\/][A-Za-z]+)|([A-Za-z_][A-Za-z0-9_]*)|(\d+\.\d+|\d+)|([=;,+\-/*()\[\]{}:])'
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
    token: str           # 'err', 'err1', ...
    tipo: ErrorType      # enum para que .value funcione en GUI
    linea: int
    mensaje: str
    lexema: Optional[str] = None  # lexema relacionado (p.ej. el literal o identificador)

# ----------------- Compilador -----------------
class CompiladorMinimalista:
    def __init__(self):
        self.tokens: List[Token] = []
        self.errores: List[Error] = []
        self.tabla_simbolos: Dict[str, Dict[str, Any]] = {}
        self._err_counter = 0

    def _new_err_token(self) -> str:
        if self._err_counter == 0:
            name = "err"
        else:
            name = f"err{self._err_counter}"
        self._err_counter += 1
        return name

    def _add_token(self, lexema: str, tipo: str, linea: int, descripcion: str = ""):
        self.tokens.append(Token(lexema=lexema, tipo=tipo, linea=linea, descripcion=descripcion))

    def _add_error(self, tipo: ErrorType, linea: int, mensaje: str, lexema: Optional[str] = None):
        tok = self._new_err_token()
        self.errores.append(Error(token=tok, tipo=tipo, linea=linea, mensaje=mensaje, lexema=lexema))

    def analizar_codigo(self, codigo: str) -> Tuple[List[Error], List[Token], Dict[str, Any]]:
        """
        Analiza el código y devuelve (errores, tokens, info_adicional).
        info_adicional incluye:
          - 'tabla_simbolos': dict lexema -> {'tipo': <...>, 'valor': <...>}
          - 'salida_ejecucion': list de strings (simulada)
        """
        # reset
        self.tokens = []
        self.errores = []
        self.tabla_simbolos = {}
        self._err_counter = 0

        declarados: Dict[str, str] = {}  # nombre -> tipo declarado interno ('/ent', '/dec', '/cad')
        salida_simulada: List[str] = []

        # Helper: asegurar inserción en tabla_simbolos sin duplicados
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

            # tokenizar todo
            parts = [m.group(0) for m in TOKEN_PATTERN.finditer(texto)]

            # Añadir tokens para la vista raw
            for p in parts:
                tipo_token = "OTRO"
                p_lower = p.lower()
                # detectar formas inválidas con slash (p. ej. /ent) -> error semántico (pero dejamos mensaje específico aparte)
                if p in INVALID_DECL_FORMS:
                    tipo_token = "PALABRA_RESERVADA"
                    # agregar un error para la forma de declaración inválida (tipo SEMANTICO)
                    # Mensaje no es uno de los tres solicitados; lo añadimos para informar sintaxis inválida.
                    self._add_error(ErrorType.SEMANTICO, idx,
                                    "forma de declaración inválida (use '\\ent', '\\dec' o '\\cad')",
                                    lexema=p)
                elif p in VALID_DECL_FORMS:
                    tipo_token = "PALABRA_RESERVADA"
                elif p_lower in KEYWORDS:
                    tipo_token = "PALABRA_RESERVADA"
                elif RE_IDENTIFICADOR.match(p):
                    tipo_token = "IDENTIFICADOR"
                elif RE_ENTERO.match(p):
                    tipo_token = "CONSTANTE_ENTERA"
                elif RE_DECIMAL.match(p):
                    tipo_token = "CONSTANTE_DECIMAL"
                elif RE_CADENA.match(p):
                    tipo_token = "CONSTANTE_CADENA"
                elif p in ("=", ";", "+", "-", "/", "*", "(", ")", ",", "[", "]", "{", "}", ":"):
                    tipo_token = "SIMBOLO"
                else:
                    tipo_token = "OTRO"

                self._add_token(lexema=p, tipo=tipo_token, linea=idx, descripcion="")

                # Registrar en tabla_simbolos según tipo
                if tipo_token == "SIMBOLO":
                    registrar_en_tabla(p, "", None)
                elif tipo_token == "PALABRA_RESERVADA":
                    registrar_en_tabla(p, "", None)
                elif tipo_token == "CONSTANTE_ENTERA":
                    registrar_en_tabla(p, "\ent", int(p))
                elif tipo_token == "CONSTANTE_DECIMAL":
                    registrar_en_tabla(p, "\dec", float(p))
                elif tipo_token == "CONSTANTE_CADENA":
                    registrar_en_tabla(p, "\cad", p[1:-1])
                # IDENTIFICADOR se registra al declararse o asignarse

            # ---------------- Declaraciones (solo con backslash) ----------------
            if parts:
                first = parts[0]
                if first in VALID_DECL_FORMS:
                    tipo_decl_internal = CANONICAL_FROM_DECL.get(first)
                    pos = 1
                    while pos < len(parts):
                        tok = parts[pos]
                        if tok == ";":
                            break
                        if RE_IDENTIFICADOR.match(tok):
                            nombre = tok
                            if nombre in declarados:
                                # duplicidad: mensaje EXACTO pedido
                                self._add_error(ErrorType.SEMANTICO, idx, "Duplicidad de declaración", lexema=nombre)
                            else:
                                declarados[nombre] = tipo_decl_internal
                                registrar_en_tabla(nombre, tipo_decl_internal, None)
                        pos += 1
                    # registrar la palabra reservada de declaración en tabla
                    registrar_en_tabla(first, "", None)
                    continue
                # si es forma inválida (p. ej. /ent), ya añadimos error durante tokenización; no procesamos como declaración
                if first in INVALID_DECL_FORMS:
                    continue

            # ---------------- Asignaciones: <id> = <valor> ; ----------------
            if "=" in parts:
                try:
                    pos_eq = parts.index("=")
                except ValueError:
                    pos_eq = -1

                if pos_eq > 0:
                    lhs = parts[pos_eq - 1] if pos_eq - 1 >= 0 else None
                    rhs = None
                    for tok in parts[pos_eq + 1:]:
                        if tok == ";":
                            break
                        if tok.strip() == "":
                            continue
                        rhs = tok
                        break

                    registrar_en_tabla("=", "", None)

                    # validar LHS
                    if lhs is None or not RE_IDENTIFICADOR.match(lhs):
                        # LHS inválido (no entró en los 3 tipos requeridos), informamos error general
                        self._add_error(ErrorType.SEMANTICO, idx, "LHS inválido en asignación", lexema=str(lhs))
                    else:
                        if lhs not in declarados:
                            # variable indefinida: mensaje EXACTO pedido
                            self._add_error(ErrorType.SEMANTICO, idx, "Variable indefinida", lexema=lhs)
                            registrar_en_tabla(lhs, "", None)
                        else:
                            registrar_en_tabla(lhs, declarados[lhs], None)

                        rhs_tipo = None
                        rhs_valor: Optional[Any] = None

                        if rhs is None:
                            # error general
                            self._add_error(ErrorType.SEMANTICO, idx, "RHS inexistente en asignación", lexema=lhs)
                        else:
                            if RE_ENTERO.match(rhs):
                                rhs_tipo = "/ent"
                                rhs_valor = int(rhs)
                            elif RE_DECIMAL.match(rhs):
                                rhs_tipo = "/dec"
                                rhs_valor = float(rhs)
                            elif RE_CADENA.match(rhs):
                                rhs_tipo = "/cad"
                                rhs_valor = rhs[1:-1]
                            elif RE_IDENTIFICADOR.match(rhs):
                                if rhs not in declarados:
                                    # variable indefinida en RHS: mensaje EXACTO pedido
                                    self._add_error(ErrorType.SEMANTICO, idx, "Variable indefinida", lexema=rhs)
                                    registrar_en_tabla(rhs, "IDENTIFICADOR", None)
                                else:
                                    rhs_tipo = declarados[rhs]
                            else:
                                self._add_error(ErrorType.SEMANTICO, idx, "RHS no reconocido", lexema=str(rhs))

                        # compatibilidad de tipos: si lhs declarado y rhs_tipo conocido
                        if lhs in declarados and rhs_tipo is not None:
                            lhs_tipo = declarados[lhs]
                            if lhs_tipo != rhs_tipo:
                                # incompatibilidad: mensaje EXACTO pedido, mostrar tipo fuente (backslash) del LHS
                                tipo_fuente = CANONICAL_TO_SOURCE.get(lhs_tipo, lhs_tipo)
                                # lexema: según tu ejemplo, queremos que la columna "Lexema" muestre el valor intentado (rhs)
                                self._add_error(ErrorType.SEMANTICO, idx, f"Incompatibilidad de tipo {tipo_fuente}", lexema=rhs)
                            else:
                                # si RHS es constante actualizamos valor en tabla
                                if rhs_valor is not None:
                                    registrar_en_tabla(lhs, lhs_tipo, rhs_valor)

            # ---------------- detectar usos de identificadores no declarados en la línea ----------------
            # (esto puede repetir algunos errores ya reportados; se deduplican al final)
            for p in parts:
                if RE_IDENTIFICADOR.match(p):
                    if p not in declarados:
                        # variable indefinida (mensaje EXACTO)
                        self._add_error(ErrorType.SEMANTICO, idx, "Variable indefinida", lexema=p)
                        registrar_en_tabla(p, "", None)

            # ---------------- registrar keywords como símbolos en tabla ----------------
            for tok in parts:
                if isinstance(tok, str) and tok.lower() in KEYWORDS:
                    registrar_en_tabla(tok.lower(), "", None)

        # ------------------- DEDUPLICADO FINAL -------------------
        errores_unicos: List[Error] = []
        seen_lex_renglon = set()
        for e in self.errores:
            key = (e.lexema if e.lexema is not None else "", e.linea, e.mensaje)
            if key in seen_lex_renglon:
                continue
            seen_lex_renglon.add(key)
            errores_unicos.append(e)
        self.errores = errores_unicos

        # Tokens: eliminar duplicados exactos (lexema, tipo, linea)
        tokens_unicos: List[Token] = []
        seen_tokens = set()
        for t in self.tokens:
            key = (t.lexema, t.tipo, t.linea)
            if key in seen_tokens:
                continue
            seen_tokens.add(key)
            tokens_unicos.append(t)
        self.tokens = tokens_unicos

        # Filtrar y formatear tabla_simbolos final
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

        # ordenar por nombre para presentación consistente
        tabla_final = dict(sorted(tabla_final.items(), key=lambda kv: kv[0]))

        info_adicional = {
            "tabla_simbolos": tabla_final,
            "salida_ejecucion": salida_simulada
        }

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
    ejemplo = r"""\ent mnmoi
mnmoi = 1.3
/ent mnmMalUso = 5;
\ent mnmA; \ent mnmA;
print(mnmNoDecl)"""
    errs, toks, info = analizar_codigo(ejemplo)
    print("ERRORES:")
    for e in errs:
        print(f"{e.token} | {e.lexema} | L{e.linea} | {e.mensaje}")
    print("\nTABLA SIMBOLOS:")
    for k,v in info["tabla_simbolos"].items():
        print(k, v)
