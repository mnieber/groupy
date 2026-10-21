from exclude_tests.exclude_test_env import Context, TestEnv

# summary.py after the developer added the print_summary function
SUMMARY_PY = """\
from myapp.books import create_book


def summarize(title):
    return create_book(title).title


def print_summary(title):
    print(summarize(title))
"""


def create_env(context: Context):
    return Env(context)


def test_groupy_sync_updates_the_passive_node_files(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that excludes the reports package, and we have run its
    # first stage (group-modules).
    if env.step(
        env.create_repo_with_reports(),
        env.run_groupy(
            "init", "--accept-risks", "--target-dir=src", "--exclude=myapp/reports/**"
        ),
        env.run_groupy("next"),
    ):
        pass

    # The developer adds a function to the passive summary module, and we run
    # groupy sync.
    #
    # Groupy sync operates on all files, so the node file of the summary module
    # should list the new function.
    if env.step(
        env.write_file("src/myapp/reports/summary.py", SUMMARY_PY),
        env.commit_all("add print_summary"),
        env.run_groupy("sync"),
        env.load_module_node("myapp/reports/summary.py"),
    ):
        assert env.function_names() == ["summarize", "print_summary"]


class Env(TestEnv):
    def function_names(self):
        return self.names(self.module_node.function_nodes)
