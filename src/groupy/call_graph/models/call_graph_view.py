import typing as T

from dataclassy import dataclass
from groupy.call_graph.enums import CallScopes


@dataclass
class CallView:
    location: str
    scope: CallScopes
    is_certain: bool
    responsibility: T.Optional[str] = None


@dataclass
class FunctionView:
    location: str
    callers: T.List[CallView] = []
    callees: T.List[CallView] = []
    caller_summary: T.Optional[str] = None


@dataclass
class CallGraphView:
    function_views: T.List[FunctionView] = []
