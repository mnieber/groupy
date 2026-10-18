from sessions_tests.groupy_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_group_modules_uses_the_package_strategy_by_default(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo without a config file. We run groupy init, and then
    # groupy next, without changing the config file.
    if env.step(
        env.create_repo_with_target_code(),
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
        env.run_groupy("next"),
        env.load_groups(),
    ):
        pass

    # We look at the group file.
    #
    # It should use the default grouping strategy (package), so the modules of
    # myapp and of myapp/chapters should be in different groups.
    if env.step():
        assert env.module_names_per_group() == [
            ["myapp/__init__.py", "myapp/books.py"],
            ["myapp/chapters/__init__.py", "myapp/chapters/create_chapter.py"],
        ]


class Env(TestEnv):
    pass
