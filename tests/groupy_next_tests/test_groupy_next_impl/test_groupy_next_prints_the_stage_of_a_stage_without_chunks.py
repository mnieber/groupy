from groupy_next_tests.groupy_next_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_next_prints_the_stage_of_a_stage_without_chunks(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package and a config file with the
    # simple grouping strategy, and we run groupy init.
    if env.step(
        env.create_repo_with_target_code(),
        env.write_file(".groupy/config.yaml", "grouping_strategy: simple\n"),
        env.commit_all("add groupy config"),
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
    ):
        pass

    # We run groupy next, which runs group-modules (a stage without chunks).
    #
    # Groupy should have printed a single progress message on stderr, with the
    # id of the stage.
    if env.step(
        env.run_groupy_next(),
    ):
        assert env.error_lines == ["group-modules"]


class Env(TestEnv):
    pass
