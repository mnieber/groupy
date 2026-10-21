from sessions_tests.groupy_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_init_keeps_the_per_branch_files_out_of_git(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package, and we run groupy init.
    if env.step(
        env.create_repo_with_target_code(),
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
    ):
        assert env.git_branch() == "groupy-1"

    # We write files into the per-branch dir, as groupy next does.
    #
    # The per-branch dir is excluded from git, so the working tree should
    # stay clean.
    if env.step(
        env.write_file(".groupy/groupy-1/last-run.yaml", "result: finished\n"),
        env.write_file(".groupy/groupy-1/logs/group-modules.jsonl", "{}\n"),
    ):
        assert env.git_status() == ""

    # We go back to main, and run groupy init again.
    #
    # The per-branch dir of groupy-1 should still be there (it is not
    # committed, so it is not removed by the checkout), and the working tree
    # should be clean. The exclude line should be in the exclude file only
    # once.
    if env.step(
        env.run_git("checkout", "main"),
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
    ):
        assert env.git_branch() == "groupy-2"
        assert env.file_exists(".groupy/groupy-1/last-run.yaml")
        assert env.git_status() == ""
        assert env.git_ignores().count("/.groupy/*/") == 1

    # We look at the committed groupy files.
    #
    # The session file and the config file are not in a dir, so they should
    # still be committed.
    if env.step():
        assert {".groupy/session.yaml", ".groupy/config.yaml"} <= env.tracked_files()


class Env(TestEnv):
    def tracked_files(self):
        return set(self._git("ls-files").splitlines())
