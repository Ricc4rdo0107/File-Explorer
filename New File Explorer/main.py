import os
import sys                 #I could use json for cache system
from PIL import Image
from shutil import rmtree

import search_module as sm
search_advanced = sm.search_advanced
#from utils import search_advanced

import customtkinter as ctk
import subprocess, platform
from time import perf_counter
from tkinter.messagebox import showinfo
from custommenu import CTkFloatingMenu, CTkPopup

class Explorer:
    def __init__(self, STARTING_PATH):
        os.chdir(STARTING_PATH)
        self.STARTING_PATH  = STARTING_PATH
        self.MARKER_COLOR = "#363636"
        self.DEFAULT_1    = "#4b4b4b"
        self.DEFAULT_2    = "transparent"
        self.FOLDER_EMOJI = "📁"
        self.EXPLORER_ROOT= "\\".join(os.path.abspath(__file__).split("\\")[:-1])
        
        self.root = ctk.CTk()
        self.window_width  = 700
        self.window_height = 500


        self.menus: list[CTkFloatingMenu] = []

        current_dirs = os.listdir(os.getcwd())

        platform_name = sys.platform
        self.system_platform = "windows" if platform_name.startswith("win") else "linux"

        self.root.geometry(f"{self.window_width}x{self.window_height}")
        #self.root.resizable(0, 0)
        self.root.title("File Explorer")

        # Configure the grid to allow resizing
        self.root.grid_rowconfigure(0, weight=0)     # Titleframe doesn't resize vertically
        self.root.grid_rowconfigure(1, weight=1)     # Mainframe resizes vertically

        self.root.grid_columnconfigure(0, weight=1)  # Column 0 resizes horizontally

        self.root.bind("<Button-1>", self.destroy_all_menus)

        self.upper_frame = ctk.CTkFrame(self.root)
        self.upper_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.current_directory_entry = ctk.CTkEntry(self.upper_frame, font=("Helvetica", 13), width=300)
        self.current_directory_entry.pack(padx=(10, 5), pady=12, fill="x", side="left", expand=True)
        self.current_directory_entry.bind("<Return>", lambda x: self.try_changing_cwd(self.current_directory_entry.get().strip()))
        self.reload_title_entry()

        global advanced_search_mode
        advanced_search_mode = False
        self.searchEntry = ctk.CTkEntry(self.upper_frame, font=("Helvetica", 13), placeholder_text="Search..")
        self.searchEntry.pack(padx=(5, 10), pady=12, fill="x", side="right", expand=True)
        self.searchEntry.bind("<Control-Button-3>", lambda x: self.switch_search_mode())
        self.searchEntry.bind("<KeyRelease>", lambda x: self.draw_dirs(os.listdir(), self.searchEntry.get().strip().replace("\x08", "")))

        self.main_frame = ctk.CTkScrollableFrame(self.root)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.columnconfigure(0, weight=1)
        self.scrollable_canvas = self.main_frame._parent_canvas
        self.scrollable_canvas.bind("<Button-3>", lambda x: self.on_right_click_dir(x, self.scrollable_canvas))

        self.FOLDER_ICON = self.load_png2tkimage(f"{self.EXPLORER_ROOT}\\assets\\folder_smaller.png")

        self.draw_dirs(current_dirs)
        self.root.mainloop()

    """
    def on_right_click_anywhere(self, event):
        widget_clicked = event.widget
        widget_class = widget_clicked.winfo_class()
        print(f"Right-click event on widget of class {widget_class} at coordinates: ({event.x}, {event.y})")
    """

    def load_png2tkimage(self, path):
        image = Image.open(path)
        tk_image = ctk.CTkImage(image)
        return tk_image

    def sort_dir_file(self, dirs):
        directories = list(filter(os.path.isdir, dirs))
        files = list(filter(os.path.isfile, dirs))        
        return directories+files

    def switch_search_mode(self):
        global advanced_search_mode
        advanced_search_mode = not(advanced_search_mode)
        if advanced_search_mode:
            self.searchEntry.configure(placeholder_text="Advanced Search...")
            self.searchEntry.unbind("<KeyRelease>", funcid=None)
            self.searchEntry.bind("<Return>", lambda x: self.draw_dirs_filtered(self.searchEntry.get().strip().replace("\x08", "")))
            self.root.focus()
        else:
            self.searchEntry.configure(placeholder_text="Search...")
            self.searchEntry.unbind("<Return>", funcid=None)
            self.searchEntry.bind("<KeyRelease>", lambda x: self.draw_dirs(os.listdir(), self.searchEntry.get().strip().replace("\x08", "")))
            self.root.focus()


    def destroy_all_menus(self, event=None):
        for menu in self.menus:
            try:
                menu.destroy()
            except:
                pass
        self.menus.clear()
        

    def popupInput(self, title, main_label) -> str:
        dialog = ctk.CTkInputDialog(title=title, text=main_label)
        x = self.root.winfo_screenwidth()  / 2
        y = self.root.winfo_screenheight() / 2
        dialog.geometry("%d+%d"%(x, y))
        dialog.overrideredirect(1)
        res = dialog.get_input()
        return res
    

    def new_file(self, filename) -> bool:
        """
        returns True if the file has been created
        """
        ret = False
        if filename:
            try:
                f = open(filename, "w")
                f.close()
                ret = True
                self.draw_dirs()
            except FileExistsError:
                pop = CTkPopup(self.root, "File alredy exists", text=repr(e))
            except (PermissionError, OSError) as e:
                pop = CTkPopup(self.root, "Permission error", text=repr(e))
            if not ret:
                pop.popup(3)
            return ret
        return ret


    def delete_file_or_dir(self, filename: str):
        try:
            if os.path.isdir(filename):
                rmtree(filename)
            elif os.path.isfile(filename):
                os.unlink(filename)
            else:
                print("Wtf?")
            self.draw_dirs()
        except (FileNotFoundError) as e:
            popup = CTkPopup(self.root, "File or Directory not found", repr(e))
            popup.popup(3)
        except (PermissionError, OSError) as e:
            popup = CTkPopup(self.root, "Permission Denied", repr(e))
            popup.popup(3)
        
    
    def new_dir(self, dirname) -> bool:
        ret = False
        if dirname:
            try:
                os.mkdir(dirname)
                self.draw_dirs()
                ret = True
            except FileExistsError as e:
                showinfo("Directory alredy exists", repr(e))
            except PermissionError as e:
                showinfo("Permission denied", repr(e))
            except (FileNotFoundError) as e:
                showinfo("File or Directory not found", repr(e))
            return ret
    

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.grid_remove()
    

    def draw_single_dir(self, dirname, index):
        if dirname is None:
            return
        bg_color = self.DEFAULT_2#self.DEFAULT_1 if index % 2 == 0 else self.DEFAULT_2
        #dirname = self.FOLDER_EMOJI+dirname if os.path.isdir(dirname) else dirname
        new_label = ctk.CTkLabel(self.main_frame, text=dirname, compound="left", bg_color=bg_color, anchor="w",
                                 image=self.FOLDER_ICON if os.path.isdir(dirname) else None)
        new_label.grid(row=index, column=0, sticky="ew")
        new_label.bind("<Double-Button-1>", lambda event, dir_=dirname: self.on_double_click_entry(dir_))
        new_label.bind("<Button-3>",        lambda event, dir_=dirname, widget=new_label: self.on_right_click_dir(event, widget, dir_))
        new_label.bind("<Enter>",           lambda event: new_label.configure(bg_color=self.MARKER_COLOR))
        new_label.bind("<Leave>",           lambda event: new_label.configure(bg_color=bg_color))
        

    def draw_dirs_filtered(self, filter):
        self.clear_main_frame()
        for index, dir_ in enumerate(search_advanced(filter, os.getcwd())):
            self.draw_single_dir(dir_, index)
            self.root.update()
            self.main_frame.update()

        if not(len(self.main_frame)):
            showinfo(f"No Result Found", "No file or directory found with {filter}")

    def draw_dirs(self, directories: list[str] = None, filter_condition: str = None) -> None:
        """
        params:
            directories:
                list of directories that will be displayed
            filter_condition:
                file's name and directories's name must have <filter_condition> in their name
        """

        if directories is None:
            directories = os.listdir()

        self.clear_main_frame()

        self.main_frame._parent_canvas.yview_moveto(0.0)

        if filter_condition:
            filter_condition = filter_condition.strip().replace("\x08", "")

        if not(filter_condition is None or filter_condition.isspace()) and filter_condition:
            directories = filter(lambda x: filter_condition.lower() in x.lower(), directories[::])
            
        directories = self.sort_dir_file(directories)

        for index, dir_ in enumerate([".."]+list(directories)):
            self.draw_single_dir(dir_, index)


    def open_terminal_in_directory(self, directory):
        system = platform.system()
        if system == 'Linux':
            terminal_emulators = ['gnome-terminal', 'konsole', 'xfce4-terminal', 'xterm']
            for emulator in terminal_emulators:
                if subprocess.call(f'command -v {emulator}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
                    if emulator == 'gnome-terminal':
                        terminal_command = [emulator, '--', 'bash', '-c', f'cd {directory}; exec bash']
                    else:
                        terminal_command = [emulator, '--workdir', directory]
                    subprocess.run(terminal_command)
                    return
            showinfo("No emulator found", "Could not find a terminal emuator")
        elif system == 'Darwin':
            terminal_command = ['osascript', '-e', f'tell application "Terminal" to do script "cd {directory}"']
            subprocess.run(terminal_command)
        elif system == 'Windows':
            terminal_command = ['cmd', '/c', 'start', 'cmd', '/k', f'cd /d {directory}']
            subprocess.run(terminal_command)
        
        else:
            showinfo("Usupported Operating System", "This operating system is not supported by this program")

    
    def openInIntegratedExplorer(self, dir_or_file):
        if os.path.isdir(dir_or_file):
            directory = dir_or_file
            os.startfile(directory)
        
        elif os.path.isfile(dir_or_file):
            file = dir_or_file
            path = os.path.abspath(file).split("\\")[:-1]
            os.startfile(path)


    def on_right_click_dir(self, event, widget: ctk.CTkLabel|ctk.CTkScrollableFrame, directory: str = None) -> None:
        self.destroy_all_menus()
        x, y  = event.x_root, event.y_root
        menu = CTkFloatingMenu(widget, on_death=self.draw_dirs)
        
        if widget_is_label := isinstance(widget, ctk.CTkLabel):
            widget.configure(bg_color=self.MARKER_COLOR)
        self.menus.append(menu)
        options = [
            menu.add_option("New Folder",              command= lambda: self.new_dir(self.popupInput("Enter the New Folder's name", "New Folder"))),
            menu.add_option("New Text File",           command= lambda: self.new_file(self.popupInput("Enter New File's name", "New Text File"))),
            menu.add_option("Open in System Explorer", command= lambda: self.openInIntegratedExplorer(directory if widget_is_label else os.getcwd())),
            menu.add_option("Open Terminal Here",      command= lambda: self.open_terminal_in_directory(directory if widget_is_label else os.getcwd()))
        ]
        
        #
        if not (directory is None) and not(".." in directory):
            options.append(menu.add_option("Delete", command=lambda: self.delete_file_or_dir(directory)))
        menu.winsize = (150, 32*len(options))
        
        menu.popup(x, y)
        self.destroy_all_menus()


    def on_double_click_entry(self, dir_: str) -> None:
        if os.path.exists(dir_):
            try:
                if os.path.isdir(dir_):
                    os.chdir(dir_)
                if os.path.isfile(dir_):
                    os.startfile(dir_)
            except (PermissionError, OSError, IOError) as e:
                showinfo("Permission Error", repr(e))

        directories = os.listdir(os.getcwd())
        self.reload_title_entry()
        self.draw_dirs(directories)


    def try_changing_cwd(self, directory: str) -> None:
        #the directory is alredy stripped
        if not(directory) or directory.isspace() or not(directory.replace("\x08", "")):
            self.reload_title_entry()
            return

        shells = ["cmd.exe", "cmd", "powershell", "powershell.exe"]
        if directory in shells and self.system_platform == "windows":
            os.system(f"start {directory} {os.getcwd()}")
            self.reload_title_entry()
            return
        if directory == "code":
            os.system(f"code {os.getcwd()}")
        try:
            if os.path.exists(directory):
                if os.path.isdir(directory):
                    os.chdir(directory)
                    self.draw_dirs()
                elif os.path.isfile(directory):
                    os.startfile(directory)
            else:
                raise FileNotFoundError
        except FileNotFoundError as e:
            showinfo("File or Directory not found", f"Could not find {directory}")
            self.reload_title_entry()


    def reload_title_entry(self) -> None:
        self.current_directory_entry.delete(0, ctk.END)
        self.current_directory_entry.insert(0, f"{os.getcwd()}")

def main():
    STARTING_PATH = r"C:\\"
    explorer = Explorer(STARTING_PATH)

if __name__ == "__main__":
    main()