# rules.py
import re
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional
from enum import Enum

# ----------------- Config / Regex -----------------
RE_IDENTIFICADOR = re.compile(r'^mnm[A-Za-z0-9_]+$')  # identificadores comienzan con mnm
RE_ENTERO = re.compile(r'^\d+$')
RE_DECIMAL = re.compile(r'^\d+\.\d+$')
RE_CADENA = re.compile(r'^".*"$')

# Aceptamos tanto \ent como /ent ya que tu ejemplo usa /ent
RESERVED = {"\\ent", "/ent", "\\dec", "/dec", "\\cad", "/cad"}

# patrón simple para tokenizar
TOKEN_PATTERN = re.compile(
    r'(".*?")|([\\/][a-zA-Z]+)|([A-Za-z_][A-Za-z0-9_]*)|(\d+\.\d+|\d+)|([=;,+\-/*()\[\]])'
)

# ----------------- Tipos -----------------
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
    lexema: Optional[str] = None  # útil para deduplicado (lexema + renglón)

# ----------------- Compilador (implem. modular) -----------------
class CompiladorMinimalista:
    def __init__(self):
        self.tokens: List[Token] = []
        self.errores: List[Error] = []
        self.tabla_simbolos: Dict[str, Dict[str, Any]] = {}
        self._err_counter = 0

    # Generador de nombres de token de error: err, err1, err2...
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
        Analiza código y devuelve (errores, tokens, info_adicional).
        info_adicional incluye:
          - 'tabla_simbolos': dict nombre -> {'tipo': <\\ent|/ent|\\dec...>, 'valor': <val o None>}
          - 'salida_ejecucion': list de strings (simulada)
        """
        # reset estado
        self.tokens = []
        self.errores = []
        self.tabla_simbolos = {}
        self._err_counter = 0

        declarados: Dict[str, str] = {}  # nombre -> tipo declarado (e.g. /ent, \dec)
        salida_simulada: List[str] = []

        lineas = codigo.splitlines()
        for idx, linea in enumerate(lineas, start=1):
            texto = linea.strip()
            if texto == "":
                continue

            # tokenizar la línea
            parts = [m.group(0) for m in TOKEN_PATTERN.finditer(texto)]

            # añadir tokens básicos para GUI
            for p in parts:
                tipo_token = "DESCONOCIDO"
                if p in RESERVED:
                    tipo_token = "Vacio"
                elif RE_IDENTIFICADOR.match(p):
                    tipo_token = "IDENTIFICADOR"
                elif RE_ENTERO.match(p):
                    tipo_token = "\ent"
                elif RE_DECIMAL.match(p):
                    tipo_token = "\dec"
                elif RE_CADENA.match(p):
                    tipo_token = "\cad"
                elif p in ("=", ";", "+", "-", "/", "*", "(", ")", ","):
                    tipo_token = "Vacio"
                else:
                    tipo_token = "Vacio"
                self._add_token(lexema=p, tipo=tipo_token, linea=idx, descripcion="")

            # ---- Declaraciones ----
            if parts and parts[0] in RESERVED:
                tipo_decl = parts[0]   # \ent /ent etc
                ids = []
                for tok in parts[1:]:
                    if tok == ";":
                        break
                    if RE_IDENTIFICADOR.match(tok):
                        ids.append(tok)
                for nombre in ids:
                    if nombre in declarados:
                        self._add_error(ErrorType.SEMANTICO, idx, f"Duplicidad de declaración de '{nombre}'", lexema=nombre)
                    else:
                        declarados[nombre] = tipo_decl
                        self.tabla_simbolos[nombre] = {"tipo": tipo_decl, "valor": None}
                continue

            # ---- Asignaciones simples: <id> = <valor> ;
            if "=" in parts:
                try:
                    pos_eq = parts.index("=")
                except ValueError:
                    pos_eq = -1

                if pos_eq > 0:
                    lhs = parts[pos_eq - 1]
                    rhs = None
                    for tok in parts[pos_eq + 1:]:
                        if tok == ";":
                            break
                        if tok.strip() == "":
                            continue
                        rhs = tok
                        break

                    # LHS valido?
                    if not RE_IDENTIFICADOR.match(lhs):
                        self._add_error(ErrorType.SEMANTICO, idx, f"LHS inválido en asignación: '{lhs}'", lexema=lhs)
                    else:
                        # variable indefinida en lhs?
                        if lhs not in declarados:
                            self._add_error(ErrorType.SEMANTICO, idx, f"Variable indefinida '{lhs}' en asignación", lexema=lhs)

                        rhs_tipo = None
                        rhs_valor = None

                        if rhs is None:
                            self._add_error(ErrorType.SEMANTICO, idx, "RHS inexistente en asignación", lexema=lhs)
                        else:
                            if RE_ENTERO.match(rhs):
                                rhs_tipo = "/ent" if "/ent" in RESERVED else "\\ent"
                                rhs_valor = int(rhs)
                            elif RE_DECIMAL.match(rhs):
                                rhs_tipo = "/dec" if "/dec" in RESERVED else "\\dec"
                                rhs_valor = float(rhs)
                            elif RE_CADENA.match(rhs):
                                rhs_tipo = "/cad" if "/cad" in RESERVED else "\\cad"
                                rhs_valor = rhs[1:-1]
                            elif RE_IDENTIFICADOR.match(rhs):
                                if rhs not in declarados:
                                    self._add_error(ErrorType.SEMANTICO, idx, f"Variable indefinida '{rhs}' usada en asignación", lexema=rhs)
                                else:
                                    rhs_tipo = declarados[rhs]
                                    rhs_valor = None
                            else:
                                self._add_error(ErrorType.SEMANTICO, idx, f"RHS no reconocido '{rhs}'", lexema=rhs)

                        # Chequear compatibilidad si ambos tipos conocidos
                        if lhs in declarados and rhs_tipo is not None:
                            lhs_tipo = declarados[lhs]
                            # regla sencilla: exigir igualdad exacta
                            if lhs_tipo != rhs_tipo:
                                self._add_error(ErrorType.SEMANTICO, idx,
                                                f"Incompatibilidad de tipos: asignar {rhs_tipo} a {lhs_tipo} ('{lhs}')",
                                                lexema=lhs)
                            else:
                                # actualizar tabla de símbolos: si se asignó una constante, guardar valor
                                if rhs_valor is not None:
                                    self.tabla_simbolos.setdefault(lhs, {})["valor"] = rhs_valor
                                    self.tabla_simbolos.setdefault(lhs, {})["tipo"] = rhs_tipo
                                else:
                                    self.tabla_simbolos.setdefault(lhs, {})["tipo"] = rhs_tipo

            # ---- Manejo básico de prints -> simulación de salida ----
            # Detectamos: print("algo"); o print(mnmX);
            if parts and parts[0].lower() == "print":
                # buscar el primer token entre paréntesis o siguiente
                contenido = None
                # intentar obtener lo que sigue
                for tok in parts[1:]:
                    if tok == ";":
                        break
                    if tok == "(" or tok == ")":
                        continue
                    contenido = tok
                    break
                if contenido is not None:
                    # si contenido es cadena literal la agregamos; si es identificador y está declarado, añadimos marcador
                    if RE_CADENA.match(contenido):
                        salida_simulada.append(contenido[1:-1])
                    elif RE_IDENTIFICADOR.match(contenido):
                        if contenido in self.tabla_simbolos and self.tabla_simbolos[contenido].get("valor") is not None:
                            salida_simulada.append(str(self.tabla_simbolos[contenido]["valor"]))
                        else:
                            # si no tiene valor, indicar su nombre (simulación)
                            salida_simulada.append(f"<{contenido}>")
                    else:
                        salida_simulada.append(f"<{contenido}>")

        # ---------------- DEDUPLICADO ----------------
        # Errores: no repetir combinación (lexema, renglón)
        errores_unicos: List[Error] = []
        seen_lex_renglon = set()
        for e in self.errores:
            key = (e.lexema if e.lexema is not None else "", e.linea)
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

        # Asegurar que tabla_simbolos tenga la forma requerida
        tabla_final: Dict[str, Dict[str, Any]] = {}
        for nombre, info in self.tabla_simbolos.items():
            tabla_final[nombre] = {"tipo": info.get("tipo"), "valor": info.get("valor")}

        info_adicional = {
            "tabla_simbolos": tabla_final,
            "salida_ejecucion": salida_simulada
        }

        return self.errores, self.tokens, info_adicional

# ----------------- Funciones públicas para importar -----------------
_compilador_singleton = CompiladorMinimalista()

def analizar_codigo(codigo: str) -> Tuple[List[Error], List[Token], Dict[str, Any]]:
    """Función pública usada por gui.py"""
    return _compilador_singleton.analizar_codigo(codigo)

def obtener_tabla_simbolos(info_adicional: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Retorna la tabla de símbolos desde info_adicional (helper)"""
    return info_adicional.get("tabla_simbolos", {})

def obtener_salida_ejecucion(info_adicional: Dict[str, Any]) -> List[str]:
    """Retorna la salida de ejecución desde info_adicional (helper)"""
    return info_adicional.get("salida_ejecucion", [])

# ----------------- prueba rápida si se ejecuta directamente -----------------
if __name__ == "__main__":
    ejemplo = """/ent mnmX = 5
/dec mnmY = 2.5
/ent mnmZ = mnmX
/cad mnmSaludo = "Hola"
mnmA = 1
print("Hola mundo");
print(mnmX);
"""
    errs, toks, info = analizar_codigo(ejemplo)
    print("ERRORES:")
    for e in errs:
        print(f"{e.token} | {e.tipo.value} | L{e.linea} | {e.mensaje} | lexema={e.lexema}")
    print("\nTOKENS (muestra):")
    for t in toks[:40]:
        print(t)
    print("\nTABLA SIMBOLOS:")
    for k,v in info["tabla_simbolos"].items():
        print(k, v)
    print("\nSALIDA:")
    print(info["salida_ejecucion"])
