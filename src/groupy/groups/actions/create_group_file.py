from pathlib import Path

from groupy.groups.actions.save_group_file import save_group_file
from groupy.groups.rules.create_package_groups import create_package_groups
from groupy.groups.rules.create_simple_groups import create_simple_groups
from groupy.sessions.models.config import Config


def create_group_file(source_root: Path, config: Config, group_file_path: Path) -> None:
    if config.grouping_strategy == "simple":
        groups = create_simple_groups(source_root, config.max_group_lines)
    elif config.grouping_strategy == "package":
        groups = create_package_groups(source_root)
    else:
        raise UnsupportedGroupingStrategyError(
            f"The grouping strategy {config.grouping_strategy} is not supported"
        )
    save_group_file(groups, group_file_path)


class UnsupportedGroupingStrategyError(Exception):
    pass
