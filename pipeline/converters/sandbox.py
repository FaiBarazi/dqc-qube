from types import MappingProxyType
from typing import Any

SAFE_BUILTINS = MappingProxyType(
    {
        "abs": abs,
        "all": all,
        "any": any,
        "bin": bin,
        "bool": bool,
        "chr": chr,
        "complex": complex,
        "dict": dict,
        "divmod": divmod,
        "enumerate": enumerate,
        "filter": filter,
        "float": float,
        "format": format,
        "frozenset": frozenset,
        "int": int,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "len": len,
        "list": list,
        "map": map,
        "max": max,
        "min": min,
        "next": next,
        "object": object,
        "pow": pow,
        "range": range,
        "repr": repr,
        "reversed": reversed,
        "round": round,
        "set": set,
        "slice": slice,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "type": type,
        "zip": zip,
    }
)

ALLOWED_IMPORT_ROOTS_QISKIT = frozenset({"cmath", "math", "numpy", "qiskit", "random"})
ALLOWED_IMPORT_ROOTS_PENNYLANE = frozenset({"cmath", "math", "numpy", "pennylane", "random"})


def _safe_import(name: str, allowed_import_roots: frozenset[str], globals=None, locals=None, fromlist=(), level=0):
    root = name.split(".")[0]
    if root in allowed_import_roots:
        return __import__(name, globals, locals, fromlist, level)
    raise ImportError(f"Import of module '{name}' is not allowed during conversion.")


def build_execution_namespace(
    allowed_import_roots: frozenset[str],
    extra_symbols: dict[str, Any] | None = None,
) -> dict[str, Any]:
    safe_builtins = dict(SAFE_BUILTINS)
    safe_builtins["__import__"] = lambda name, globals=None, locals=None, fromlist=(), level=0: _safe_import(
        name, allowed_import_roots, globals, locals, fromlist, level
    )

    namespace = {
        "__builtins__": safe_builtins,
        "__name__": "__submission__",
    }
    if extra_symbols:
        namespace.update(extra_symbols)
    return namespace

