from exclude_tests.exclude_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_init_without_exclude_keeps_every_module_active(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package in the src dir, and we run
    # groupy init without --exclude.
    #
    # The session file should have no exclude patterns.
    if env.step(
        env.create_repo_with_reports(),
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
        env.load_session(),
    ):
        assert env.session.exclude == []

    # We load the active modules.
    #
    # Without patterns, every module should be active.
    if env.step(
        env.load_active_module_names(),
    ):
        assert env.exclude_patterns == []
        assert env.active_module_names == [
            "myapp/__init__.py",
            "myapp/books.py",
            "myapp/chapters/__init__.py",
            "myapp/chapters/create_chapter.py",
            "myapp/reports/__init__.py",
            "myapp/reports/summary.py",
        ]


class Env(TestEnv):
    pass
