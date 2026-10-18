import ast
import typing as T
from pathlib import Path

from dataclassy import dataclass

from groupy.call_graph.models.call_edge import CallEdge
from groupy.call_graph.models.call_graph import CallGraph
from groupy.nodes.rules.get_target_module_names import get_target_module_names

_FUNCTION_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)


@dataclass
class _ClassInfo:
    module_name: str
    name: str
    bases: T.List[ast.expr] = []
    method_names: T.List[str] = []


@dataclass
class _ModuleInfo:
    module_name: str
    tree: ast.Module
    # A top-level name maps onto ("function", location) or ("class", class name)
    definitions: T.Dict[str, T.Tuple[str, str]] = {}
    # An imported name maps onto ("module", dotted name) or
    # ("symbol", dotted module name, name)
    imports: T.Dict[str, T.Tuple[str, ...]] = {}
    classes: T.Dict[str, _ClassInfo] = {}


def create_call_graph(source_root: Path) -> CallGraph:
    module_infos = {
        module_name: _create_module_info(source_root, module_name)
        for module_name in get_target_module_names(source_root)
    }
    resolver = _Resolver(module_infos)

    functions = []
    edges = []
    for module_info in module_infos.values():
        functions += [
            location
            for kind, location in module_info.definitions.values()
            if kind == "function"
        ]
        for class_info in module_info.classes.values():
            functions += [
                f"{module_info.module_name}:{class_info.name}.{method_name}"
                for method_name in class_info.method_names
            ]
        edges += _CallCollector(resolver, module_info).collect()
    return CallGraph(functions=functions, edges=edges)


def _get_dotted_name(module_name: str) -> str:
    parts = module_name[: -len(".py")].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _create_module_info(source_root: Path, module_name: str) -> _ModuleInfo:
    tree = ast.parse((source_root / module_name).read_text())
    module_info = _ModuleInfo(module_name=module_name, tree=tree)
    package = _get_dotted_name(module_name)
    if not module_name.endswith("__init__.py"):
        package = package.rpartition(".")[0]

    for statement in tree.body:
        if isinstance(statement, _FUNCTION_DEFS):
            module_info.definitions[statement.name] = (
                "function",
                f"{module_name}:{statement.name}",
            )
        elif isinstance(statement, ast.ClassDef):
            module_info.definitions[statement.name] = ("class", statement.name)
            module_info.classes[statement.name] = _ClassInfo(
                module_name=module_name,
                name=statement.name,
                bases=statement.bases,
                method_names=[
                    item.name
                    for item in statement.body
                    if isinstance(item, _FUNCTION_DEFS)
                ],
            )
        elif isinstance(statement, ast.Import):
            for alias in statement.names:
                if alias.asname:
                    module_info.imports[alias.asname] = ("module", alias.name)
                else:
                    # `import a.b` binds the name a
                    root = alias.name.split(".")[0]
                    module_info.imports[root] = ("module", root)
        elif isinstance(statement, ast.ImportFrom):
            from_module = statement.module or ""
            if statement.level:
                base = package.split(".")
                base = base[: len(base) - statement.level + 1]
                from_module = ".".join([*base, from_module]).strip(".")
            for alias in statement.names:
                module_info.imports[alias.asname or alias.name] = (
                    "symbol",
                    from_module,
                    alias.name,
                )
    return module_info


