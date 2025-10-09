# error_handler.py - Gestión de errores del compilador
from typing import List, Optional
from models import Error, ErrorType


class ErrorHandler:
    """Maneja el registro y deduplicación de errores"""
    
    def __init__(self):
        self.errores: List[Error] = []
        self._err_counter = 0
    
    def reset(self):
        """Reinicia el manejador de errores"""
        self.errores = []
        self._err_counter = 0
    
    def _new_err_token(self) -> str:
        """Genera un nuevo identificador de error"""
        name = "err" if self._err_counter == 0 else f"err{self._err_counter}"
        self._err_counter += 1
        return name
    
    def add_error(self, tipo: ErrorType, linea: int, mensaje: str, 
                  lexema: Optional[str] = None):
        """Agrega un nuevo error"""
        tok = self._new_err_token()
        self.errores.append(
            Error(token=tok, tipo=tipo, linea=linea, mensaje=mensaje, lexema=lexema)
        )
    
    def deduplicate_errors(self) -> List[Error]:
        """Elimina errores duplicados y retorna la lista limpia"""
        errores_unicos: List[Error] = []
        seen = set()
        
        for e in self.errores:
            key = (e.lexema if e.lexema is not None else "", e.linea, e.mensaje)
            if key in seen:
                continue
            seen.add(key)
            errores_unicos.append(e)
        
        self.errores = errores_unicos
        return self.errores
    
    def get_errors(self) -> List[Error]:
        """Retorna todos los errores registrados"""
        return self.errores
    
    def has_errors(self) -> bool:
        """Verifica si hay errores"""
        return len(self.errores) > 0