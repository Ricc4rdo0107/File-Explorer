from tkinter.messagebox import showinfo
from json import dump, loads, dumps
from typing import List
from time import sleep
import logging
import zstd
import os


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

"""
          .o.                                 .oooooo..o     .                 .
         .888.                               d8P'    `Y8   .o8               .o8
        .8"888.     oo.ooooo.  oo.ooooo.     Y88bo.      .o888oo  .oooo.   .o888oo  .ooooo.
       .8' `888.     888' `88b  888' `88b     `"Y8888o.    888   `P  )88b    888   d88' `88b
      .88ooo8888.    888   888  888   888         `"Y88b   888    .oP"888    888   888ooo888
     .8'     `888.   888   888  888   888    oo     .d8P   888 . d8(  888    888 . 888    .o
    o88o     o8888o  888bod8P'  888bod8P'    8""88888P'    "888" `Y888""8o   "888" `Y8bod8P'
                     888        888
                    o888o      o888o
"""

class AppState:
    def __init__(self, CACHE_FILE_PATH, CachedPath):
        self.system_cache = {}
        self.CACHE_FILE_PATH = CACHE_FILE_PATH
        self.CachedPath = CachedPath

    def search_files(self, filename: str, dirfirst: bool=False, sortet_by_lenght: bool=False) -> List[str]:
        results = []
        if not filename:
            return results
        for i in range(5):
            try:
                for path, cache in self.system_cache.copy().items():
                    for file_name, cached_paths in cache.copy().items():
                        for cached_path in cached_paths:
                            if filename.lower() in cached_path['file_path'].lower().split("\\")[-1]:
                                if dirfirst and os.path.isdir(cached_path["file_path"]):
                                    results.insert(0, cached_path["file_path"])
                                else:
                                    results.append(cached_path['file_path'])
                if sortet_by_lenght:
                    results = sorted(results, key=lambda x: len(x))
                return results
            except RuntimeError as e:
                showinfo("Runtime Error", repr(e))
                sleep(1)

    def map_filesystem(self, root_path):
        for root, dirs, files in os.walk(root_path):
            for name in dirs:
                path = os.path.join(root, name)
                self.handle_create(path, 'directory')
            for name in files:
                path = os.path.join(root, name)
                self.handle_create(path, 'file')

    def handle_create(self, path, kind):
        filename = os.path.basename(path)
        file_type = "FILE" if kind == 'file' else "DIRECTORY"

        # Check if path exists in system_cache, if not create it
        if path not in self.system_cache:
            self.system_cache[path] = {}

        if filename not in self.system_cache[path]:
            self.system_cache[path][filename] = []

        self.system_cache[path][filename].append(self.CachedPath(path, file_type).__dict__)
        logging.debug(f"Handled create: {path}, type: {file_type}")

    def handle_delete(self, path):
        try:
            filename = os.path.basename(path)
            del self.system_cache[path][filename]
            logging.info(f"Deleted from cache: {path}")
        except KeyError:
            logging.warning(f"Attempted to delete non-existing path from cache: {path}")

    def save_to_cache(self):
        serialized_cache = dumps(self.system_cache)
        compressed_cache = zstd.compress(serialized_cache.encode('utf-8'), 1)
        with open(self.CACHE_FILE_PATH, 'wb') as cache_file:
            cache_file.write(compressed_cache)
        logging.info("Cache saved to disk")

    """
    ooooo                                  .o8       .oooooo.                       oooo
    `888'                                 "888      d8P'  `Y8b                      `888
     888          .ooooo.   .oooo.    .oooo888     888           .oooo.    .ooooo.   888 .oo.    .ooooo.
     888         d88' `88b `P  )88b  d88' `888     888          `P  )88b  d88' `"Y8  888P"Y88b  d88' `88b
     888         888   888  .oP"888  888   888     888           .oP"888  888        888   888  888ooo888
     888       o 888   888 d8(  888  888   888     `88b    ooo  d8(  888  888   .o8  888   888  888    .o
    o888ooooood8 `Y8bod8P' `Y888""8o `Y8bod88P"     `Y8bood8P'  `Y888""8o `Y8bod8P' o888o o888o `Y8bod8P'

    """

    def load_system_cache(self):
        try:
            with open(self.CACHE_FILE_PATH, 'rb') as cache_file:
                compressed_cache = cache_file.read()
            decompressed_cache = zstd.decompress(compressed_cache).decode('utf-8')
            self.system_cache = loads(decompressed_cache)
            logging.info("Cache loaded from disk")
            logging.info(f"Loaded cache content")#: {self.system_cache}")
            return True
        except FileNotFoundError:
            logging.warning("Cache file not found, initializing new cache.")
            return False
        except Exception as e:
            logging.error(f"Failed to deserialize the cache from disk: {e}")
            return False