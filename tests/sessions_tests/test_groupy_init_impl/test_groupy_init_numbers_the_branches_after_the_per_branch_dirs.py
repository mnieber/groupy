from sessions_tests.groupy_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_init_numbers_the_branches_after_the_per_branch_dirs(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package. The .groupy dir has the
    # per-branch dir of groupy-7 (a branch that no longer exists), and the
    # per-branch dir of a branch with a name of the developer.
    if env.step(
        env.create_repo_with_target_code(),
        env.make_per_branch_dir("groupy-7"),
        env.make_per_branch_dir("refactor-myapp"),
    ):
        assert env.git_status() == ""

    # We run groupy init without a branch name.
    #
    # The highest number of the groupy-<N> dirs is 7, so the branch should be
    # groupy-8. The dir of refactor-myapp should not count.
    if env.step(
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
    ):
        assert env.git_branch() == "groupy-8"
        assert env.file_exists(".groupy/groupy-8")


class Env(TestEnv):
    def make_per_branch_dir(self, branch_name: str) -> None:
        """Makes the per-branch dir of a branch, with a log in it."""
        self.write_file(f".groupy/{branch_name}/logs/request.jsonl", "")

