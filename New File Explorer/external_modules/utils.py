import os
import shutil
import base64
import platform
from PIL import Image
from io import BytesIO
from typing import Callable
from customtkinter import CTkImage

def get_disk_info() -> list[dict]:
    disk_info = []
    if platform.system() == 'Windows':
        for disk in ['%s:' % d for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']:
            try:
                total, used, free = shutil.disk_usage(disk)
                disk_info.append({
                    "disk_name": disk,
                    "tot_size": f"{total / (1024.0 ** 3):.2f} GB",
                    "used": f"{used / (1024.0 ** 3):.2f} GB",
                    "free": f"{free / (1024.0 ** 3):.2f} GB",
                    "percentage": f"{(used / total) * 100:.2f}"
                })
            except OSError:
                continue
    else:
        for disk in ['/']:
            try:
                st = os.statvfs(disk)
                total = st.f_frsize * st.f_blocks
                free = st.f_frsize * st.f_bavail
                used = total - free
                disk_info.append({
                    "disk_name": disk,
                    "tot_size": f"{total / (1024.0 ** 3):.2f} GB",
                    "used": f"{used / (1024.0 ** 3):.2f} GB",
                    "free": f"{free / (1024.0 ** 3):.2f} GB",
                    "percentage": f"{(used / total) * 100:.2f}%"
                })
            except OSError:
                continue
    return disk_info

def base64_to_pil_image(base64_str: bytes, resize:tuple =None, to_ctk_image: bool=False) -> CTkImage|Image.Image:
    image_data = base64.b64decode(base64_str)
    image = Image.open(BytesIO(image_data))
    if resize and image.size != resize:
        image.resize(resize, Image.LANCZOS)
    if to_ctk_image:
        image = CTkImage(image)
    return image

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


def search_advanced(hint: str, starting_path: str):
    for root, dirs, files in os.walk(starting_path):
        for file in files:
            if hint in file:
                yield os.path.join(root, file)
    yield None