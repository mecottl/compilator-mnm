
import csv
from typing import List, Tuple

def export_triplos_to_txt(triplos: List[Tuple], filename: str):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"{'#':<5} {'Operador':<10} {'DO':<15} {'DF':<15}\n")
            f.write("-" * 47 + "\n")
            for idx, (op, arg1, arg2) in enumerate(triplos, 1):
                arg1_str = arg1 if arg1 is not None else ""
                arg2_str = arg2 if arg2 is not None else ""
                f.write(f"{idx:<5} {op:<10} {arg1_str:<15} {arg2_str:<15}\n")
    except Exception as e:
        print(f"Error al guardar el archivo TXT: {e}")

def export_triplos_to_csv(triplos: List[Tuple], filename: str):
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['#', 'Operador', 'DO', 'DF'])
            for idx, (op, arg1, arg2) in enumerate(triplos, 1):
                arg1_str = arg1 if arg1 is not None else ""
                arg2_str = arg2 if arg2 is not None else ""
                writer.writerow([idx, op, arg1_str, arg2_str])
    except Exception as e:
        print(f"Error al guardar el archivo CSV: {e}")