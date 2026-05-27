import tkinter as tk
from db import init_db, seed_preset_data
from ui_main import MainWindow


def main():
    init_db()
    seed_preset_data()

    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
