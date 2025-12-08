# ensamblador/assembler_generator.py
# Generador de Ensamblador: Regla de Oro AX para Variables y Números.

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

        skip_counter = 0 
        
        for i, (op, arg1, arg2) in enumerate(triplos):
            if skip_counter > 0:
                skip_counter -= 1
                continue

            line_num = i + 1
            if line_num in self.jump_targets:
                self.lines.append(f"Et{line_num}:")
            
            # --- DETECCIÓN: CARGA PARA DIVISIÓN (FORCE AX) ---
            # CORRECCIÓN: Ahora aplica si arg2 NO es temporal (es numero O variable)
            force_ax_load = False
            if op == "=" and not self._is_temp(arg2) and i + 1 < len(triplos):
                next_op, next_arg1, _ = triplos[i+1]
                # Si la siguiente operación es división/modulo y usa esta variable
                if next_op in ['/', '%'] and next_arg1 == arg1:
                    force_ax_load = True

            # --- LOOKAHEAD INTELIGENTE (Operaciones Inversas) ---
            # Solo entramos si NO forzamos AX
            if op == "=" and not self._is_temp(arg2) and i + 1 < len(triplos) and not force_ax_load:
                next_op, next_arg1, next_arg2 = triplos[i+1]
                if next_arg1 == arg1 and self._is_temp(next_arg2) and next_op in ['+', '-', '*', '/']:
                    save_var = None
                    if i + 2 < len(triplos):
                        next2_op, next2_arg1, next2_arg2 = triplos[i+2]
                        if next2_op == "=" and next2_arg2 == arg1 and not self._is_temp(next2_arg1):
                            save_var = next2_arg1
                            skip_counter = 2
                        else:
                            skip_counter = 1
                    else:
                        skip_counter = 1

                    self._emit_smart_op(next_op, arg2, save_var)
                    continue

            self._translate_triplo(op, arg1, arg2, force_ax_load)

        return "\n".join(self.lines)

    def _is_temp(self, arg):
        return arg and str(arg).startswith('T') and str(arg)[1:].isdigit()

    def _emit_smart_op(self, op, val, save_var=None):
        self.lines.append(f"MOV BL, {val}") 
        target_reg = "AL" 
        
        if op == "+":
            self.lines.append("ADD BL, AL") 
            target_reg = "BL" 
        elif op == "-":
            self.lines.append("SUB BL, AL") 
            target_reg = "BL"
        elif op == "*":
            self.lines.append("MUL BL")
            target_reg = "AX" 
        elif op == "/":
            self.lines.append("MOV CL, AL")
            self.lines.append("MOV AL, BL")
            self.lines.append("MOV AH, 0")
            self.lines.append("DIV CL")
            self.lines.append("MOV AH, 0")
            target_reg = "AL"

        if save_var:
            if target_reg == "AX": 
                self.lines.append(f"MOV {save_var}, AL") 
            else:
                self.lines.append(f"MOV {save_var}, {target_reg}") 
        else:
            if target_reg == "BL":
                self.lines.append("MOV AL, BL")

    def _translate_triplo(self, op, arg1, arg2, force_ax_load=False):
        if op == "=":
            if self._is_temp(arg2):
                if not self._is_temp(arg1):
                    src = "AX" if self.is_16bit else "AL"
                    self.lines.append(f"MOV {arg1}, {src}")
                    self.is_16bit = False
                return
            
            # --- CARGA CORRECTA EN AX ---
            if force_ax_load:
                self.lines.append(f"MOV AX, {arg2}") # Carga Variable o Numero en 16 bits
                self.is_16bit = True 
            else:
                self.is_16bit = False
                self.lines.append(f"MOV AL, {arg2}")
            
            if not self._is_temp(arg1):
                src = "AX" if force_ax_load else "AL"
                self.lines.append(f"MOV {arg1}, {src}")

        elif op == "+":
            self.lines.append(f"ADD AL, {arg2}")
            self.is_16bit = False

        elif op == "-":
            self.lines.append(f"SUB AL, {arg2}")
            self.is_16bit = False

        elif op == "*":
            self.lines.append(f"MOV BL, {arg2}")
            self.lines.append("MUL BL")
            self.is_16bit = True 

        # --- DIVISIÓN ---
        elif op == "/":
            self.lines.append(f"MOV BL, {arg2}")
            
            # Si NO venimos de una carga forzada a AX o MUL, limpiamos AH
            if not self.is_16bit: 
                self.lines.append("MOV AH, 0")
            
            self.lines.append("DIV BL")
            self.lines.append("MOV AH, 0") 
            self.is_16bit = False

        elif op == "%":
            self.lines.append(f"MOV BL, {arg2}")
            if not self.is_16bit:
                self.lines.append("MOV AH, 0")
            self.lines.append("DIV BL")
            self.lines.append("MOV AL, AH") 
            self.lines.append("MOV AH, 0")
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