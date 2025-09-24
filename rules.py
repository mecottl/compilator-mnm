# rules.py - Lógica del Compilador/Intérprete Minimalista
"""
Este módulo contiene toda la lógica del compilador minimalista, incluyendo:
- Análisis léxico y sintáctico
- Tabla de símbolos
- Validación de tipos
- Ejecución de bucles for y print
- Detección de errores específicos
"""

import re
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum

# ================================
# TIPOS Y ENUMERACIONES
# ================================

class TipoDato(Enum):
    """Tipos de datos permitidos en el lenguaje"""
    ENTERO = "entero"
    DECIMAL = "decimal"
    CADENA = "cadena"

class TipoError(Enum):
    """Tipos de errores posibles"""
    DECLARACION_DUPLICADA = "DECLARACION_DUPLICADA"
    VARIABLE_INDEFINIDA = "VARIABLE_INDEFINIDA"
    INCOMPATIBILIDAD_TIPOS = "INCOMPATIBILIDAD_TIPOS"
    SINTAXIS_INVALIDA = "SINTAXIS_INVALIDA"

# ================================
# CLASES DE DATOS
# ================================

class Error:
    """Representa un error encontrado durante el análisis"""
    def __init__(self, linea: int, tipo: TipoError, mensaje: str, token: str = ""):
        self.linea = linea
        self.tipo = tipo
        self.mensaje = mensaje
        self.token = token

class Token:
    """Representa un token del análisis léxico"""
    def __init__(self, lexema: str, tipo: str, linea: int, descripcion: str = ""):
        self.lexema = lexema
        self.tipo = tipo
        self.linea = linea
        self.descripcion = descripcion

class Simbolo:
    """Representa una entrada en la tabla de símbolos"""
    def __init__(self, nombre: str, tipo: TipoDato, valor: Any):
        self.nombre = nombre
        self.tipo = tipo
        self.valor = valor

# ================================
# COMPILADOR PRINCIPAL
# ================================

