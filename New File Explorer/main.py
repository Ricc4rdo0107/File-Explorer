import os
import sys
import ctypes
import platform
import subprocess
import tkinter as tk
from json import load
from time import sleep
from threading import Thread, Lock

"""
TODO: aggiungere trascinamento icone
"""

#EXTERNAL
import PIL
import PIL.Image
import customtkinter as ctk
from tkinter import BooleanVar
from tkinter.messagebox import showinfo
from shutil import rmtree, copy, copytree, move
from external_modules.assets64 import (dll_icon, file_icon, folder_icon, 
                                       image_icon, python_icon, txt_icon,
                                       home_icon, exe_icon, desktop_icon,
                                       zip_icon, rar_icon, right_arrow_icon)
from external_modules.app_state import AppState, CachedPath
from external_modules.utils import base64_to_pil_image, get_disk_info
from external_modules.customwidgets import CTkFloatingMenu, CTkInputPopup

import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileDeletedEvent


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache")
CACHE_FILE_PATH = os.path.join(CACHE_DIR, "file_explorer_cache.bin")

# Ensure the cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)
#showinfo = lambda title, message: Thread(target=showinfo, args=(title, message)).start()


"""
    oooooooooooo          oooooooooooo                                       .
    `888'     `8          `888'     `8                                     .o8
     888          .oooo.o  888         oooo    ooo  .ooooo.  ooo. .oo.   .o888oo
     888oooo8    d88(  "8  888oooo8     `88.  .8'  d88' `88b `888P"Y88b    888
     888    "    `"Y88b.   888    "      `88..8'   888ooo888  888   888    888
     888         o.  )88b  888       o    `888'    888    .o  888   888    888 .
    o888o        8""888P' o888ooooood8     `8'     `Y8bod8P' o888o o888o   "888"

    ooooo   ooooo                             .o8  oooo
    `888'   `888'                            "888  `888
     888     888   .oooo.   ooo. .oo.    .oooo888   888   .ooooo.  oooo d8b
     888ooooo888  `P  )88b  `888P"Y88b  d88' `888   888  d88' `88b `888""8P
     888     888   .oP"888   888   888  888   888   888  888ooo888  888
     888     888  d8(  888   888   888  888   888   888  888    .o  888
    o888o   o888o `Y888""8o o888o o888o `Y8bod88P" o888o `Y8bod8P' d888b
"""

class FsEventHandler(FileSystemEventHandler):
    def __init__(self, state, mountpoint):
        super().__init__()
        self.state = state
        self.mountpoint = mountpoint
        logging.info(f"Initialized FsEventHandler for mountpoint: {self.mountpoint}")

    def get_from_cache(self):
        mountpoint = str(self.mountpoint)
        if mountpoint not in self.state.system_cache:
            self.state.system_cache[mountpoint] = {}
            logging.info(f"Created new cache entry for mountpoint: {mountpoint}")
        return self.state.system_cache[mountpoint]

    def on_created(self, event):
        if isinstance(event, FileCreatedEvent):
            self.state.handle_create(event.src_path, 'file')
        elif isinstance(event, FileDeletedEvent):
            self.state.handle_create(event.src_path, 'directory')
        logging.info(f"File created: {event.src_path}")

    def on_deleted(self, event):
        self.state.handle_delete(event.src_path)
        logging.info(f"File deleted: {event.src_path}")

    def on_moved(self, event):
        self.state.handle_delete(event.src_path)
        self.state.handle_create(event.dest_path, 'file')
        logging.info(f"File moved from {event.src_path} to {event.dest_path}")

def start_event_handler(state, mountpoint):
    event_handler = FsEventHandler(state, mountpoint)
    observer = Observer()
    observer.schedule(event_handler, mountpoint, recursive=True)
    observer.start()
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


    """
    oooooooooooo                        oooo
    `888'     `8                        `888
     888         oooo    ooo oo.ooooo.   888   .ooooo.  oooo d8b  .ooooo.  oooo d8b
     888oooo8     `88b..8P'   888' `88b  888  d88' `88b `888""8P d88' `88b `888""8P
     888    "       Y888'     888   888  888  888   888  888     888ooo888  888
     888       o  .o8"'88b    888   888  888  888   888  888     888    .o  888
    o888ooooood8 o88'   888o  888bod8P' o888o `Y8bod8P' d888b    `Y8bod8P' d888b
                              888
                             o888o
    """