class _Resolver:
    def __init__(self, module_infos: T.Dict[str, _ModuleInfo]):
        self.module_infos = module_infos
        self.module_name_by_dotted_name = {
            _get_dotted_name(module_name): module_name for module_name in module_infos
        }
        self.method_locations_by_name: T.Dict[str, T.List[str]] = {}
        for module_info in module_infos.values():
            for class_info in module_info.classes.values():
                for method_name in class_info.method_names:
                    self.method_locations_by_name.setdefault(method_name, []).append(
                        _method_location(class_info, method_name)
                    )

    def resolve_name(
        self, module_name: str, name: str, seen: T.FrozenSet = frozenset()
    ) -> T.Optional[T.Tuple]:
        # Returns ("function", location), ("class", class info), ("module", module
        # name), ("package", dotted name), ("external",) or None (unknown)
        if (module_name, name) in seen:
            return None
        seen = seen | {(module_name, name)}
        module_info = self.module_infos[module_name]

        if name in module_info.definitions:
            kind, value = module_info.definitions[name]
            if kind == "function":
                return ("function", value)
            return ("class", module_info.classes[value])

        if name in module_info.imports:
            imported = module_info.imports[name]
            if imported[0] == "module":
                return self.resolve_dotted_name(imported[1])

            # An imported name is resolved in the module that it comes from, also
            # when that module imports it in turn
            _, from_module, imported_name = imported
            if from_module in self.module_name_by_dotted_name:
                result = self.resolve_name(
                    self.module_name_by_dotted_name[from_module], imported_name, seen
                )
                if result is not None:
                    return result
            return self.resolve_dotted_name(f"{from_module}.{imported_name}")
        return None

    def resolve_dotted_name(self, dotted_name: str) -> T.Tuple:
        if dotted_name in self.module_name_by_dotted_name:
            return ("module", self.module_name_by_dotted_name[dotted_name])
        if any(
            each.startswith(f"{dotted_name}.")
            for each in self.module_name_by_dotted_name
        ):
            return ("package", dotted_name)
        return ("external",)

    def resolve_attribute(
        self, base: T.Optional[T.Tuple], name: str
    ) -> T.Optional[T.Tuple]:
        if base is None:
            return None
        if base[0] == "module":
            return self.resolve_name(base[1], name)
        if base[0] == "package":
            return self.resolve_dotted_name(f"{base[1]}.{name}")
        if base[0] == "class":
            class_info = self.find_method_class(base[1], name)
            if class_info:
                return ("function", _method_location(class_info, name))
            return None
        if base[0] == "external":
            return ("external",)
        return None

    def resolve_class(
        self, class_info: _ClassInfo, expr: ast.expr
    ) -> T.Optional[_ClassInfo]:
        result = self.resolve_expression(class_info.module_name, expr)
        return result[1] if result and result[0] == "class" else None

    def resolve_expression(
        self, module_name: str, expr: ast.expr
    ) -> T.Optional[T.Tuple]:
        if isinstance(expr, ast.Name):
            return self.resolve_name(module_name, expr.id)
        if isinstance(expr, ast.Attribute):
            return self.resolve_attribute(
                self.resolve_expression(module_name, expr.value), expr.attr
            )
        return None

    def find_method_class(self, class_info: _ClassInfo, method_name: str, depth=0):
        # The class (or base class in the target code) that defines the method
        if method_name in class_info.method_names:
            return class_info
        if depth > 20:
            return None
        for base in class_info.bases:
            base_class_info = self.resolve_class(class_info, base)
            if base_class_info:
                found = self.find_method_class(base_class_info, method_name, depth + 1)
                if found:
                    return found
        return None

    def get_overrides(self, class_info: _ClassInfo, method_name: str) -> T.List[str]:
        # The locations of the methods that override the method in subclasses
        result = []
        for module_info in self.module_infos.values():
            for other in module_info.classes.values():
                if other is class_info or method_name not in other.method_names:
                    continue
                if self.is_subclass(other, class_info):
                    result.append(_method_location(other, method_name))
        return result

    def is_subclass(self, class_info: _ClassInfo, base_class_info: _ClassInfo, depth=0):
        if depth > 20:
            return False
        for base in class_info.bases:
            resolved = self.resolve_class(class_info, base)
            if resolved is base_class_info or (
                resolved and self.is_subclass(resolved, base_class_info, depth + 1)
            ):
                return True
        return False


def _method_location(class_info: _ClassInfo, method_name: str) -> str:
    return f"{class_info.module_name}:{class_info.name}.{method_name}"


