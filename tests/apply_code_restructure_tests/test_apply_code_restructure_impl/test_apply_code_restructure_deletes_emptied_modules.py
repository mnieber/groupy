from apply_code_restructure_tests.apply_code_restructure_test_env import (
    Context,
    TestEnv,
)
from breaker.nodes.actions.set_code_unit_type import set_code_unit_type
from breaker.nodes.actions.set_move_to_file import set_move_to_file

HELPERS = "myapp/reports/helpers.py"
FORMAT_TITLE = "myapp/reports/utils/format_title.py"
FORMAT_NAME = "myapp/reports/utils/format_name.py"

HELPERS_PY = """\
def format_title(title):
    return title.title()


def format_name(name):
    return name.strip()
"""


def create_env(context: Context):
    return Env(context)


def test_apply_code_restructure_deletes_emptied_modules(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-code-restructure, with a valid proposal for the modules of the
    # base env. Besides the modules of the base env, myapp has
    # myapp/reports/helpers.py, whose functions move to their own util files.
    if env.step(
        env.create_session_at_apply_code_restructure({HELPERS: HELPERS_PY}),
        env.edit_node_file(set_code_unit_type, HELPERS, "format_title", "util"),
        env.edit_node_file(set_move_to_file, HELPERS, "format_title", FORMAT_TITLE),
        env.edit_node_file(set_code_unit_type, HELPERS, "format_name", "util"),
        env.edit_node_file(set_move_to_file, HELPERS, "format_name", FORMAT_NAME),
        env.commit_all("propose the code restructure"),
    ):
        pass

    # We run breaker next.
    #
    # helpers.py has no code left, so Breaker should have deleted it,
    # together with its node file.
    if env.step(
        env.run_breaker_next(),
    ):
        assert not env.module_exists(HELPERS)
        assert not env.file_exists(f"src/{HELPERS}.breaker.yaml")
        assert env.top_level_names(FORMAT_TITLE) == ["format_title"]
        assert env.top_level_names(FORMAT_NAME) == ["format_name"]

    # We look at the package node file of myapp/reports and the group file.
    #
    # helpers.py should be removed from both, and the new modules should be in
    # the group of helpers.py.
    if env.step(
        env.load_package_node("myapp/reports"),
        env.load_groups(),
    ):
        assert env.package_node.module_names == []
        assert HELPERS not in sum(env.module_names_per_group(), [])
        assert env.group_of(FORMAT_TITLE) == 3
        assert env.group_of(FORMAT_NAME) == 3


class Env(TestEnv):
    pass
