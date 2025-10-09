# models.py - Clases de datos del compilador
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ErrorType(Enum):
    """Tipos de errores del compilador"""
    SEMANTICO = "SEMÁNTICO"
    LEXICO = "LÉXICO"
    SINTACTICO = "SINTÁCTICO"
    OTRO = "OTRO"


@dataclass
class Token:
    """Representa un token del código fuente"""
    lexema: str
    tipo: str
    linea: int
    descripcion: str = ""


@dataclass
class Error:
    """Representa un error encontrado durante la compilación"""
    token: str
    tipo: ErrorType
    linea: int
    mensaje: str
    lexema: Optional[str] = None