from setuptools import setup, Extension

module = Extension(
    'search_module',
    sources=['search_advanced.cpp'],
    include_dirs=[],
    extra_compile_args=['/std:c++17'],  # Specify C++17 standard
    extra_link_args=[],
)

setup(
    name='search_module',
    version='1.0',
    description='A module to search files with a hint',
    ext_modules=[module],
)
