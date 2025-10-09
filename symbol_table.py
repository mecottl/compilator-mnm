# symbol_table.py - Tabla de símbolos del compilador
from typing import Dict, Any, Optional
from constants import RE_IDENTIFICADOR, RE_ENTERO, RE_DECIMAL, RE_CADENA, KEYWORDS, VALID_DECL_FORMS, INVALID_DECL_FORMS


class SymbolTable:
    """Tabla de símbolos para almacenar variables y sus tipos"""
    
    def __init__(self):
        self.tabla: Dict[str, Dict[str, Any]] = {}
        self.declarados: Dict[str, str] = {}  # nombre -> tipo ('/ent', '/dec', '/cad')
    
    def reset(self):
        """Reinicia la tabla de símbolos"""
        self.tabla = {}
        self.declarados = {}
    
    def registrar(self, lexema: str, tipo: str, valor: Optional[Any] = None):
        """
        Registra un símbolo en la tabla
        
        Args:
            lexema: Nombre del símbolo
            tipo: Tipo del símbolo
            valor: Valor inicial (opcional)
        """
        if lexema in self.tabla:
            # Actualizar símbolo existente
            if valor is not None:
                self.tabla[lexema]["valor"] = valor
            if not self.tabla[lexema].get("tipo") and tipo:
                self.tabla[lexema]["tipo"] = tipo
        else:
            # Crear nuevo símbolo
            self.tabla[lexema] = {"tipo": tipo, "valor": valor}
    
    def declarar_variable(self, nombre: str, tipo: str):
        """
        Declara una variable con su tipo
        
        Args:
            nombre: Nombre de la variable
            tipo: Tipo de la variable ('/ent', '/dec', '/cad')
        """
        self.declarados[nombre] = tipo
        self.registrar(nombre, tipo, None)
    
    def esta_declarada(self, nombre: str) -> bool:
        """Verifica si una variable está declarada"""
        return nombre in self.declarados
    
    def obtener_tipo(self, nombre: str) -> Optional[str]:
        """Obtiene el tipo de una variable declarada"""
        return self.declarados.get(nombre)
    
    def actualizar_valor(self, nombre: str, valor: Any):
        """Actualiza el valor de una variable"""
        if nombre in self.tabla:
            self.tabla[nombre]["valor"] = valor
    
    def obtener_valor(self, nombre: str) -> Optional[Any]:
        """Obtiene el valor de una variable"""
        if nombre in self.tabla:
            return self.tabla[nombre].get("valor")
        return None
    
    def get_tabla_final(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna la tabla de símbolos filtrada y ordenada
        """
        tabla_final: Dict[str, Dict[str, Any]] = {}
        
        for nombre, info in self.tabla.items():
            # Filtrar solo elementos relevantes
            if (RE_IDENTIFICADOR.match(nombre) or
                RE_ENTERO.match(nombre) or
                RE_DECIMAL.match(nombre) or
                RE_CADENA.match(nombre) or
                info.get("tipo") in ("SIMBOLO", "PALABRA_RESERVADA", "IDENTIFICADOR", "")):
                tabla_final[nombre] = {
                    "tipo": info.get("tipo"),
                    "valor": info.get("valor")
                }
            else:
                # Incluir palabras clave y declaraciones
                if (nombre.lower() in KEYWORDS or 
                    nombre in VALID_DECL_FORMS or 
                    nombre in INVALID_DECL_FORMS):
                    tabla_final[nombre] = {
                        "tipo": info.get("tipo"),
                        "valor": info.get("valor")
                    }
        
        # Ordenar alfabéticamente
        return dict(sorted(tabla_final.items(), key=lambda kv: kv[0]))
    
    def get_declarados(self) -> Dict[str, str]:
        """Retorna el diccionario de variables declaradas"""
        return self.declarados