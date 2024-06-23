from typing import Callable
import subprocess
import platform
import os
from time import perf_counter

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

if __name__ == "__main__":
    start = perf_counter()
    hw = search_advanced("ricky", "C:\\Users")
    end = perf_counter()
    print(f"{hw}\nIt took {end-start} seconds")