class Explorer:
    def __init__(self, app_state, STARTING_PATH=None):
        self.MARKER_COLOR = "#363636"
        self.DEFAULT_1 = "#4b4b4b"
        self.DEFAULT_2 = "transparent"

        platform_name = sys.platform
        self.system_platform = "windows" if platform_name.startswith("win") else "linux"

        self.copyied_item = False
        self.cutted_item  = False
        global can_draw
        can_draw = False

        self.HOME = os.environ.get("USERPROFILE") if self.system_platform == "windows" else os.environ.get("HOME")
        self.EXPLORER_ROOT = os.getcwd()

        ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"

        if os.path.exists(os.path.join(self.EXPLORER_ROOT, "config", "config.json")):
            self.CONFIG_DICT = load(open(os.path.join(self.EXPLORER_ROOT, "config", "config.json"), "r"))
            self.config_exists = True
        else:
            self.config_exists = False

        if STARTING_PATH is None and self.config_exists:
            STARTING_PATH = self.CONFIG_DICT["explorer"]["starting_path"]
        else:
            STARTING_PATH = os.getcwd()
        os.chdir(STARTING_PATH)
        self.STARTING_PATH = STARTING_PATH
            

        self.app_state = app_state


        """
        oooooooooooo ooooooooooooo ooooooooo.
        `888'     `8 8'   888   `8 `888   `Y88.
         888              888       888   .d88'
         888oooo8         888       888ooo88P'
         888    "         888       888
         888              888       888
        o888o            o888o     o888o


          .oooooo.     .oooooo.   ooooo      ooo oooooooooooo ooooo   .oooooo.
         d8P'  `Y8b   d8P'  `Y8b  `888b.     `8' `888'     `8 `888'  d8P'  `Y8b
        888          888      888  8 `88b.    8   888          888  888
        888          888      888  8   `88b.  8   888oooo8     888  888
        888          888      888  8     `88b.8   888    "     888  888     ooooo
        `88b    ooo  `88b    d88'  8       `888   888          888  `88.    .88'
         `Y8bood8P'   `Y8bood8P'  o8o        `8  o888o        o888o  `Y8bood8P'
        """

        self.FTP_SERVER_PATH = os.path.join(self.EXPLORER_ROOT, "external_modules", "ftp_server.py")
        if os.path.exists(self.FTP_SERVER_PATH):
            logging.info(f"FTP SERVER FOUND in {self.FTP_SERVER_PATH}")
        else:
            logging.warning(f"FTP SERVER NOT FOUND (should have been in {self.FTP_SERVER_PATH})")
        if self.config_exists:
            self.FTP_CONFIG_DICT = self.CONFIG_DICT["ftp_server"]
            self.FTP_HOST       = self.FTP_CONFIG_DICT["host"]
            self.FTP_PORT        = int(self.FTP_CONFIG_DICT["port"])
            self.FTP_USERNAME    = self.FTP_CONFIG_DICT["username"]
            self.FTP_PASSWORD    = self.FTP_CONFIG_DICT["password"]
            self.FTP_PERMISSION  = self.FTP_CONFIG_DICT["permissions"]
        else:
            self.FTP_HOST        = "0.0.0.0"
            self.FTP_CONFIG_DICT = None
            self.FTP_PORT        = 21
            self.FTP_USERNAME    = "root"
            self.FTP_PASSWORD    = "1234"
            self.FTP_PERMISSION  = "elradfmw"

        self.root = ctk.CTk()
        self.window_width = 700
        self.window_height = 700

        self.menus: list[CTkFloatingMenu] = []
        current_dirs = os.listdir()

        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.title("File Explorer")

        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.root.bind("<Button-1>", self.destroy_all_menus)

        self.DEFAULT_FONT_FAMILY = "Segoe UI"
        self.root.bind("<Control-plus>",  func=lambda x: self.zoom_in_all_labels())
        self.root.bind("<Control-minus>", func=lambda x: self.zoom_out_all_labels())

        #GRID COORDS
        TOOLS_FRAME  = (0, 0)
        SEARCH_FRAME = (1, 0)
        MAIN_FRAME   = (2, 0)

        self.toolsFrame = ctk.CTkFrame(self.root, height=0)
        self.toolsFrame.grid(row=TOOLS_FRAME[0], column=TOOLS_FRAME[1], sticky="nsew", padx=10, pady=10)
        self.toolsFrame.grid_columnconfigure(0, weight=1)
        self.toolsFrame.grid_rowconfigure(0, weight=1)
        self.toolsFrame.grid_rowconfigure(1, weight=1)

        global show_hidden
        show_hidden = BooleanVar(value=False)
        self.show_hidden_checkbox = ctk.CTkCheckBox(self.toolsFrame, text="Show Hidden",
                                                    variable=show_hidden, onvalue=True, offvalue=False, 
                                                    command=lambda x=None: self.draw_dirs([ x for x in os.listdir() ]))
        
        self.got_to_disks = ctk.CTkButton(self.toolsFrame, text="Go To Disks", command=self.display_disks)

        
        global isToolsLabelUp
        isToolsLabelUp = True
        self.openToolsLabel = ctk.CTkLabel(self.toolsFrame, text="")
        self.openToolsLabel.grid(row=1, column=0, sticky="nsew")
        self.openToolsLabel.bind("<Button-1>", command=lambda event: self.switch_tools_label_mode())
        #adding arrow image after updating the root window because tkinter works like this

        self.search_frame = ctk.CTkFrame(self.root)
        self.search_frame.grid(row=SEARCH_FRAME[0], column=SEARCH_FRAME[1], sticky="nsew", padx=10, pady=10)

        self.current_directory_entry = ctk.CTkEntry(self.search_frame, font=(self.DEFAULT_FONT_FAMILY, 13), width=300)
        self.current_directory_entry.pack(padx=(10, 5), pady=12, fill="x", side="left", expand=True)
        self.current_directory_entry.bind("<Return>", lambda x: self.try_changing_cwd(self.current_directory_entry.get().strip()))
        self.reload_title_entry()

        global advanced_search_mode
        advanced_search_mode = False
        self.searchEntry = ctk.CTkEntry(self.search_frame, font=(self.DEFAULT_FONT_FAMILY, 13), placeholder_text="Search..")
        self.searchEntry.pack(padx=(5, 10), pady=12, fill="x", expand=True)
        self.searchEntry.bind("<Control-Button-3>", lambda x: self.switch_search_mode())
        self.searchEntry.bind("<KeyRelease>", lambda x: self.draw_dirs(os.listdir(), self.searchEntry.get().strip().replace("\x08", "")))

        # MAIN FRAME STARTING POINT
        self.main_frame = ctk.CTkScrollableFrame(self.root)
        self.main_frame.grid(row=MAIN_FRAME[0], column=MAIN_FRAME[1], sticky="nsew", padx=10, pady=10)
        self.main_frame.columnconfigure(0, weight=1)
        self.scrollable_canvas = self.main_frame._parent_canvas
        self.scrollable_canvas.bind("<Button-3>", lambda x: self.on_right_click_dir(x, self.scrollable_canvas))

        #self.ASSETS_FOLDER = os.path.join(self.EXPLORER_ROOT,"assets")
        icon_size = (25, 25)

        """
        ooooo
        `888'
         888  ooo. .oo.  .oo.    .oooo.    .oooooooo  .ooooo.   .oooo.o
         888  `888P"Y88bP"Y88b  `P  )88b  888' `88b  d88' `88b d88(  "8
         888   888   888   888   .oP"888  888   888  888ooo888 `"Y88b.
         888   888   888   888  d8(  888  `88bod8P'  888    .o o.  )88b
        o888o o888o o888o o888o `Y888""8o `8oooooo.  `Y8bod8P' 8""888P'
                                          d"     YD
                                          "Y88888P'
        """

        #Explorer Icons for extensions of files or folders
        self.FOLDER_ICON     = base64_to_pil_image(folder_icon,  to_ctk_image=True, resize=icon_size)
        self.FILE_ICON       = base64_to_pil_image(file_icon,    to_ctk_image=True, resize=icon_size)
        self.FILE_TXT_ICON   = base64_to_pil_image(txt_icon,     to_ctk_image=True, resize=icon_size)
        self.FILE_PY_ICON    = base64_to_pil_image(python_icon,  to_ctk_image=True, resize=icon_size)
        self.FILE_IMAGE_ICON = base64_to_pil_image(image_icon,   to_ctk_image=True, resize=icon_size)
        self.FILE_DLL_ICON   = base64_to_pil_image(dll_icon,     to_ctk_image=True, resize=icon_size)
        self.HOME_ICON       = base64_to_pil_image(home_icon,    to_ctk_image=True, resize=icon_size)
        self.EXE_ICON        = base64_to_pil_image(exe_icon,     to_ctk_image=True, resize=icon_size)
        self.DESKTOP_ICON    = base64_to_pil_image(desktop_icon, to_ctk_image=True, resize=icon_size)
        self.ZIP_ICON        = base64_to_pil_image(zip_icon,     to_ctk_image=True, resize=icon_size)
        self.RAR_ICON        = base64_to_pil_image(rar_icon,     to_ctk_image=True, resize=icon_size)

        #Arrows
        self.RIGHT_ARROW_ICON  = base64_to_pil_image(right_arrow_icon, resize=(50,50))
        self.UP_ARROW_ICON     = ctk.CTkImage(self.RIGHT_ARROW_ICON.rotate(90, PIL.Image.NEAREST, expand=1))
        self.DOWN_ARROW_ICON   = ctk.CTkImage(self.RIGHT_ARROW_ICON.rotate(270, PIL.Image.NEAREST, expand=1))

        self.openToolsLabel.configure(image=self.DOWN_ARROW_ICON)

        #che merdaio
        self.EXTENSION2ICON = {
            "jpg"  : self.FILE_IMAGE_ICON,
            "png"  : self.FILE_IMAGE_ICON,
            "gif"  : self.FILE_IMAGE_ICON,
            "webp" : self.FILE_IMAGE_ICON,
            "tiff" : self.FILE_IMAGE_ICON,
            "psd"  : self.FILE_IMAGE_ICON,
            "raw"  : self.FILE_IMAGE_ICON,
            "bmp"  : self.FILE_IMAGE_ICON,
            "heif" : self.FILE_IMAGE_ICON,
            "indd" : self.FILE_IMAGE_ICON,
            "svg"  : self.FILE_IMAGE_ICON,
            "ai"   : self.FILE_IMAGE_ICON,
            "eps"  : self.FILE_IMAGE_ICON,
            "pdf"  : self.FILE_IMAGE_ICON,
            "dll"  : self.FILE_DLL_ICON,
            "txt"  : self.FILE_TXT_ICON,
            "py"   : self.FILE_PY_ICON,
            "exe"  : self.EXE_ICON,
            "zip"  : self.ZIP_ICON,
            "rar"  : self.RAR_ICON,
        }

        self.draw_dirs(current_dirs)
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.root.grab_set()    #Set the window on top
        self.root.grab_release()
        self.root.mainloop()

    def switch_tools_label_mode(self):
        global isToolsLabelUp
        isToolsLabelUp = not(isToolsLabelUp)
        if isToolsLabelUp:
            self.show_hidden_checkbox.grid_remove()
            self.got_to_disks.grid_remove()
            self.openToolsLabel.configure(image=self.DOWN_ARROW_ICON)
        else:
            self.show_hidden_checkbox.grid(row=0, column=0, sticky="nsew")
            self.got_to_disks.grid(row=0, column=1, sticky="nsew")
            self.openToolsLabel.configure(image=self.UP_ARROW_ICON)

    def on_exit(self, *args):
        self.root.destroy()
        stop_cache_thread_func()


    def choose_file_icon(self, filename):
        filename = filename.strip().replace("\x08", "")
        extension = filename.split(".")[-1]
        return self.EXTENSION2ICON.get(extension.lower(), self.FILE_ICON)

    """
    def load_png2tkimage(self, path):
        image = Image.open(path)
        if image.size != (25, 25):
            image = image.resize((25, 25), Image.LANCZOS)
        tk_image = ctk.CTkImage(image)
        return tk_image
    """

    def uni_path_split(self, string: str) -> list[str]:
        if self.system_platform == "windows":
            return string.split("\\")
        else:
            return string.split("/")

    def sort_dir_file(self, dirs):
        directories = list(filter(os.path.isdir, dirs))
        files = list(filter(os.path.isfile, dirs))        
        return directories+files

    def switch_search_mode(self):
        global advanced_search_mode
        advanced_search_mode = not(advanced_search_mode)
        if advanced_search_mode:
            self.searchEntry.configure(placeholder_text="Global Search...")
            self.searchEntry.unbind("<KeyRelease>", funcid=None)
            self.searchEntry.bind("<Return>", lambda x: self.draw_dirs_filtered(self.searchEntry.get().strip().replace("\x08", "")))
            self.root.focus()
        else:
            self.searchEntry.configure(placeholder_text="Search...")
            self.searchEntry.unbind("<Return>", funcid=None)
            self.searchEntry.bind("<KeyRelease>", lambda x: self.draw_dirs(os.listdir(), self.searchEntry.get().strip().replace("\x08", "")))
            self.root.focus()


    def destroy_all_menus(self, event=None):
        if not(self.menus):
            return
        for menu in self.menus:
            try:
                if menu.winfo_exists():
                    menu.destroy_custom()
            except tk.TclError:
                pass
        self.menus.clear()
        

    def popupInput(self, title, main_label) -> str:
        dialog = CTkInputPopup(title=title, text=main_label, centered=True)
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
            except FileExistsError as e:
                showinfo("File Alredy Exists", repr(e))
            except (PermissionError, OSError) as e:
                showinfo("Permission Error", repr(e))
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
            showinfo("File or directory not found", repr(e))
        except (PermissionError, OSError) as e:
            showinfo("Permission Denied", repr(e))
        
    
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
        

    """
    oooooooooo.                                          ooo        ooooo            o8o
    `888'   `Y8b                                         `88.       .888'            `"'
     888      888 oooo d8b  .oooo.   oooo oooo    ooo     888b     d'888   .oooo.   oooo  ooo. .oo.
     888      888 `888""8P `P  )88b   `88. `88.  .8'      8 Y88. .P  888  `P  )88b  `888  `888P"Y88b
     888      888  888      .oP"888    `88..]88..8'       8  `888'   888   .oP"888   888   888   888
     888     d88'  888     d8(  888     `888'`888'        8    Y     888  d8(  888   888   888   888
    o888bood8P'   d888b    `Y888""8o     `8'  `8'        o8o        o888o `Y888""8o o888o o888o o888o


    oooooooooooo
    `888'     `8
     888         oooo d8b  .oooo.   ooo. .oo.  .oo.    .ooooo.
     888oooo8    `888""8P `P  )88b  `888P"Y88bP"Y88b  d88' `88b
     888    "     888      .oP"888   888   888   888  888ooo888
     888          888     d8(  888   888   888   888  888    .o
    o888o        d888b    `Y888""8o o888o o888o o888o `Y8bod8P'

    """

    def checkifishidden(self, filepath):
        if os.name == 'nt':  # Windows
            try:
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(filepath))
                if attrs == -1:
                    return False
                # Verifica se l'attributo nascosto è impostato
                is_hidden = bool(attrs & 0x2)
                return is_hidden
            except Exception as e:
                return False
        else:  # Unix-like
            is_hidden = os.path.basename(filepath).startswith('.')
            return is_hidden


    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    

    def draw_single_dir(self, dirname, index):
        if dirname is None:
            return
        dirname_abs = os.path.abspath(dirname)
        if os.path.isdir(dirname):
            if dirname_abs == self.HOME:
                image = self.HOME_ICON

            elif dirname_abs == os.path.join(self.HOME, "Desktop"):
                image = self.DESKTOP_ICON

            else:
                image = self.FOLDER_ICON
        else:
            image = self.choose_file_icon(dirname)

        bg_color = self.DEFAULT_2
        new_label = ctk.CTkLabel(self.main_frame, text=dirname, compound="left", bg_color=bg_color, anchor="w",
                                 image=image,
                                 font=(self.DEFAULT_FONT_FAMILY, 13))
        new_label.grid(row=index, column=0, sticky="ew")
        new_label.bind("<Double-Button-1>", lambda event, dir_=dirname: self.on_double_click_entry(dir_))
        new_label.bind("<Button-3>",        lambda event, dir_=dirname, widget=new_label: self.on_right_click_dir(event, widget, dir_))
        new_label.bind("<Enter>", lambda event: new_label.configure(bg_color=self.MARKER_COLOR))
        new_label.bind("<Leave>", lambda event: new_label.configure(bg_color=bg_color))
        new_label.bind("<Control-c>", lambda event, dir_=dirname: self.copy_selected(dir_))
        new_label.bind("<Control-x>", lambda event, dir_=dirname: self.cut_selected(dir_))
        new_label.bind("<Control-v>", lambda event, dir_=dirname: self.paste(os.getcwd()))

    def draw_dirs_filtered(self, filter):
        self.clear_main_frame()
        global can_draw
        can_draw = True
        if not(filter.strip().replace("\x08", "")):
            self.draw_dirs()
            return
        elements_found = False
        for index, dir_ in enumerate(elements_found := self.app_state.search_files(filter, True, True)):
            if dir_:
                self.draw_single_dir(dir_, index)
                self.root.update()
                self.main_frame.update()
            if not can_draw:
                return
        
        if not elements_found:
            showinfo("No Result Found", f"No file or directory found with {filter}")
            self.draw_dirs()

    def draw_dirs(self, directories: list[str] = None, filter_condition: str = None) -> None:
        global can_draw

        can_draw = False
        self.clear_main_frame()
        """
        params:
            directories:
                list of directories that will be displayed
            filter_condition:
                file's name and directories's name must have <filter_condition> in their name
        """

        if directories is None or directories == []:
            directories = os.listdir()

        self.main_frame._parent_canvas.yview_moveto(0.0)

        if not(filter_condition is None or filter_condition.isspace()) and filter_condition:
            directories = list(filter(lambda x: filter_condition.lower() in x.lower(), directories[::]))
        
        if not(bool(self.show_hidden_checkbox.get())):
            directories = list(filter(lambda x: not(self.checkifishidden(os.path.abspath(x))), directories))

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

    def ftp_server(self, directory):
        try:
            os.startfile(self.FTP_SERVER_PATH, arguments=f"{self.FTP_HOST} {self.FTP_PORT} {directory} {self.FTP_USERNAME} {self.FTP_PASSWORD} {self.FTP_PERMISSION}")
        except Exception as e:
            logging.warning(f"FTP_SERVER could not be started because: {repr(e)}\nFULL ERROR:\n{e}\n\n")

    """
    oooooooooooo  o8o  oooo                 .oooooo.   ooooooooo.
    `888'     `8  `"'  `888                d8P'  `Y8b  `888   `Y88.
     888         oooo   888   .ooooo.     888      888  888   .d88'
     888oooo8    `888   888  d88' `88b    888      888  888ooo88P'
     888    "     888   888  888ooo888    888      888  888
     888          888   888  888    .o    `88b    d88'  888
    o888o        o888o o888o `Y8bod8P'     `Y8bood8P'  o888o
    """

    def paste(self, dir, copyied=None, cutted=None):
        assert bool(self.copyied_item) != bool(self.cutted_item), f"{bool(self.copyied_item)} != {bool(self.cutted_item)}"
        if self.copyied_item:
            itemname = os.path.split(self.copyied_item)[-1]
            if os.path.isdir(self.copyied_item):
                copytree(self.copyied_item, os.path.join(dir, itemname))
            elif os.path.isfile(self.copyied_item):
                copy(self.copyied_item, os.path.join(dir, itemname))
            self.cutted_item = None

        elif self.cutted_item:
            self.copyied_item = None
            move(self.cutted_item, dir)
        self.draw_dirs(dir)


    def copy_selected(self, directory):
        self.cutted_item = False
        self.copyied_item = os.path.abspath(directory)

    def cut_selected(self, directory):
        self.copyied_item = False
        self.cutted_item = os.path.abspath(directory)
    
    def openInIntegratedExplorer(self, dir_or_file):
        if os.path.isdir(dir_or_file):
            directory = dir_or_file
            os.startfile(directory)
        
        elif os.path.isfile(dir_or_file):
            file = dir_or_file
            path = self.uni_path_split(file)[:-1]
            os.startfile(path)

    """
    ooooooooo.    o8o             oooo            .        .oooooo.   oooo   o8o            oooo        
    `888   `Y88.  `"'             `888          .o8       d8P'  `Y8b  `888   `"'            `888        
     888   .d88' oooo   .oooooooo  888 .oo.   .o888oo    888           888  oooo   .ooooo.   888  oooo  
     888ooo88P'  `888  888' `88b   888P"Y88b    888      888           888  `888  d88' `"Y8  888 .8P'   
     888`88b.     888  888   888   888   888    888      888           888   888  888        888888.    
     888  `88b.   888  `88bod8P'   888   888    888 .    `88b    ooo   888   888  888   .o8  888 `88b.  
    o888o  o888o o888o `8oooooo.  o888o o888o   "888"     `Y8bood8P'  o888o o888o `Y8bod8P' o888o o888o 
                       d"     YD
                       "Y88888P'

    ooooo   ooooo                             .o8  oooo
    `888'   `888'                            "888  `888
     888     888   .oooo.   ooo. .oo.    .oooo888   888   .ooooo.
     888ooooo888  `P  )88b  `888P"Y88b  d88' `888   888  d88' `88b
     888     888   .oP"888   888   888  888   888   888  888ooo888
     888     888  d8(  888   888   888  888   888   888  888    .o
    o888o   o888o `Y888""8o o888o o888o `Y8bod88P" o888o `Y8bod8P'
    """


    def on_right_click_dir(self, event, widget: ctk.CTkLabel|ctk.CTkScrollableFrame, directory: str = None) -> None:
        self.destroy_all_menus()
        x, y  = event.x_root, event.y_root
        menu = CTkFloatingMenu(widget, on_death=self.draw_dirs)
        
        if widget_is_label := isinstance(widget, ctk.CTkLabel):
            widget.configure(bg_color=self.MARKER_COLOR)

        self.menus.append(menu)
        
        menu.add_option("New Folder",              command = lambda: self.new_dir(self.popupInput("Enter the New Folder's name", "New Folder"))),
        menu.add_option("New Text File",           command = lambda: self.new_file(self.popupInput("Enter New File's name", "New Text File"))),
        menu.add_option("Open in System Explorer", command = lambda: self.openInIntegratedExplorer(directory if widget_is_label else os.getcwd())),
        menu.add_option("Open Terminal Here",      command = lambda: self.open_terminal_in_directory(directory if widget_is_label else os.getcwd())),
        menu.add_option("Bind FTP Server Here",    command = lambda: self.ftp_server(os.getcwd())),
        
        if widget_is_label:
            menu.add_option("Cut",  command = lambda: self.cut_selected(directory))
            menu.add_option("Copy", command = lambda: self.copy_selected(directory))
            
        menu.add_option("Paste",  command = lambda dir_=os.getcwd(): self.paste(dir_))
        
        if not (directory is None) and not(".." in directory) and widget_is_label:
            menu.add_option("Delete", command = lambda: self.delete_file_or_dir(directory))        

        menu.popup(x, y)
        self.destroy_all_menus()

    def draw_single_disk(self, disk:dict, index):
        disk_name  = disk["disk_name"]
        tot_size   = disk["tot_size"]
        used       = disk["used"]
        free       = disk["free"][:3]
        percentage = float(disk["percentage"])/100

        disk_frame = ctk.CTkFrame(self.main_frame, border_color="black", border_width=3)
        disk_frame.bind("<Double-Button-1>", lambda x=None: self.on_double_click_entry(disk_name, checklastdot=False))

        disk_name_label = ctk.CTkLabel(disk_frame, text=f"{disk_name}\nFree: {free}/{tot_size}", anchor="w")
        disk_name_label.grid(row=0, column=0, padx=12, pady=12)

        disk_percentage_bar = ctk.CTkProgressBar(disk_frame)
        disk_percentage_bar.set(percentage)
        disk_percentage_bar.grid(row=2, column=0, padx=12, pady=(0, 12))

        disk_frame.grid(row=index, column=0, sticky="w")

    def display_disks(self):
        self.destroy_all_menus()
        self.clear_main_frame()
        disk_info = get_disk_info()

        for index, disk in enumerate(disk_info):
            self.draw_single_disk(disk, index)



    def on_double_click_entry(self, dir_: str, checklastdot: bool=True) -> None:
        last_path = os.getcwd()
        if dir_ == ".." and checklastdot:
            if os.path.abspath("..") == os.getcwd():
                self.display_disks()
                return
        if os.path.exists(dir_):
            try:
                if self.isdir_accessibe(dir_):
                    if os.path.isdir(dir_):
                        os.chdir(dir_)
                        directories = os.listdir()
                        self.reload_title_entry()
                        self.draw_dirs(directories)
                    elif os.path.isfile(dir_):
                        os.startfile(dir_)
                else:
                    raise PermissionError("Extceptional Permission Denied")
            except (PermissionError, OSError, IOError,) as e:
                showinfo("Permission Error", repr(e))
                os.chdir(last_path)
                directories = os.listdir()
                self.reload_title_entry()
                self.draw_dirs(directories)
                

    def isdir_accessibe(self, directory):
        can_read = os.access(directory, os.R_OK)
        can_write = os.access(directory, os.W_OK)
        can_execute = os.access(directory, os.X_OK)
        return can_read and can_write and can_execute


    def try_changing_cwd(self, directory: str) -> None:
        if not(directory) or directory.isspace() or not(directory.replace("\x08", "")):
            self.reload_title_entry()
            return

        shells: list[str] = ["cmd.exe", "cmd", "powershell", "powershell.exe"]
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

    """
     oooooooooooo
    d'""""""d888'
          .888P    .ooooo.   .ooooo.  ooo. .oo.  .oo.
         d888'    d88' `88b d88' `88b `888P"Y88bP"Y88b
       .888P      888   888 888   888  888   888   888
      d888'    .P 888   888 888   888  888   888   888
    .8888888888P  `Y8bod8P' `Y8bod8P' o888o o888o o888o
    """

    def zoom_in_all_labels(self):
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                font_family, current_size = widget.cget("font")
                new_size = int(current_size) + 2
                widget.configure(font=(font_family, new_size))

    def zoom_out_all_labels(self):
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                font_family, current_size = widget.cget("font")
                new_size = int(current_size) - 2
                widget.configure(font=(font_family, new_size))


