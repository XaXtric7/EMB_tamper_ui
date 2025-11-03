import customtkinter as ctk
from ui import TamperUI

if __name__ == "__main__":
    root = ctk.CTk()
    app = TamperUI(root)
    app.create_ui()
    app.run()
