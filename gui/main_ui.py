import tkinter as tk
from tkinter import ttk
import time

class MainUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Main Application")
        self.geometry("800x600")
        
        self.create_menu()
        self.create_central_widgets()
        self.create_status_bar()
    
    def create_menu(self):
        menu_bar = tk.Menu(self)
        
        # Menu File
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Menu Help
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Documentation", command=self.show_docs)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.config(menu=menu_bar)
    
    def create_central_widgets(self):
        self.label = ttk.Label(self, text="Welcome to the Application")
        self.label.pack(pady=20)
        
        self.button = ttk.Button(self, text="Click Me", command=self.button_clicked)
        self.button.pack(pady=10)
    
    def create_status_bar(self):
        self.status = tk.StringVar()
        self.status.set("Ready")
        status_bar = ttk.Label(self, textvariable=self.status, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def open_file(self):
        # Thêm logic mở file tại đây
        pass
    
    def save_file(self):
        # Thêm logic lưu file tại đây
        pass
    
    def show_about(self):
        # Hiển thị hộp thoại About tại đây
        pass
    
    def show_docs(self):
        # Hiển thị tài liệu tại đây
        pass
    
    def button_clicked(self):
        self.label.config(text="Button was clicked!")
        self.status.set("Button clicked at " + time.strftime("%H:%M:%S"))

if __name__ == "__main__":
    app = MainUI()
    app.mainloop()