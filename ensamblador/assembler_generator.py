# ensamblador/assembler_generator.py
# Generador Final: JMP corregido (apunta a ETIQUETA correcta) y Regla de Oro.

class AssemblerGenerator:
    def __init__(self):
        self.lines = []
        self.labels = {} 
        self.last_compare_op = None
        self.is_16bit = False 
        self.result_in_ah = False 

    def generate(self, triplos: list) -> str:
        self.lines = []
        self.labels = {}
        self.last_compare_op = None
        self.is_16bit = False
        self.result_in_ah = False
        
        # 1. Identificar etiquetas (Pasada robusta)
        unique_targets = set()
        for op, arg1, arg2 in triplos:
            # Detectamos el destino correcto
            if op == "JMP" or (op == "" and arg1 in ["True", "False"]):
                # Si es condicional (True/False), destino en arg2. Si es JMP, destino en arg1.
                target = arg2 if arg1 in ["True", "False"] else arg1
                
                target_str = str(target).replace("Et", "").strip()
                if target_str.isdigit():
                     unique_targets.add(int(target_str))
        
        # 2. Asignar nombres ETIQUETAx secuenciales
        for idx, line_num in enumerate(sorted(unique_targets), start=1):
            self.labels[line_num] = f"ETIQUETA{idx}"

        skip_counter = 0 
        
        for i, (op, arg1, arg2) in enumerate(triplos):
            if skip_counter > 0:
                skip_counter -= 1
                continue

            # --- GESTIÓN DE ETIQUETA EN LÍNEA ---
            current_label_prefix = ""
            line_num = i + 1 
            if line_num in self.labels:
                current_label_prefix = f"{self.labels[line_num]}: "

            # --- DETECCIÓN: CARGA PARA DIVISIÓN/MÓDULO (FORCE AX) ---
            force_ax_load = False
            if op == "=" and not self._is_temp(arg2) and i + 1 < len(triplos):
                next_op, next_arg1, _ = triplos[i+1]
                if next_op in ['/', '%'] and next_arg1 == arg1:
                    force_ax_load = True

            # --- LOOKAHEAD INTELIGENTE ---
            smart_op_done = False
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

                    self._emit_smart_op(next_op, arg2, save_var, current_label_prefix)
                    smart_op_done = True
            
            if smart_op_done:
                continue

            self._translate_triplo(op, arg1, arg2, force_ax_load, current_label_prefix)

        return "\n".join(self.lines)

    def _is_temp(self, arg):
        return arg and str(arg).startswith('T') and str(arg)[1:].isdigit()

    def _add_line(self, instruction, label_prefix=""):
        if label_prefix:
            self.lines.append(f"{label_prefix}{instruction}")
        else:
            self.lines.append(instruction)

    def _emit_smart_op(self, op, val, save_var=None, label_prefix=""):
        self._add_line(f"MOV BL, {val}", label_prefix)
        
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

    def _translate_triplo(self, op, arg1, arg2, force_ax_load=False, label_prefix=""):
        
        if self.result_in_ah and op != "=":
            self._add_line("MOV AL, AH", label_prefix)
            self.lines.append("MOV AH, 0")
            self.result_in_ah = False
            label_prefix = "" 

        if op == "=":
            if self._is_temp(arg2):
                if not self._is_temp(arg1):
                    if self.result_in_ah:
                        self._add_line("MOV AL, 0", label_prefix)
                        self.lines.append(f"MOV {arg1}, AH") 
                        self.result_in_ah = False
                    else:
                        src = "AX" if self.is_16bit else "AL"
                        self._add_line(f"MOV {arg1}, {src}", label_prefix)
                        self.is_16bit = False
                return
            
            reg = "AX" if force_ax_load else "AL"
            self._add_line(f"MOV {reg}, {arg2}", label_prefix)
            self.is_16bit = force_ax_load
            
            if not self._is_temp(arg1):
                self.lines.append(f"MOV {arg1}, {reg}")
            
            self.result_in_ah = False 

        elif op == "+":
            self._add_line(f"MOV BL, {arg2}", label_prefix)
            self.lines.append("ADD AL, BL")
            self.is_16bit = False

        elif op == "-":
            self._add_line(f"MOV BL, {arg2}", label_prefix)
            self.lines.append("SUB AL, BL")
            self.is_16bit = False

        elif op == "*":
            self._add_line(f"MOV BL, {arg2}", label_prefix)
            self.lines.append("MUL BL")
            self.is_16bit = True 

        elif op == "/":
            self._add_line(f"MOV BL, {arg2}", label_prefix)
            if not self.is_16bit: 
                self.lines.append("MOV AH, 0")
            self.lines.append("DIV BL")
            self.lines.append("MOV AH, 0") 
            self.is_16bit = False

        elif op == "%":
            self._add_line(f"MOV BL, {arg2}", label_prefix)
            if not self.is_16bit:
                self.lines.append("MOV AH, 0")
            self.lines.append("DIV BL")
            self.result_in_ah = True 
            self.is_16bit = False

        elif op in ["<", ">", "<=", ">=", "==", "!="]:
            op2 = arg2
            if not str(arg2).isdigit() and arg2 != "AL":
                self._add_line(f"MOV BL, {arg2}", label_prefix)
                op2 = "BL"
                label_prefix = "" 
            
            self._add_line(f"CMP AL, {op2}", label_prefix)
            self.last_compare_op = op

        # --- CORRECCIÓN FINAL EN SALTOS ---
        elif op == "JMP" or (op == "" and arg1 in ["True", "False"]):
            
            # ¡AQUÍ ESTABA EL ERROR!
            # Si es JMP (incondicional), el destino está en arg1.
            # Si es Condicional (True/False), el destino está en arg2.
            target_val = arg2 if arg1 in ["True", "False"] else arg1
            
            raw_target = str(target_val).replace("Et", "").strip()
            target_line = int(raw_target) if raw_target.isdigit() else 0
            
            label_name = self.labels.get(target_line, f"Et{target_val}")

            if arg1 in ["True", "False"]:
                instr = self._get_jump_instruction(arg1)
                self._add_line(f"{instr} {label_name}", label_prefix)
            elif op == "JMP":
                self._add_line(f"JMP {label_name}", label_prefix)

        elif op == "PRINT":
             self._add_line(f"; PRINT {arg2}", label_prefix)
        
        elif label_prefix:
            self.lines.append(f"{label_prefix[:-2]}:")

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
            return "JMP"
        return "JMP"