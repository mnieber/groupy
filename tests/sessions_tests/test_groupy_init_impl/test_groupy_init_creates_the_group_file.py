from sessions_tests.groupy_test_env import Context, TestEnv

CONFIG_YAML = """\
grouping_strategy: simple
max_group_lines: 10000
"""


def create_env(context: Context):
    return Env(context)


def test_groupy_init_creates_the_group_file(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo without a config file, and we run groupy init.
    if env.step(
        env.create_repo_with_target_code(),
        env.run_groupy("init", "--target-dir=src"),
    ):
        assert ".groupy/groups.txt" in env.files_in_head_commit()

    # We load the group file.
    #
    # It should use the default grouping strategy (package), so the modules of
    # myapp and of myapp/chapters should be in different groups.
    if env.step(
        env.load_groups(),
    ):
        assert env.module_names_per_group() == [
            ["myapp/__init__.py", "myapp/books.py"],
            ["myapp/chapters/__init__.py", "myapp/chapters/create_chapter.py"],
        ]


def test_groupy_init_creates_the_group_file_from_the_config(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with a committed config file that sets the simple
    # grouping strategy with large groups, and we run groupy init.
    if env.step(
        env.create_repo_with_target_code(),
        env.write_file(".groupy/config.yaml", CONFIG_YAML),
        env.commit_all("add groupy config"),
        env.run_groupy("init", "--target-dir=src"),
    ):
        pass

    # We load the group file.
    #
    # All modules should be in a single group.
    if env.step(
        env.load_groups(),
    ):
        assert env.module_names_per_group() == [
            [
                "myapp/__init__.py",
                "myapp/books.py",
                "myapp/chapters/__init__.py",
                "myapp/chapters/create_chapter.py",
            ]
        ]


class Env(TestEnv):
    pass