stop_cache_thread = False
cache_thread_lock = Lock()


def explorer_func(app_state, starting_path):
    explorer = Explorer(app_state, starting_path)

def cache_func(app_state, mountpoint):
    global stop_cache_thread
    
    # Start filesystem observer to watch for changes
    observer = Observer()
    event_handler = FsEventHandler(app_state, mountpoint)
    observer.schedule(event_handler, mountpoint, recursive=True)
    observer.start()

    try:
        timeout = 45
        #start = perf_counter()
        while not stop_cache_thread:
            sleep(timeout)
        else:
            sys.exit()
    finally:
        observer.stop()
        observer.join()

def stop_cache_thread_func():
    global stop_cache_thread
    with cache_thread_lock:
        stop_cache_thread = True

"""
    ooo        ooooo            o8o              
    `88.       .888'            `"'              
     888b     d'888   .oooo.   oooo  ooo. .oo.   
     8 Y88. .P  888  `P  )88b  `888  `888P"Y88b  
     8  `888'   888   .oP"888   888   888   888  
     8    Y     888  d8(  888   888   888   888  
    o8o        o888o `Y888""8o o888o o888o o888o

    oooooooooooo                                       .    o8o
    `888'     `8                                     .o8    `"'
     888         oooo  oooo  ooo. .oo.    .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.
     888oooo8    `888  `888  `888P"Y88b  d88' `"Y8   888   `888  d88' `88b `888P"Y88b
     888    "     888   888   888   888  888         888    888  888   888  888   888
     888          888   888   888   888  888   .o8   888 .  888  888   888  888   888
    o888o         `V88V"V8P' o888o o888o `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o
"""

def main():
    global stop_cache_thread
    global app_state
    global mountpoint

    # Initialize app_state and mountpoint
    app_state = AppState(CACHE_FILE_PATH=CACHE_FILE_PATH, CachedPath=CachedPath)
    if os.path.exists(os.path.join("config", "config.json")):
        mountpoint = load(open(os.path.join("config", "config.json"), "r"))["explorer"]["mountpoint"]
    else:
        mountpoint = "C:\\" if "win" in platform.system() else "/"  # Set your mountpoint path here

    if not app_state.load_system_cache():
        app_state.map_filesystem(mountpoint)

    explorer_thread = Thread(target=explorer_func, args=(app_state, None,))
    explorer_thread.start()

    cache_thread = Thread(target=cache_func, args=(app_state, mountpoint,))
    cache_thread.start()

    cache_thread.join()

if __name__ == "__main__":
    main()