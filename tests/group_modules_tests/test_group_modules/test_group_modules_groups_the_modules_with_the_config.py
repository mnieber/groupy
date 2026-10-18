from sessions_tests.groupy_test_env import Context, TestEnv

CONFIG_YAML = """\
grouping_strategy: simple
max_group_lines: 10000
"""


def create_env(context: Context):
    return Env(context)


def test_group_modules_groups_the_modules_with_the_config(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo without a config file, and we run groupy init.
    #
    # It should not create the group file, since grouping is the first stage.
    if env.step(
        env.create_repo_with_target_code(),
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
        env.load_session(),
    ):
        assert env.session.next_stage == "group-modules"
        assert not env.file_exists(".groupy/groups.txt")

    # We change the config file that groupy init wrote to the simple grouping
    # strategy with large groups, commit it, and run groupy next.
    #
    # The stage should create the group file with the strategy of the config
    # file, commit it, and finish.
    if env.step(
        env.write_file(".groupy/config.yaml", CONFIG_YAML),
        env.commit_all("use the simple grouping strategy"),
        env.remember_git_head(),
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.commit_messages_since_remembered_head() == [
            "group-modules: create the group file",
            "group-modules: finish the stage",
        ]
        assert env.git_status() == ""
        assert env.session.next_stage == "identify-helper-functions"

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
    def commit_messages_since_remembered_head(self):
        log = self._git(
            "log", "--reverse", "--format=%s", f"{self.remembered_git_head}..HEAD"
        )
        return log.splitlines()
