import inspect
import typing as T
from pathlib import Path

from groupy.call_graph.rules.get_callees import get_callees
from groupy.call_graph.rules.get_callers import get_callers
from groupy.claude_requests.actions.run_callback import GLOSSARY_EDITS, NODE_EDITS
from groupy.functions.actions.commit_refactoring import commit_refactoring
from groupy.functions.actions.extract_method import extract_method
from groupy.functions.rules.get_source import get_source

PREAMBLE = """\
## How to work with Groupy

You help Groupy, a tool that refactors the Python code in this repository. This is
the request {request_id}. The code that Groupy refactors (the target code) is in the
dir {target_dir}, and the node file of each module (e.g. books.py.groupy.yaml) is
next to the module.

Read the context of the request first: {context_path} (yaml).

{change_rule}

Run each callback with the Bash tool, as a single command of exactly this form:

    groupy callback <name> --args '<json object with the arguments>'

For example:

    groupy callback add_responsibility --args '{{"module_name": "myapp/books.py", "location": "create_book", "responsibility": "Creates a book"}}'

- module_name is the path of a module, relative to the target dir (e.g.
  myapp/books.py is the file {target_dir}/myapp/books.py).
- location identifies a node in the node file of the module: @module for the module
  itself, create_book for a function, Book for a class, Book.save for a method,
  MAX_CHAPTERS for a module-level variable, and create_report._format_lines for a
  helper function of create_report. A function that is nested in another function
  (an embedded function) has no node: don't make callbacks for it. A location in
  the context of the form <module_name>:<location> (e.g. myapp/books.py:create_book)
  has these two parts; the queries get_callers, get_callees and get_source take
  such a full location.
- Pass every argument that has no default value. Pass null for an empty value
  (e.g. an empty description).
- A callback prints its result as yaml, or OK.
- When a callback fails, you may correct the call and retry it once. When the retry
  fails too, Groupy tells you to stop. Then stop at once: don't run more callbacks,
  don't edit files, and end your answer.

The callbacks are:

{callbacks}

When you are done, end your answer with a short summary.
"""

RFA_CHANGE_RULE = """\
Don't edit any files yourself: make all changes with the callbacks of Groupy."""

RFR_CHANGE_RULE = """\
Edit the source files directly (with the Edit tool), but change the node files
(*.groupy.yaml) only with the callbacks of Groupy."""


def get_preamble(
    request_id: str, context_path: Path, target_dir: Path, in_rfr: bool
) -> str:
    # Explains Claude how to read the context and how to run callbacks
    callbacks = [
        _describe(get_callers),
        _describe(get_callees),
        _describe(get_source),
        _describe(commit_refactoring) if in_rfr else _describe(extract_method),
        *[_describe(action) for action in NODE_EDITS.values()],
        *[_describe(action) for action in GLOSSARY_EDITS.values()],
    ]
    return PREAMBLE.format(
        request_id=request_id,
        target_dir=target_dir.as_posix(),
        context_path=context_path.as_posix(),
        change_rule=RFR_CHANGE_RULE if in_rfr else RFA_CHANGE_RULE,
        callbacks="\n".join(f"- {callback}" for callback in callbacks),
    )


def _describe(function: T.Callable) -> str:
    # The arguments that Groupy supplies (e.g. the source root) are left out
    supplied_names = ("source_root", "glossary_path", "call_graph", "rfr_policy")
    parameters = [
        _describe_parameter(parameter)
        for parameter in inspect.signature(function).parameters.values()
        if parameter.name not in supplied_names
    ]
    return f"{function.__name__}({', '.join(parameters)})"


def _describe_parameter(parameter: inspect.Parameter) -> str:
    text = parameter.name
    if parameter.annotation is not inspect.Parameter.empty:
        text += f": {inspect.formatannotation(parameter.annotation)}"
    if parameter.default is not inspect.Parameter.empty:
        text += f" = {parameter.default!r}"
    return text
