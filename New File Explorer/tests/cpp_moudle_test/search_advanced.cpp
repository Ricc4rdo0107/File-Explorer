#include <Python.h>
#include <vector>
#include <string>
#include <filesystem>
#include <algorithm> // For std::sort

#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif

namespace fs = std::filesystem;

void setConsoleEncoding() {
#ifdef _WIN32
    _setmode(_fileno(stdout), _O_U8TEXT);
    _setmode(_fileno(stderr), _O_U8TEXT);
#endif
}

bool containsHint(const std::string& name, const std::string& hint) {
    // Convert both name and hint to lowercase for case-insensitive comparison
    std::string name_lower = name;
    std::transform(name_lower.begin(), name_lower.end(), name_lower.begin(), ::tolower);
    std::string hint_lower = hint;
    std::transform(hint_lower.begin(), hint_lower.end(), hint_lower.begin(), ::tolower);

    return name_lower.find(hint_lower) != std::string::npos;
}

std::vector<std::string> search_advanced(const std::string& hint, const std::string& starting_path) {
    std::vector<std::string> result;
    try {
        for (const auto& entry : fs::recursive_directory_iterator(starting_path, fs::directory_options::skip_permission_denied)) {
            try {
                if (containsHint(entry.path().filename().string(), hint)) {
                    result.push_back(entry.path().string());
                }
            } catch (const std::filesystem::filesystem_error&) {
                continue; // Continue to next entry on error
            } catch (const std::exception&) {
                continue; // Continue to next entry on error
            }
        }
    } catch (const std::filesystem::filesystem_error&) {
        // Continue to the next directory on error
    } catch (const std::exception&) {
        // Continue to the next directory on error
    }

    // Sort result by length of paths
    std::sort(result.begin(), result.end(), [](const std::string& a, const std::string& b) {
        return a.size() < b.size();
    });

    return result;
}

// Wrapper function for Python
static PyObject* py_search_advanced(PyObject* self, PyObject* args) {
    const char* hint;
    const char* starting_path;

    if (!PyArg_ParseTuple(args, "ss", &hint, &starting_path)) {
        return NULL;
    }

    std::vector<std::string> result = search_advanced(hint, starting_path);

    PyObject* py_result = PyList_New(result.size());

    for (size_t i = 0; i < result.size(); ++i) {
        PyObject* py_path = PyUnicode_Decode(result[i].c_str(), result[i].size(), "cp850", "strict");
        if (!py_path) {
            Py_DECREF(py_result);
            return NULL;
        }
        PyList_SetItem(py_result, i, py_path);
    }

    return py_result;
}

// Module method definition
static PyMethodDef SearchMethods[] = {
    {"search_advanced", py_search_advanced, METH_VARARGS, "Search files and directories with hint and sort by length"},
    {NULL, NULL, 0, NULL}
};

// Module initialization function
static struct PyModuleDef searchmodule = {
    PyModuleDef_HEAD_INIT,
    "search_module",
    NULL,
    -1,
    SearchMethods
};

// Module initialization function for Python 3
PyMODINIT_FUNC PyInit_search_module(void) {
    setConsoleEncoding(); // Set console encoding for Windows
    return PyModule_Create(&searchmodule);
}
