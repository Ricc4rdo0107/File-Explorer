from typing import Callable
import os
from customtkinter import CTkImage
from PIL import Image
import base64
from io import BytesIO
#from assets64 import dll

def base64_to_pil_image(base64_str, to_ctk_image=False):
    image_data = base64.b64decode(base64_str)
    image = Image.open(BytesIO(image_data))
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