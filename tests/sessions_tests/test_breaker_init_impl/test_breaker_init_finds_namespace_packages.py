from sessions_tests.breaker_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_breaker_init_finds_namespace_packages(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package in the src dir. We add:
    # - a module directly in the src dir,
    # - the tools dir, which has modules but no __init__.py,
    # - the plugins dir, which only has modules in its export sub-dir,
    # - the assets dir, which has no Python modules.
    if env.step(
        env.create_repo_with_target_code(),
        env.write_file("src/manage.py", "import myapp\n"),
        env.write_file("src/tools/lint.py", "RULES = []\n"),
        env.write_file("src/plugins/export/to_pdf.py", "FORMAT = 'pdf'\n"),
        env.write_file("src/assets/logo.svg", "<svg></svg>\n"),
        env.commit_all("add tools, plugins and assets"),
    ):
        pass

    # We run breaker init.
    #
    # Every dir that contains Python modules, directly or in a sub-dir, should
    # have a package node file, whether or not it has an __init__.py.
    if env.step(
        env.run_breaker("init", "--target-dir=src"),
    ):
        assert env.package_node_file_paths() == {
            # The target dir is the root package.
            "src/package-node.breaker.yaml",
            "src/myapp/package-node.breaker.yaml",
            "src/myapp/chapters/package-node.breaker.yaml",
            "src/tools/package-node.breaker.yaml",
            "src/plugins/package-node.breaker.yaml",
            "src/plugins/export/package-node.breaker.yaml",
        }
        assert env.file_exists("src/manage.py.breaker.yaml")
        assert env.file_exists("src/tools/lint.py.breaker.yaml")
        assert env.file_exists("src/plugins/export/to_pdf.py.breaker.yaml")


class Env(TestEnv):
    # Queries (for use in asserts)

    def package_node_file_paths(self):
        return {
            path
            for path in self.node_file_paths()
            if path.endswith("package-node.breaker.yaml")
        }
