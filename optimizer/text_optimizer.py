# text_optimizer.py
# Módulo para optimizar el código fuente (mnm).

import re

# Regex para encontrar asignaciones
ASSIGNMENT_REGEX = re.compile(r"^\s*(mnm[A-Za-z0-9_]+)\s*=\s*(.*?);?\s*$")
VAR_REGEX = re.compile(r"(mnm[A-Za-z0-9_]+)")
# Regex para encontrar operaciones matemáticas simples
MATH_REGEX = re.compile(r"^\s*(\d+(\.\d+)?)\s*([\+\-\*\/])\s*(\d+(\.\d+)?)\s*$")

# Regex para multiplicación binaria simple A * B
BINARY_MULT_REGEX = re.compile(r"^([a-zA-Z0-9_.]+)\s*(\*)\s*([a-zA-Z0-9_.]+)$")

OPTIMIZED_PREFIX = "//OPTIMIZADO: "

class TextOptimizer:
    def __init__(self, source_code: str):
        self.original_lines = source_code.splitlines()
        self.optimized_lines = []
        
        self.known_expressions = {} 
        self.variable_to_expressions = {}
        self.copies = {}
        self.line_map = {}

    def _normalize(self, expr: str) -> str:
        """
        Normaliza la expresión ordenando términos y factores.
        Ej: "mnmB - 20 + mnmA * 5" -> "+5*mnmA+mnmB-20"
        """
        expr = expr.strip()
        
        # 1. Quitar paréntesis externos innecesarios: (A + B) -> A + B
        while expr.startswith('(') and expr.endswith(')'):
            # Chequeo simple: asegurar que los paréntesis se corresponden
            # (Esto evita romper cosas como "(A) + (B)")
            depth = 0
            is_wrapped = True
            for i, char in enumerate(expr[:-1]):
                if char == '(': depth += 1
                elif char == ')': depth -= 1
                if depth == 0 and i > 0: 
                    is_wrapped = False
                    break
            
            if is_wrapped:
                expr = expr[1:-1].strip()
            else:
                break

        # 2. Si es cadena o tiene división (no conmutativa), no tocar
        if any(c in expr for c in ['"', "'", '/']):
            return expr.replace(" ", "")
        
        # 3. Limpiar espacios y asegurar signo inicial
        expr_clean = expr.replace(" ", "")
        if not (expr_clean.startswith('+') or expr_clean.startswith('-')):
            expr_clean = "+" + expr_clean
            
        # 4. Separar en TÉRMINOS de suma/resta
        # Regex: (+ o -) seguido de (cualquier cosa que no sea + o -)
        # Esto funciona incluso con paréntesis internos si no hay signos fuera de ellos
        # Ej: +A+(B*C)
        terms = re.findall(r'[+-][^+-]+', expr_clean)
        
        # Si la suma de longitudes no coincide, algo salió mal con el regex
        # (ej: paréntesis complejos), así que abortamos la normalización avanzada
        if len("".join(terms)) != len(expr_clean):
            return expr.replace(" ", "")

        normalized_terms = []
        for term in terms:
            sign = term[0] # + o -
            content = term[1:] # mnmA*5
            
            # 5. Separar en FACTORES de multiplicación (si existen)
            # Ej: "mnmA*5" -> ["mnmA", "5"]
            if '*' in content and '(' not in content:
                factors = content.split('*')
                factors.sort() # Ordenar factores: "5*mnmA"
                content = "*".join(factors)
            
            normalized_terms.append(sign + content)
            
        # 6. Ordenar los términos completos
        # Ej: ["+5*mnmA", "+mnmB", "-20"] -> ["+5*mnmA", "+mnmB", "-20"] (orden alfa)
        normalized_terms.sort()
        
        return "".join(normalized_terms)

    def _propagate_values(self, text: str) -> str:
        parts = re.split(r'(".*?"|\'.*?\')', text)
        result = []
        for part in parts:
            if part.startswith('"') or part.startswith("'"):
                result.append(part)
            else:
                def replace_match(match):
                    var_name = match.group(1)
                    return self.copies.get(var_name, var_name)
                propagated_part = VAR_REGEX.sub(replace_match, part)
                result.append(propagated_part)
        return "".join(result)

    def _fold_constants(self, expression: str) -> str:
        match = MATH_REGEX.match(expression)
        if match:
            try:
                num1 = float(match.group(1))
                op = match.group(3)
                num2 = float(match.group(4))
                result = 0
                if op == '+': result = num1 + num2
                elif op == '-': result = num1 - num2
                elif op == '*': result = num1 * num2
                elif op == '/': result = num1 / num2 if num2 != 0 else 0
                
                if result.is_integer():
                    return str(int(result))
                return str(result)
            except:
                return expression
        return expression

    def _invalidate_expressions(self, var_name: str):
        if var_name in self.variable_to_expressions:
            expressions_to_remove = self.variable_to_expressions[var_name]
            for expr_norm in expressions_to_remove:
                if expr_norm in self.known_expressions:
                    del self.known_expressions[expr_norm]
            del self.variable_to_expressions[var_name]
            
        if var_name in self.copies:
            del self.copies[var_name]
        
        for copy_var, source_var in list(self.copies.items()):
            if source_var == var_name:
                del self.copies[copy_var]

    def optimize(self) -> tuple[str, dict]:
        self.optimized_lines = []
        self.known_expressions.clear()
        self.variable_to_expressions.clear()
        self.copies.clear()
        self.line_map = {}
        
        optimized_line_index = 1 

        for original_line_index, line in enumerate(self.original_lines, 1):
            match = ASSIGNMENT_REGEX.match(line)
            match_decl = re.match(r"^\s*(\\[a-z]+)\s+(mnm[A-Za-z0-9_]+)\s*=\s*(.*?);?\s*$", line)
            
            target_var = None
            raw_expr = None
            prefix = "" 

            if match_assign := match:
                target_var = match_assign.group(1).strip()
                raw_expr = match_assign.group(2).strip()
            elif match_decl:
                prefix = match_decl.group(1).strip() + " " 
                target_var = match_decl.group(2).strip()
                raw_expr = match_decl.group(3).strip()
            
            if not target_var:
                line_propagated = self._propagate_values(line)
                line_propagated = self._fold_constants(line_propagated)
                
                self.optimized_lines.append(line_propagated)
                self.line_map[optimized_line_index] = original_line_index
                optimized_line_index += 1
                
                simple_decl = re.match(r"^\s*(\\[a-z]+)\s+(mnm[A-Za-z0-9_]+)", line)
                if simple_decl:
                    self._invalidate_expressions(simple_decl.group(2))
                continue

            # --- PROCESO DE OPTIMIZACIÓN ---
            expression = self._propagate_values(raw_expr)
            expression = self._fold_constants(expression)
            expr_normalized = self._normalize(expression)
            self._invalidate_expressions(target_var)

            if expr_normalized in self.known_expressions:
                original_var = self.known_expressions[expr_normalized]
                
                # Optimización: Reemplazar por copia
                # NO generamos línea de asignación, solo registramos la copia
                self.optimized_lines.append(f"{OPTIMIZED_PREFIX}{line.strip()}")
                self.line_map[optimized_line_index] = original_line_index
                optimized_line_index += 1
                
                self.copies[target_var] = original_var

            else:
                # Cálculo Nuevo
                new_line = f"{prefix}{target_var} = {expression};"
                
                self.optimized_lines.append(new_line)
                self.line_map[optimized_line_index] = original_line_index
                optimized_line_index += 1
                
                self.known_expressions[expr_normalized] = target_var
                
                if not (expression.startswith('"') or expression.startswith("'")):
                    vars_in_expression = VAR_REGEX.findall(expression)
                    for var in vars_in_expression:
                        self.variable_to_expressions.setdefault(var, set()).add(expr_normalized)
                
                simple_assign_match = re.match(r"^(mnm[A-Za-z0-9_]+)$", expression.strip())
                if simple_assign_match:
                    self.copies[target_var] = simple_assign_match.group(1)

        return "\n".join(self.optimized_lines), self.line_map