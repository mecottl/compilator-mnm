# ensamblador/assembler_generator.py
# Generador de Ensamblador con limpieza de registros y optimización de guardado.

class AssemblerGenerator:
    def __init__(self):
        self.lines = []
        self.jump_targets = set()
        self.last_compare_op = None
        self.is_16bit = False 

    def generate(self, triplos: list) -> str:
        self.lines = []
        self.jump_targets = set()
        self.last_compare_op = None
        self.is_16bit = False
        
        # 1. Identificar etiquetas
        for op, arg1, arg2 in triplos:
            if op == "JMP" or (op == "" and arg1 in ["True", "False"]):
                target = arg2 if arg1 in ["True", "False"] else arg1
                try:
                    if str(target).isdigit():
                         self.jump_targets.add(int(target))
                except:
                    pass

        # 2. Generar instrucciones
        skip_counter = 0 # Para saltar múltiples instrucciones si optimizamos
        
        for i, (op, arg1, arg2) in enumerate(triplos):
            if skip_counter > 0:
                skip_counter -= 1
                continue

            # Insertar etiqueta
            line_num = i + 1
            if line_num in self.jump_targets:
                self.lines.append(f"Et{line_num}:")
            
            # --- LOOKAHEAD INTELIGENTE ---
            # Patrón: Carga de Constante (8) -> Operación Inversa (+) -> Asignación (mnmW)
            # Triplos: 
            #   i   : = T2 8
            #   i+1 : + T2 T1
            #   i+2 : = mnmW T2
            if op == "=" and not self._is_temp(arg2) and i + 1 < len(triplos):
                next_op, next_arg1, next_arg2 = triplos[i+1]
                
                if next_arg1 == arg1 and self._is_temp(next_arg2) and next_op in ['+', '-', '*', '/']:
                    # Revisar el triplo subsiguiente (i+2) para ver si guardamos
                    save_var = None
                    if i + 2 < len(triplos):
                        next2_op, next2_arg1, next2_arg2 = triplos[i+2]
                        if next2_op == "=" and next2_arg2 == arg1 and not self._is_temp(next2_arg1):
                            save_var = next2_arg1
                            skip_counter = 2 # Saltaremos la op y la asignación, ya que las haremos aquí
                        else:
                            skip_counter = 1 # Solo saltamos la op, el guardado será normal
                    else:
                        skip_counter = 1

                    # Emitir la operación optimizada usando BL
                    self._emit_smart_op(next_op, arg2, save_var)
                    continue

            self._translate_triplo(op, arg1, arg2)

        return "\n".join(self.lines)

    def _is_temp(self, arg):
        return arg and str(arg).startswith('T') and str(arg)[1:].isdigit()

    def _emit_smart_op(self, op, val, save_var=None):
        """
        Maneja: val [op] AL.
        Si save_var existe, guarda el resultado directo de BL a la variable.
        """
        self.lines.append(f"MOV BL, {val}") # Cargar constante en BL
        
        target_reg = "AL" # Por defecto regresamos a AL
        
        if op == "+":
            self.lines.append("ADD BL, AL") # BL = 8 + AL
            target_reg = "BL" # El resultado está en BL
            
        elif op == "-":
            self.lines.append("SUB BL, AL") # BL = 8 - AL
            target_reg = "BL"
            
        elif op == "*":
            self.lines.append("MUL BL") # AX = AL * BL
            target_reg = "AX" # Resultado en AX
            
        elif op == "/":
            # División inversa: 8 / AL. Complejo en 8 bits.
            # Asumimos estándar: MOV CL, AL -> MOV AX, BL -> DIV CL
            self.lines.append("MOV CL, AL")
            self.lines.append("MOV AL, BL")
            self.lines.append("MOV AH, 0")
            self.lines.append("DIV CL")
            target_reg = "AL"

        # --- OPTIMIZACIÓN DE GUARDADO ---
        if save_var:
            # Si tenemos variable destino, guardamos directo del registro donde quedó
            # Si target_reg es AX y la variable es 8 bits, tomamos AL (riesgo aceptado para este modelo)
            if target_reg == "AX": 
                self.lines.append(f"MOV {save_var}, AL") # Asumimos resultado cabe en 8 bits
            else:
                self.lines.append(f"MOV {save_var}, {target_reg}") # MOV mnmW, BL
        else:
            # Si no guardamos, debemos regresar el valor al acumulador AL
            if target_reg == "BL":
                self.lines.append("MOV AL, BL")

    def _translate_triplo(self, op, arg1, arg2):
        if op == "=":
            if self._is_temp(arg2):
                if not self._is_temp(arg1):
                    # Si venimos de MUL (16bit), usamos AX, si no AL
                    src = "AX" if self.is_16bit else "AL"
                    self.lines.append(f"MOV {arg1}, {src}")
                    self.is_16bit = False
                return
            
            self.is_16bit = False
            self.lines.append(f"MOV AL, {arg2}")
            if not self._is_temp(arg1):
                self.lines.append(f"MOV {arg1}, AL")

        elif op == "+":
            self.lines.append(f"ADD AL, {arg2}")
            self.is_16bit = False

        elif op == "-":
            self.lines.append(f"SUB AL, {arg2}")
            self.is_16bit = False

        elif op == "*":
            self.lines.append(f"MOV BL, {arg2}")
            self.lines.append("MUL BL")
            self.is_16bit = True # Resultado en AX

        elif op == "/":
            self.lines.append(f"MOV BL, {arg2}")
            
            self.lines.append("DIV BL")
            
            # --- CAMBIO SOLICITADO: Limpieza DESPUÉS ---
            self.lines.append("MOV AH, 0") # Limpiar residuo para que AX sea puro
            
            self.is_16bit = False # Cociente en AL

        elif op == "%":
            self.lines.append(f"MOV BL, {arg2}")
            self.lines.append("DIV BL")
            self.lines.append("MOV AL, AH") # Residuo a AL
            self.lines.append("MOV AH, 0")  # Limpiar AH
            self.is_16bit = False

        elif op in ["<", ">", "<=", ">=", "==", "!="]:
            op2 = arg2
            if not str(arg2).isdigit() and arg2 != "AL":
                self.lines.append(f"MOV BL, {arg2}")
                op2 = "BL"
            self.lines.append(f"CMP AL, {op2}")
            self.last_compare_op = op

        elif op == "JMP" or (op == "" and arg1 in ["True", "False"]):
            if arg1 in ["True", "False"]:
                instr = self._get_jump_instruction(arg1)
                self.lines.append(f"{instr} Et{arg2}")
            elif op == "JMP":
                self.lines.append(f"JMP Et{arg1}")

        elif op == "PRINT":
             self.lines.append(f"; PRINT {arg2}")

    def _get_jump_instruction(self, condition_type):
        op = self.last_compare_op
        if condition_type == "True":
            if op == "<": return "LT"
            if op == ">": return "GT"
            if op == "<=": return "LE"
            if op == ">=": return "GE"
            if op == "==": return "EQ"
            if op == "!=": return "NE"
        elif condition_type == "False":
            if op == "<": return "GE"
            if op == ">": return "LE"
            if op == "<=": return "GT"
            if op == ">=": return "LT"
            if op == "==": return "NE"
            if op == "!=": return "EQ"
        return "JMP"