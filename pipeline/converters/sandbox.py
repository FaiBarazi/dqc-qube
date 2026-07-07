from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, Optional


@dataclass(frozen=True)
class EntryPointConfig:
    """Configuration for how to extract and execute the entry point from user code."""

    mode: Literal["function", "class_method", "direct"] = "function"
    name: str = "solve"
    method_name: str = ""
    args: list = field(default_factory=list)
    kwargs: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.mode == "class_method" and not self.method_name:
            raise ValueError("method_name is required for class_method mode")


# Default entry point config for backward compatibility
DEFAULT_ENTRY_POINT = EntryPointConfig(mode="function", name="solve")


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
        "__build_class__": __build_class__,
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
    extra_symbols: Optional[dict[str, Any]] = None,
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


def execute_submission(
    source: str,
    entry_point_config: Optional[EntryPointConfig],
    namespace: dict[str, Any],
    type_validator: callable,
    type_error_message: str,
    allow_direct_submission: bool = False,
) -> Any:
    """
    Execute user code and extract result based on entry point configuration.

    Supports three modes:
    - function: Call the named function with configured args/kwargs
    - class_method: Instantiate the named class, then call the specified method
    - direct: Return the named object directly (must pass type validation)

    Args:
        source: The user's Python source code
        entry_point_config: Configuration for how to extract the result.
            If None, uses DEFAULT_ENTRY_POINT (function mode, name="solve").
        namespace: The execution namespace
        type_validator: Function to validate the result type
        type_error_message: Error message if type validation fails
        allow_direct_submission: If True, allow the named object itself to be the result

    Returns:
        The result of executing the entry point

    Raises:
        RuntimeError: If execution fails, entry point not found, or type validation fails
    """
    config = entry_point_config or DEFAULT_ENTRY_POINT

    try:
        exec(compile(source, "<submission>", "exec"), namespace)
    except Exception as exc:
        raise RuntimeError(f"Could not execute submission source: {exc}") from exc

    entry_point = namespace.get(config.name)

    if config.mode == "direct":
        if entry_point is None:
            raise RuntimeError(f"Submission must define '{config.name}'")
        if not type_validator(entry_point):
            raise RuntimeError(type_error_message)
        return entry_point

    if entry_point is None:
        raise RuntimeError(f"Submission must define a callable '{config.name}'")

    if allow_direct_submission and type_validator(entry_point):
        return entry_point

    if not callable(entry_point):
        raise RuntimeError(f"Submission must define a callable '{config.name}'")

    if config.mode == "function":
        try:
            result = entry_point(*config.args, **config.kwargs)
        except Exception as exc:
            raise RuntimeError(f"`{config.name}` failed while building the circuit: {exc}") from exc

        if not type_validator(result):
            raise RuntimeError(type_error_message)
        return result

    elif config.mode == "class_method":
        try:
            instance = entry_point(*config.args, **config.kwargs)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to instantiate `{config.name}` with args={config.args}, kwargs={config.kwargs}: {exc}"
            ) from exc

        method = getattr(instance, config.method_name, None)
        if method is None:
            raise RuntimeError(
                f"Class `{config.name}` has no method '{config.method_name}'"
            )
        if not callable(method):
            raise RuntimeError(
                f"'{config.method_name}' on class `{config.name}` is not callable"
            )

        try:
            result = method()
        except Exception as exc:
            raise RuntimeError(
                f"Method `{config.method_name}` on `{config.name}` failed: {exc}"
            ) from exc

        if not type_validator(result):
            raise RuntimeError(type_error_message)
        return result

    else:
        raise RuntimeError(f"Unknown entry point mode: {config.mode}")


def execute_submission_source(
    source: str,
    function_name: str,
    namespace: dict[str, Any],
    type_validator: callable,
    type_error_message: str,
    allow_direct_submission: bool = False,
) -> Any:
    """
    Execute user code and extract result by calling a function.

    This is the original function for backward compatibility.
    For new code, use execute_submission() with EntryPointConfig.

    Args:
        source: The user's Python source code
        function_name: Name of the function to call
        namespace: The execution namespace
        type_validator: Function to validate the result type
        type_error_message: Error message if type validation fails
        allow_direct_submission: If True, allow the function itself to be the result

    Returns:
        The result of calling the function
    """
    config = EntryPointConfig(mode="function", name=function_name)
    return execute_submission(
        source=source,
        entry_point_config=config,
        namespace=namespace,
        type_validator=type_validator,
        type_error_message=type_error_message,
        allow_direct_submission=allow_direct_submission,
    )