class _CallCollector:
    def __init__(self, resolver: _Resolver, module_info: _ModuleInfo):
        self.resolver = resolver
        self.module_info = module_info
        self.edges: T.List[CallEdge] = []

    def collect(self) -> T.List[CallEdge]:
        module_name = self.module_info.module_name
        module_location = f"{module_name}:@module"
        for statement in self.module_info.tree.body:
            if isinstance(statement, _FUNCTION_DEFS):
                self._collect_module_code(statement.decorator_list, module_location)
                self._collect_function(
                    statement, f"{module_name}:{statement.name}", None
                )
            elif isinstance(statement, ast.ClassDef):
                class_info = self.module_info.classes[statement.name]
                for item in statement.body:
                    if isinstance(item, _FUNCTION_DEFS):
                        self._collect_module_code(item.decorator_list, module_location)
                        self._collect_function(
                            item, _method_location(class_info, item.name), class_info
                        )
                    else:
                        self._collect_module_code([item], module_location)
                self._collect_module_code(
                    [*statement.bases, *statement.decorator_list], module_location
                )
            else:
                self._collect_module_code([statement], module_location)
        return self.edges

    def _collect_module_code(self, nodes: T.List[ast.AST], caller: str) -> None:
        for node in nodes:
            for call in _find_calls(node):
                self._add_edges(call, caller, set(), None)

    def _collect_function(
        self, function_def, caller: str, class_info: T.Optional[_ClassInfo]
    ) -> None:
        # A nested function is part of the body of its enclosing function
        local_names = _get_local_names(function_def)
        self_name = None
        if class_info is not None and function_def.args.args:
            self_name = function_def.args.args[0].arg
        for statement in function_def.body:
            for call in _find_calls(statement):
                self._add_edges(call, caller, local_names, class_info, self_name)

    def _add_edges(
        self,
        call: ast.Call,
        caller: str,
        local_names: T.Set[str],
        class_info: T.Optional[_ClassInfo],
        self_name: T.Optional[str] = None,
    ) -> None:
        for callee, is_certain in self._get_callees(
            call.func, local_names, class_info, self_name
        ):
            self.edges.append(
                CallEdge(
                    caller=caller,
                    callee=callee,
                    file=self.module_info.module_name,
                    line=call.lineno,
                    is_certain=is_certain,
                )
            )

    def _get_callees(self, func, local_names, class_info, self_name):
        resolver = self.resolver
        module_name = self.module_info.module_name

        if isinstance(func, ast.Name):
            if func.id in local_names:
                return []
            return _get_certain_callees(resolver.resolve_name(module_name, func.id))

        if not isinstance(func, ast.Attribute):
            return []

        # A call of a method of self
        if (
            self_name
            and isinstance(func.value, ast.Name)
            and func.value.id == self_name
        ):
            method_class_info = resolver.find_method_class(class_info, func.attr)
            if method_class_info is None:
                return []
            location = _method_location(method_class_info, func.attr)
            overrides = resolver.get_overrides(method_class_info, func.attr)
            if overrides:
                return [(location, False)] + [(each, False) for each in overrides]
            return [(location, True)]

        # A call via a module or a class
        root = func.value
        while isinstance(root, ast.Attribute):
            root = root.value
        if isinstance(root, ast.Name) and root.id not in local_names:
            base = resolver.resolve_expression(module_name, func.value)
            if base is not None:
                if base[0] == "external":
                    return []
                result = resolver.resolve_attribute(base, func.attr)
                if result is not None:
                    return _get_certain_callees(result)
                if base[0] in ("module", "package", "class"):
                    return []

        # A call of a method of an object of unknown type
        return [
            (location, False)
            for location in resolver.method_locations_by_name.get(func.attr, [])
        ]


def _get_certain_callees(resolved: T.Optional[T.Tuple]) -> T.List[T.Tuple[str, bool]]:
    if resolved is None:
        return []
    if resolved[0] == "function":
        return [(resolved[1], True)]
    if resolved[0] == "class":
        # A call of a class is a call of its __init__ method
        class_info = resolved[1]
        if "__init__" in class_info.method_names:
            return [(_method_location(class_info, "__init__"), True)]
    return []


def _find_calls(node: ast.AST) -> T.Iterator[ast.Call]:
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            yield child


def _get_local_names(function_def) -> T.Set[str]:
    # The parameters, local variables and nested functions of the function
    names = set()
    for node in ast.walk(function_def):
        if isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif (
            isinstance(node, (*_FUNCTION_DEFS, ast.ClassDef))
            and node is not function_def
        ):
            names.add(node.name)
    return names
