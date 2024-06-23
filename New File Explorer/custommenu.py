from typing import Callable
import customtkinter as ctk
from time import perf_counter
from utils import add_function


class CTkFloatingMenu(ctk.CTkToplevel):
    def __init__(self, master, winsize: tuple=(100,140), on_death:Callable=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.popup_time = 0
        self.master = master
        self.winsize = winsize
        self.overrideredirect(1)

        self.on_death = on_death

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.BigFrame = ctk.CTkFrame(self)
        self.BigFrame.rowconfigure(0, weight=1)
        self.BigFrame.columnconfigure(0, weight=1)
        self.BigFrame.grid(row=0, column=0, sticky="nsew")
        self.buttons = []
        self.bind("<FocusOut>", self.on_focus_out)
        self.geometry("%dx%d" % self.winsize)
        #self.bind("<Leave>",    self.on_focus_out)

    def destroy(self):
        return add_function(self.on_death)(super().destroy) if self.on_death else super().destroy()

    def on_focus_out(self, event):
        self.destroy()

    def quit_and_execute(self, function: Callable):
        self.destroy()
        function()

    def add_option(self, text, command) -> None:
        button = ctk.CTkButton(self.BigFrame, text=text, corner_radius=0, fg_color="transparent", hover_color="#3d3d3d")
        button.pack(fill="x")
        button.bind("<Button-1>", command=lambda x=None: self.quit_and_execute(command))#Uccidetemi
        self.buttons.append(button)
        
    def popup(self, x, y):
        self.popup_time = perf_counter()
        self.geometry(f"{self.winsize[0]}x{self.winsize[1]-20}+{x}+{y}")
        self.mainloop()


class CTkPopup(ctk.CTkToplevel):
    def __init__(self, master, title: str, text: str, size: tuple=(300, 70), centered: bool=False, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.size = size
        self.overrideredirect(1)
        self.title = title
        self.text = ctk.CTkLabel(self, text=text, font=("Helvetica", 10))
        self.text.pack(fill="x")
        if centered:
            x = master.winfo_width()/2
            y = master.winfo_height()/2
            self.geometry("%d+%d"%(x, y))


    def popup(self, timeout: int):
        start = perf_counter()
        self.mainloop()
        while perf_counter()-start < timeout:
            continue
        else:
            self.destroy()