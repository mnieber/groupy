import typing as T

import yaml


class FlowList(list):
    # A list that is written on one line, e.g. [name, book_title]
    pass


class _Dumper(yaml.SafeDumper):
    # Indents list items below their key, instead of aligning them with the key
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


_Dumper.add_representer(
    FlowList,
    lambda dumper, data: dumper.represent_sequence(
        "tag:yaml.org,2002:seq", data, flow_style=True
    ),
)


def dump_yaml(data: T.Any) -> str:
    return yaml.dump(
        data, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=1000
    )
