from typing import Callable
import customtkinter as ctk
from external_modules.utils import add_function

class CTkFloatingMenu(ctk.CTkToplevel):
    def __init__(self, master, winsize: tuple=(100,140), on_death:Callable=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
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
        #self.attributes("-alpha", 0.5)  # Set transparency level (0.0 to 1.0)
        #self.attributes("-transparentcolor", self["bg"])  # Make the background color transparent
        #self.bind("<Leave>",    self.on_focus_out)

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
        button.bind("<Button-1>", command=lambda x=None: self.quit_and_execute(command))#Uccidetemi
        self.buttons.append(button)
        return text
        
    def popup(self, x, y):
        self.geometry(f"{self.winsize[0]}x{self.winsize[1]-20}+{x}+{y}")
        self.mainloop()
