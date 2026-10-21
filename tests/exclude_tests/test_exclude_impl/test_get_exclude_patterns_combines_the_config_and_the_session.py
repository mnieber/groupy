from exclude_tests.exclude_test_env import Context, TestEnv

CONFIG_YAML = """\
exclude:
  - myapp/chapters/**
"""


def create_env(context: Context):
    return Env(context)


def test_get_exclude_patterns_combines_the_config_and_the_session(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with a config file that excludes the chapters package,
    # and we run groupy init, which keeps the existing config file, and exclude
    # the reports package.
    if env.step(
        env.create_repo_with_reports(),
        env.write_file(".groupy/config.yaml", CONFIG_YAML),
        env.commit_all("add the config file"),
        env.run_groupy(
            "init", "--accept-risks", "--target-dir=src", "--exclude=myapp/reports/**"
        ),
    ):
        pass

    # We load the active modules.
    #
    # The patterns should be the union of the patterns in the config file and
    # in the session file.
    if env.step(
        env.load_active_module_names(),
    ):
        assert set(env.exclude_patterns) == {"myapp/chapters/**", "myapp/reports/**"}
        assert env.active_module_names == ["myapp/__init__.py", "myapp/books.py"]

    # The developer replaces the exclude patterns in the session file, and we
    # load the active modules again (as the next stage does when it starts).
    #
    # The change should take effect: the reports package is active again, and
    # the books module is passive.
    if env.step(
        env.set_session_exclude("myapp/books.py"),
        env.load_active_module_names(),
    ):
        assert set(env.exclude_patterns) == {"myapp/chapters/**", "myapp/books.py"}
        assert env.active_module_names == [
            "myapp/__init__.py",
            "myapp/reports/__init__.py",
            "myapp/reports/summary.py",
        ]


class Env(TestEnv):
    pass
