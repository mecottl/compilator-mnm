# optimizer/optimizer.py
# Módulo para aplicar optimizaciones a la lista de triplos.

from typing import List, Tuple, Dict, Any

class Optimizer:
    """
    Toma una lista de triplos y aplica varias técnicas de
    optimización, como la Eliminación de Subexpresiones Comunes (CSE).
    """
    
    def __init__(self, triplos: List[Tuple]):
        # Esta es la lista "sucia" (SIN resolver) que viene del generador
        self.original_triplos = triplos
        self.optimized_triplos = []
        
        # --- Cachés para la optimización ---
        
        # 1. expressions: Mapea una expresión a un resultado.
        #    Ej: { ('+', 'T1', 'T2'): 'T3' }
        #    Significa: "El resultado de T1+T2 está en T3"
        self.expressions = {}

        # 2. aliases: Mapea una variable al temporal que tiene su valor.
        #    Ej: { 'mnmC': 'T3' }
        #    Significa: "El valor de mnmC es el que está en T3"
        self.aliases = {}
    
    def _clear_cache(self):
        """
        Limpia los cachés. Se llama al encontrar un salto o etiqueta.
        Esto finaliza el "bloque básico" y previene
        optimizaciones incorrectas.
        """
        self.expressions.clear()
        self.aliases.clear()

    def optimize(self) -> List[Tuple]:
        """
        Punto de entrada principal.
        Recorre la lista de triplos y aplica CSE.
        """
        self.optimized_triplos = []
        self._clear_cache()
        
        # --- Lógica de Optimización (CSE) ---
        
        # Usamos un iterador para poder "espiar" el siguiente triplo
        i = 0
        while i < len(self.original_triplos):
            current_triplo = self.original_triplos[i]
            op, arg1, arg2 = current_triplo
            
            # 1. Manejo de Saltos y Etiquetas (Fin de Bloque Básico)
            if op in ("JMP", "True", "False", "LABEL", "LABEL_END_LOOP"):
                self.optimized_triplos.append(current_triplo)
                self._clear_cache() # ¡INVALIDAR TODO!
                i += 1
                continue

            # 2. Manejo de Cálculos (ej: +, *, <)
            if op not in ("="):
                # Es un cálculo como (+, T1, mnmB)
                
                # Resolvemos los alias: si arg1 es 'mnmC', usar 'T3' (su valor real)
                val1 = self.aliases.get(arg1, arg1)
                val2 = self.aliases.get(arg2, arg2)
                expr = (op, val1, val2)
                
                if expr in self.expressions:
                    # --- ¡OPTIMIZACIÓN ENCONTRADA! ---
                    # El cálculo (op, val1, val2) ya se hizo y está en un temporal.
                    
                    # 1. Obtener el temporal (ej: T3) donde está el resultado
                    existing_result_temp = self.expressions[expr]
                    
                    # 2. El triplo actual es (op, T_actual, ...).
                    #    Queremos que T_actual sea un alias del resultado existente.
                    current_result_temp = arg1 # (En nuestro formato, ej: (+, T4, ...))
                    self.aliases[current_result_temp] = existing_result_temp
                    
                    # 3. NO añadimos el triplo actual (ej: (+, T4, ...))
                    #    porque es redundante.
                    i += 1 # Saltar este triplo
                
                else:
                    # --- Expresión Nueva ---
                    # 1. Guardamos esta expresión en el caché
                    #    ej: expressions[('+', 'mnmA', 'mnmB')] = 'T1'
                    self.expressions[expr] = arg1
                    self.optimized_triplos.append(current_triplo)
                    i += 1

            # 3. Manejo de Asignaciones (ej: =)
            elif op == "=":
   
                for (e_op, e_arg1, e_arg2), res in list(self.expressions.items()):
                    if e_arg1 == arg1 or e_arg2 == arg1:
                        del self.expressions[(e_op, e_arg1, e_arg2)]
                        
                # También eliminamos el alias anterior de 'mnmC'
                if arg1 in self.aliases:
                    del self.aliases[arg1]

                val2 = self.aliases.get(arg2, arg2)
                self.aliases[arg1] = val2
                
                self.optimized_triplos.append(current_triplo)
                i += 1
                
            else:
                # Otro tipo de triplo (ej: '...')
                self.optimized_triplos.append(current_triplo)
                i += 1

        return self.optimized_triplos