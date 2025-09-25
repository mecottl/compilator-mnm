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

# Aceptamos formas \ent y /ent, etc.
RESERVED_DECL = {"\\ent", "/ent", "\\dec", "/dec", "\\cad", "/cad"}

# Palabras clave adicionales que quieres ver en la tabla
KEYWORDS = {"print", "for", "in", "range"}

# Patrón para tokenizar: cadenas, palabras reservadas (\ent /ent ...), ids, números, operadores/símbolos, palabras
TOKEN_PATTERN = re.compile(
    r'(".*?")|([\\/][A-Za-z]+)|([A-Za-z_][A-Za-z0-9_]*)|(\d+\.\d+|\d+)|([=;,+\-/*()\[\]{}:])'
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

# ----------------- Compilador -----------------
class CompiladorMinimalista:
    def __init__(self):
        self.tokens: List[Token] = []
        self.errores: List[Error] = []
        # tabla_simbolos: lexema -> {"tipo": <string>, "valor": <val o None>}
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

        declarados: Dict[str, str] = {}  # nombre -> tipo declarado (p. ej. "/ent")
        salida_simulada: List[str] = []

        # Helper: asegurar inserción en tabla_simbolos sin duplicados
        def registrar_en_tabla(lex: str, tipo: str, valor: Optional[Any] = None):
            # Si ya existe, no sobrescribir tipo/valor salvo que se pase valor no None (actualizar)
            if lex in self.tabla_simbolos:
                # Si nos pasan valor, lo actualizamos
                if valor is not None:
                    self.tabla_simbolos[lex]["valor"] = valor
                # si tipo está vacío y antes no lo estaba, preferimos mantener existente
                if not self.tabla_simbolos[lex].get("tipo") and tipo:
                    self.tabla_simbolos[lex]["tipo"] = tipo
            else:
                self.tabla_simbolos[lex] = {"tipo": tipo, "valor": valor}

        lineas = codigo.splitlines()
        for idx, linea in enumerate(lineas, start=1):
            texto = linea.strip()
            if texto == "":
                continue

            # tokenizar todo (incluye operadores, paréntesis, palabras, números y cadenas)
            parts = [m.group(0) for m in TOKEN_PATTERN.finditer(texto)]

            # Añadir tokens para la vista raw
            for p in parts:
                tipo_token = "OTRO"
                p_lower = p.lower()
                if p in RESERVED_DECL:
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

                # Registrar en tabla_simbolos según tipo pedido por ti:
                # - siempre registrar operadores/símbolos como SIMBOLO
                # - registrar palabras reservadas (declaraciones y keywords) como PALABRA_RESERVADA
                # - registrar constantes literales con su tipo y valor
                # - identificadores se registran cuando se declaran o se asignan (más abajo)
                if tipo_token == "SIMBOLO":
                    registrar_en_tabla(p, "SIMBOLO", None)
                elif tipo_token == "PALABRA_RESERVADA":
                    # normalizar la forma que mostramos en tabla: usar la misma cadena p
                    registrar_en_tabla(p, "PALABRA_RESERVADA", None)
                elif tipo_token == "CONSTANTE_ENTERA":
                    registrar_en_tabla(p, "/ent", int(p))
                elif tipo_token == "CONSTANTE_DECIMAL":
                    registrar_en_tabla(p, "/dec", float(p))
                elif tipo_token == "CONSTANTE_CADENA":
                    registrar_en_tabla(p, "/cad", p[1:-1])
                # no registrar IDENTIFICADOR aquí por aparición casual (evitar "ensuciar" la tabla)
                # los IDENTIFICADOR se registran al declararse o asignarse

            # ---------------- Declaraciones (\ent /ent /dec /cad) ----------------
            if parts and parts[0] in RESERVED_DECL:
                tipo_decl = parts[0]
                ids: List[str] = []
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
                        # registrar el identificador y la palabra reservada en tabla_simbolos
                        registrar_en_tabla(parts[0], "PALABRA_RESERVADA", None)
                        registrar_en_tabla(nombre, tipo_decl, None)
                continue

            # ---------------- Asignaciones simples: <id> = <valor> ; ----------------
            if "=" in parts:
                # tomamos la primera '='
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

                    # registrar el símbolo '=' en tabla
                    registrar_en_tabla("=", "SIMBOLO", None)

                    # validar LHS
                    if lhs is None or not RE_IDENTIFICADOR.match(lhs):
                        self._add_error(ErrorType.SEMANTICO, idx, f"LHS inválido en asignación: '{lhs}'", lexema=str(lhs))
                    else:
                        # si lhs no declarado, marcar error y aun así registrarlo en tabla (según tu petición)
                        if lhs not in declarados:
                            self._add_error(ErrorType.SEMANTICO, idx, f"Variable indefinida '{lhs}' en asignación", lexema=lhs)
                            # registrar identificador aunque no declarado (el GUI pedía ver identificadores)
                            registrar_en_tabla(lhs, "IDENTIFICADOR", None)
                        else:
                            registrar_en_tabla(lhs, declarados[lhs], None)

                        rhs_tipo = None
                        rhs_valor: Optional[Any] = None

                        if rhs is None:
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
                                    self._add_error(ErrorType.SEMANTICO, idx, f"Variable indefinida '{rhs}' usada en asignación", lexema=rhs)
                                    # registrar rhs en tabla como identificador sin tipo
                                    registrar_en_tabla(rhs, "IDENTIFICADOR", None)
                                else:
                                    rhs_tipo = declarados[rhs]
                            else:
                                self._add_error(ErrorType.SEMANTICO, idx, f"RHS no reconocido '{rhs}'", lexema=str(rhs))

                        # compatibilidad de tipos (si tenemos información)
                        if lhs in declarados and rhs_tipo is not None:
                            lhs_tipo = declarados[lhs]
                            if lhs_tipo != rhs_tipo:
                                self._add_error(ErrorType.SEMANTICO, idx,
                                                f"Incompatibilidad de tipos: asignar {rhs_tipo} a {lhs_tipo} ('{lhs}')",
                                                lexema=lhs)
                            else:
                                # si RHS es constante, actualizar valor en tabla
                                if rhs_valor is not None:
                                    registrar_en_tabla(lhs, lhs_tipo, rhs_valor)

            # ---------------- imprimir / otros: detectar 'print' y keywords ----------------
            # Si en la línea aparece 'print' u otras keywords, registrarlas en tabla
            for tok in parts:
                if isinstance(tok, str):
                    tl = tok.lower()
                    if tl in KEYWORDS:
                        registrar_en_tabla(tok, "PALABRA_RESERVADA", None)

                # ya tokenizamos constantes y símbolos más arriba

        # ------------------- DEDUPLICADO FINAL -------------------
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

        # Filtrar y formatear tabla_simbolos final: ya está en dict (claves únicas).
        # Sin embargo, por seguridad, mantenemos solo lexemas útiles (identificadores, constantes, símbolos, keywords, palabras reservadas)
        tabla_final: Dict[str, Dict[str, Any]] = {}
        for nombre, info in self.tabla_simbolos.items():
            if (RE_IDENTIFICADOR.match(nombre)
                    or RE_ENTERO.match(nombre)
                    or RE_DECIMAL.match(nombre)
                    or RE_CADENA.match(nombre)
                    or info.get("tipo") in ("SIMBOLO", "PALABRA_RESERVADA", "IDENTIFICADOR")):
                tabla_final[nombre] = {"tipo": info.get("tipo"), "valor": info.get("valor")}
            else:
                # para seguridad, si el lexema es una palabra clave en KEYWORDS o una reserved decl, lo incluimos
                if nombre.lower() in KEYWORDS or nombre in RESERVED_DECL:
                    tabla_final[nombre] = {"tipo": info.get("tipo"), "valor": info.get("valor")}
                # de otro modo se descarta (raro)

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
    ejemplo = """/ent mnmX = 5;
    /dec mnmY = 2.5;
    /ent mnmZ = mnmX;
    /cad mnmSaludo = "Hola mundo";
    print(mnmSaludo);
    for mnmI in range(mnmX):
        print(mnmI);
    """
    errs, toks, info = analizar_codigo(ejemplo)
    print("ERRORES:")
    for e in errs:
        print(f"{e.token} | {e.tipo.value} | L{e.linea} | {e.mensaje} | lexema={e.lexema}")
    print("\nTOKENS (muestra):")
    for t in toks[:80]:
        print(t)
    print("\nTABLA SIMBOLOS:")
    for k,v in info["tabla_simbolos"].items():
        print(k, v)
    print("\nSALIDA:")
    print(info["salida_ejecucion"])