class CompiladorMinimalista:
    """Clase principal del compilador/intérprete"""
    
    def __init__(self):
        self.symbol_table: Dict[str, Simbolo] = {}
        self.errores: List[Error] = []
        self.tokens: List[Token] = []
        self.lineas_codigo: List[str] = []
        self.salida_ejecucion: List[str] = []
        
        # Patrones regex para análisis léxico
        self.patron_variable = re.compile(r'^mnm[A-Za-z0-9]+$')
        self.patron_declaracion = re.compile(r'^/(ent|dec|cad)\s+(mnm[A-Za-z0-9]+)\s*=\s*(.+)$')
        self.patron_for = re.compile(r'^for\s+(mnm[A-Za-z0-9]+)\s+in\s+range\((.+)\):$')
        self.patron_print = re.compile(r'^print\("(.+)"\);$')
        self.patron_entero = re.compile(r'^-?\d+$')
        self.patron_decimal = re.compile(r'^-?\d+\.\d+$')
        self.patron_cadena = re.compile(r'^".*"$')
        self.patron_operacion = re.compile(r'^(.+)\s*([+\-*/])\s*(.+)$')

    def limpiar_estado(self):
        """Limpia el estado del compilador para un nuevo análisis"""
        self.symbol_table.clear()
        self.errores.clear()
        self.tokens.clear()
        self.lineas_codigo.clear()
        self.salida_ejecucion.clear()

    def analizar_codigo(self, codigo: str) -> Tuple[List[Error], List[Token]]:
        """
        Función principal que analiza todo el código
        
        Args:
            codigo (str): Código fuente a analizar
            
        Returns:
            Tuple[List[Error], List[Token]]: Lista de errores y tokens encontrados
        """
        self.limpiar_estado()
        
        # Dividir código en líneas y limpiar espacios
        self.lineas_codigo = [linea.strip() for linea in codigo.split('\n') if linea.strip()]
        
        # Analizar cada línea
        nivel_indentacion = 0
        dentro_for = False
        instrucciones_for = []
        
        for i, linea in enumerate(self.lineas_codigo, 1):
            # Detectar indentación para manejo de for
            indentacion_actual = len(linea) - len(linea.lstrip())
            
            if indentacion_actual > 0 and not dentro_for:
                self.errores.append(Error(i, TipoError.SINTAXIS_INVALIDA, 
                                        "Indentación sin estructura de control", linea))
                continue
            
            if indentacion_actual == 0 and dentro_for:
                # Fin del bloque for, ejecutar instrucciones acumuladas
                self._ejecutar_for(instrucciones_for)
                dentro_for = False
                instrucciones_for = []
            
            if indentacion_actual > 0 and dentro_for:
                # Instrucción dentro del for
                instrucciones_for.append((i, linea.strip()))
                continue
                
            # Analizar línea según su tipo
            if self.patron_for.match(linea):
                dentro_for = True
                self._analizar_for(linea, i)
            elif self.patron_declaracion.match(linea):
                self._analizar_declaracion(linea, i)
            elif self.patron_print.match(linea):
                self._analizar_print(linea, i)
            elif linea:  # Línea no vacía que no coincide con patrones conocidos
                self.errores.append(Error(i, TipoError.SINTAXIS_INVALIDA, 
                                        "Sintaxis no reconocida", linea))
        
        # Si terminamos dentro de un for, ejecutar las instrucciones pendientes
        if dentro_for:
            self._ejecutar_for(instrucciones_for)
        
        return self.errores, self.tokens

    def _analizar_declaracion(self, linea: str, num_linea: int):
        """Analiza una línea de declaración de variable"""
        match = self.patron_declaracion.match(linea)
        if not match:
            self.errores.append(Error(num_linea, TipoError.SINTAXIS_INVALIDA, 
                                    "Formato de declaración inválido", linea))
            return
        
        tipo_str, nombre_var, expresion = match.groups()
        
        # Agregar tokens
        self.tokens.append(Token(f"/{tipo_str}", "TIPO", num_linea, "Tipo de dato"))
        self.tokens.append(Token(nombre_var, "VARIABLE", num_linea, "Identificador de variable"))
        self.tokens.append(Token("=", "ASIGNACION", num_linea, "Operador de asignación"))
        
        # Validar nombre de variable
        if not self.patron_variable.match(nombre_var):
            self.errores.append(Error(num_linea, TipoError.SINTAXIS_INVALIDA, 
                                    "Nombre de variable inválido", nombre_var))
            return
        
        # Verificar si la variable ya existe
        if nombre_var in self.symbol_table:
            self.errores.append(Error(num_linea, TipoError.DECLARACION_DUPLICADA, 
                                    f"La variable '{nombre_var}' ya está declarada", nombre_var))
            return
        
        # Mapear tipos
        tipo_mapa = {
            'ent': TipoDato.ENTERO,
            'dec': TipoDato.DECIMAL,
            'cad': TipoDato.CADENA
        }
        tipo = tipo_mapa[tipo_str]
        
        # Evaluar la expresión del lado derecho
        valor, tipo_resultado = self._evaluar_expresion(expresion, num_linea)
        
        if valor is None:
            return  # Error ya registrado en _evaluar_expresion
        
        # Verificar compatibilidad de tipos
        if tipo != tipo_resultado:
            self.errores.append(Error(num_linea, TipoError.INCOMPATIBILIDAD_TIPOS, 
                                    f"No se puede asignar {tipo_resultado.value} a {tipo.value}", 
                                    expresion))
            return
        
        # Agregar variable a la tabla de símbolos
        self.symbol_table[nombre_var] = Simbolo(nombre_var, tipo, valor)
        
        # Agregar token de valor
        self.tokens.append(Token(str(valor), tipo_resultado.value.upper(), num_linea, 
                                "Valor asignado"))

    def _evaluar_expresion(self, expresion: str, num_linea: int) -> Tuple[Any, Optional[TipoDato]]:
        """
        Evalúa una expresión y retorna su valor y tipo
        
        Args:
            expresion (str): Expresión a evaluar
            num_linea (int): Número de línea para errores
            
        Returns:
            Tuple[Any, Optional[TipoDato]]: Valor y tipo de la expresión
        """
        expresion = expresion.strip()
        
        # Verificar si es un literal
        if self.patron_entero.match(expresion):
            return int(expresion), TipoDato.ENTERO
        elif self.patron_decimal.match(expresion):
            return float(expresion), TipoDato.DECIMAL
        elif self.patron_cadena.match(expresion):
            return expresion[1:-1], TipoDato.CADENA  # Remover comillas
        
        # Verificar si es una variable
        elif self.patron_variable.match(expresion):
            if expresion not in self.symbol_table:
                self.errores.append(Error(num_linea, TipoError.VARIABLE_INDEFINIDA, 
                                        f"Variable '{expresion}' no está definida", expresion))
                return None, None
            
            simbolo = self.symbol_table[expresion]
            return simbolo.valor, simbolo.tipo
        
        # Verificar si es una operación aritmética
        match_op = self.patron_operacion.match(expresion)
        if match_op:
            return self._evaluar_operacion(match_op.groups(), num_linea)
        
        # Expresión no reconocida
        self.errores.append(Error(num_linea, TipoError.SINTAXIS_INVALIDA, 
                                "Expresión no reconocida", expresion))
        return None, None

    def _evaluar_operacion(self, grupos: Tuple[str, str, str], num_linea: int) -> Tuple[Any, Optional[TipoDato]]:
        """
        Evalúa una operación aritmética
        
        Args:
            grupos (Tuple[str, str, str]): Operando1, operador, operando2
            num_linea (int): Número de línea para errores
            
        Returns:
            Tuple[Any, Optional[TipoDato]]: Resultado y tipo de la operación
        """
        operando1_str, operador, operando2_str = grupos
        
        # Evaluar operandos
        valor1, tipo1 = self._evaluar_expresion(operando1_str, num_linea)
        valor2, tipo2 = self._evaluar_expresion(operando2_str, num_linea)
        
        if valor1 is None or valor2 is None:
            return None, None
        
        # Verificar compatibilidad de tipos
        if tipo1 != tipo2:
            self.errores.append(Error(num_linea, TipoError.INCOMPATIBILIDAD_TIPOS, 
                                    f"No se puede operar {tipo1.value} con {tipo2.value}", 
                                    f"{operando1_str} {operador} {operando2_str}"))
            return None, None
        
        # Agregar tokens de la operación
        self.tokens.append(Token(operador, "OPERADOR", num_linea, "Operador aritmético"))
        
        # Realizar operación según el tipo
        try:
            if tipo1 == TipoDato.CADENA:
                if operador == '+':
                    return valor1 + valor2, TipoDato.CADENA
                else:
                    self.errores.append(Error(num_linea, TipoError.SINTAXIS_INVALIDA, 
                                            f"Operador '{operador}' no válido para cadenas", operador))
                    return None, None
            
            elif tipo1 in [TipoDato.ENTERO, TipoDato.DECIMAL]:
                if operador == '+':
                    resultado = valor1 + valor2
                elif operador == '-':
                    resultado = valor1 - valor2
                elif operador == '*':
                    resultado = valor1 * valor2
                elif operador == '/':
                    if valor2 == 0:
                        self.errores.append(Error(num_linea, TipoError.SINTAXIS_INVALIDA, 
                                                "División por cero", f"{valor1} / {valor2}"))
                        return None, None
                    resultado = valor1 / valor2
                    # Si era división entre enteros, convertir a decimal
                    if tipo1 == TipoDato.ENTERO:
                        return float(resultado), TipoDato.DECIMAL
                else:
                    self.errores.append(Error(num_linea, TipoError.SINTAXIS_INVALIDA, 
                                            f"Operador '{operador}' no reconocido", operador))
                    return None, None
                
                return resultado, tipo1
        
        except Exception as e:
            self.errores.append(Error(num_linea, TipoError.SINTAXIS_INVALIDA, 
                                    f"Error en operación: {str(e)}", 
                                    f"{valor1} {operador} {valor2}"))
            return None, None
        
        return None, None

    def _analizar_for(self, linea: str, num_linea: int):
        """Analiza una declaración de bucle for"""
        match = self.patron_for.match(linea)
        if not match:
            self.errores.append(Error(num_linea, TipoError.SINTAXIS_INVALIDA, 
                                    "Formato de for inválido", linea))
            return
        
        var_bucle, rango_expr = match.groups()
        
        # Agregar tokens
        self.tokens.append(Token("for", "FOR", num_linea, "Palabra clave for"))
        self.tokens.append(Token(var_bucle, "VARIABLE", num_linea, "Variable de bucle"))
        self.tokens.append(Token("in", "IN", num_linea, "Palabra clave in"))
        self.tokens.append(Token("range", "RANGE", num_linea, "Función range"))
        
        # Validar nombre de variable de bucle
        if not self.patron_variable.match(var_bucle):
            self.errores.append(Error(num_linea, TipoError.SINTAXIS_INVALIDA, 
                                    "Nombre de variable de bucle inválido", var_bucle))
            return
        
        # Evaluar expresión del rango
        valor_rango, tipo_rango = self._evaluar_expresion(rango_expr, num_linea)
        
        if valor_rango is None:
            return
        
        # El rango debe ser un entero
        if tipo_rango != TipoDato.ENTERO:
            self.errores.append(Error(num_linea, TipoError.INCOMPATIBILIDAD_TIPOS, 
                                    f"El rango debe ser entero, no {tipo_rango.value}", rango_expr))
            return
        
        if valor_rango < 0:
            self.errores.append(Error(num_linea, TipoError.SINTAXIS_INVALIDA, 
                                    "El rango no puede ser negativo", str(valor_rango)))
            return
        
        # Guardar información del for para ejecución posterior
        self.symbol_table[f"__FOR__{var_bucle}"] = Simbolo(var_bucle, TipoDato.ENTERO, valor_rango)

    def _analizar_print(self, linea: str, num_linea: int):
        """Analiza una instrucción print"""
        match = self.patron_print.match(linea)
        if not match:
            self.errores.append(Error(num_linea, TipoError.SINTAXIS_INVALIDA, 
                                    "Formato de print inválido", linea))
            return
        
        contenido = match.group(1)
        
        # Agregar tokens
        self.tokens.append(Token("print", "PRINT", num_linea, "Función print"))
        self.tokens.append(Token(f'"{contenido}"', "CADENA", num_linea, "Contenido a imprimir"))
        
        # Verificar si el contenido es una variable
        if self.patron_variable.match(contenido):
            if contenido not in self.symbol_table:
                self.errores.append(Error(num_linea, TipoError.VARIABLE_INDEFINIDA, 
                                        f"Variable '{contenido}' no está definida", contenido))
                return

    def _ejecutar_for(self, instrucciones: List[Tuple[int, str]]):
        """Ejecuta un bucle for con sus instrucciones"""
        if not instrucciones:
            return
        
        # Encontrar la variable de bucle y su rango
        var_bucle = None
        rango = None
        
        for nombre, simbolo in self.symbol_table.items():
            if nombre.startswith("__FOR__"):
                var_bucle = nombre.replace("__FOR__", "")
                rango = simbolo.valor
                break
        
        if var_bucle is None or rango is None:
            return
        
        # Ejecutar el bucle
        for i in range(rango):
            # Crear/actualizar variable de bucle
            self.symbol_table[var_bucle] = Simbolo(var_bucle, TipoDato.ENTERO, i)
            
            # Ejecutar cada instrucción del bucle
            for num_linea, instruccion in instrucciones:
                self._ejecutar_instruccion(instruccion, num_linea)
        
        # Limpiar variable temporal del for
        for nombre in list(self.symbol_table.keys()):
            if nombre.startswith("__FOR__"):
                del self.symbol_table[nombre]

    def _ejecutar_instruccion(self, instruccion: str, num_linea: int):
        """Ejecuta una instrucción individual"""
        # Solo ejecutar print por ahora
        match = self.patron_print.match(instruccion)
        if match:
            contenido = match.group(1)
            
            # Si es una variable, obtener su valor
            if self.patron_variable.match(contenido):
                if contenido in self.symbol_table:
                    valor = self.symbol_table[contenido].valor
                    self.salida_ejecucion.append(str(valor))
                else:
                    self.salida_ejecucion.append(f"ERROR: Variable {contenido} no definida")
            else:
                # Es un literal de cadena
                self.salida_ejecucion.append(contenido)

    def obtener_tabla_simbolos(self) -> Dict[str, Dict[str, Any]]:
        """Retorna la tabla de símbolos en formato dict"""
        return {
            nombre: {
                "tipo": simbolo.tipo.value,
                "valor": simbolo.valor
            }
            for nombre, simbolo in self.symbol_table.items()
            if not nombre.startswith("__")  # Excluir variables internas
        }

    def obtener_salida_ejecucion(self) -> List[str]:
        """Retorna la salida de la ejecución"""
        return self.salida_ejecucion.copy()

# ================================
# FUNCIÓN PRINCIPAL DE ANÁLISIS
# ================================

# Instancia global del compilador
compilador = CompiladorMinimalista()

def analizar_codigo(codigo: str) -> Tuple[List[Error], List[Token], Dict[str, Any]]:
    """
    Función principal para analizar código desde la GUI
    
    Args:
        codigo (str): Código fuente a analizar
        
    Returns:
        Tuple: (errores, tokens, información adicional)
    """
    errores, tokens = compilador.analizar_codigo(codigo)
    
    info_adicional = {
        "tabla_simbolos": compilador.obtener_tabla_simbolos(),
        "salida_ejecucion": compilador.obtener_salida_ejecucion(),
        "total_errores": len(errores),
        "total_tokens": len(tokens)
    }
    
    return errores, tokens, info_adicional

def obtener_tabla_simbolos() -> Dict[str, Dict[str, Any]]:
    """Retorna la tabla de símbolos actual"""
    return compilador.obtener_tabla_simbolos()

def obtener_salida_ejecucion() -> List[str]:
    """Retorna la salida de ejecución actual"""
    return compilador.obtener_salida_ejecucion()