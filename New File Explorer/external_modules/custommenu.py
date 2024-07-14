from typing import Callable
import customtkinter as ctk
#from utils import add_function

def add_function(function_before: Callable=None, function_after: Callable=None):
    def wrapper(function: Callable): 
        res_before = res_after = None
        if function_before:
            res_before = function_before()
        res = function()
        if function_after:
            res_after = function_after()
        return res_before, res, res_after
    return wrapper

class CTkFloatingMenu(ctk.CTkToplevel):
    def __init__(self, master, winsize: tuple=(100,140), on_death:Callable=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.winsize = winsize
        self.overrideredirect(1)

        self.screensize: tuple[int, int]= (self.master.winfo_screenwidth(), self.master.winfo_screenheight())

        self.on_death = on_death
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.BigFrame = ctk.CTkFrame(self)
        self.BigFrame.rowconfigure(0, weight=1)
        self.BigFrame.columnconfigure(0, weight=1)
        self.BigFrame.grid(row=0, column=0, sticky="nsew")
        self.buttons = []
        self.bind("<FocusOut>", self.on_focus_out)

    def destroy_custom(self):
        return add_function(self.on_death)(super().destroy) if self.on_death else super().destroy()

    def on_focus_out(self, event):
        self.destroy_custom()

    def quit_and_execute(self, function: Callable):
        self.destroy()
        function()

    def add_option(self, text, command) -> None:
        button = ctk.CTkButton(self.BigFrame, text=text, fg_color="#2b2b2b", hover_color="#3d3d3d",  border_color="black")
        button.pack(fill="x")
        button.bind("<Button-1>", command=lambda x=None: self.quit_and_execute(command))
        self.buttons.append(button)
        return text
        
    def popup(self, x, y):
        self.winsize = (150, 32*len(self.buttons))

        if y > self.screensize[1]-self.winsize[1]:
            y-=self.winsize[1]

        elif y <= self.winsize[1]:
            y += self.winsize[1]/2

        elif x <= self.winsize[0]:
            x += self.winsize[0]/2

        elif x > self.screensize[0]-self.winsize[0]:
            x-=self.winsize[0]

        self.geometry(f"{self.winsize[0]}x{self.winsize[1]-20}+{x}+{y}")
        self.mainloop()