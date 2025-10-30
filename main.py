# main.py - Punto de entrada de la aplicación
import tkinter as tk
from tkinter import messagebox
import sys
from gui.main_window import MainWindow


def main():
    try:
        root = tk.Tk()
        app = MainWindow(root)
        root.mainloop()
    
    except KeyboardInterrupt:
        print("\nAplicación cerrada por el usuario")
        sys.exit(0)
    
    except Exception as e:
        messagebox.showerror("Error Fatal", f"Error inesperado: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()