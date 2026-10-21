from exclude_tests.exclude_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_init_excludes_part_of_the_target_code(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package in the src dir, which contains
    # the books module, the chapters package and the reports package.
    if env.step(
        env.create_repo_with_reports(),
    ):
        pass

    # We run groupy init, and exclude the reports package and the legacy
    # module (which doesn't exist).
    #
    # The session file should contain both patterns, in the order in which
    # they were given. A pattern that matches no file is accepted.
    if env.step(
        env.run_groupy(
            "init",
            "--accept-risks",
            "--target-dir=src",
            "--exclude=myapp/reports/**",
            "--exclude=myapp/legacy.py",
        ),
        env.load_session(),
    ):
        assert env.session.exclude == ["myapp/reports/**", "myapp/legacy.py"]

    # We look at the node files.
    #
    # The passive modules should have node files too, since the call graph and
    # the context of the Claude requests cover all files.
    if env.step():
        assert "src/myapp/reports/summary.py.groupy.yaml" in env.node_file_paths()
        assert "src/myapp/reports/package-node.groupy.yaml" in env.node_file_paths()

    # We run the first stage (group-modules), and load the group file.
    #
    # The group file should list the passive modules too, so that the chunk
    # ids do not depend on the exclude patterns.
    if env.step(
        env.run_groupy("next"),
        env.load_groups(),
    ):
        assert env.grouped_module_names() == {
            "myapp/__init__.py",
            "myapp/books.py",
            "myapp/chapters/__init__.py",
            "myapp/chapters/create_chapter.py",
            "myapp/reports/__init__.py",
            "myapp/reports/summary.py",
        }

    # We load the active modules, as the next stage does when it starts.
    #
    # The modules in the reports package should be passive, and the other
    # modules active.
    if env.step(
        env.load_active_module_names(),
    ):
        assert env.active_module_names == [
            "myapp/__init__.py",
            "myapp/books.py",
            "myapp/chapters/__init__.py",
            "myapp/chapters/create_chapter.py",
        ]


class Env(TestEnv):
    pass
