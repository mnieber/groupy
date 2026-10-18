from stage_tests.e2e_test_env import Context, TestEnv

SHELVES_PY = """\
def add_volume(shelf, volume, qty):
    for _ in range(qty):
        shelf.append(volume)
    return shelf


def count_books(shelf, book):
    return sum(1 for item in shelf if item == book)
"""


def create_env(context: Context):
    return Env(context)


def test_analyze_terminology_with_claude(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses Claude, whose next stage is
    # analyze-terminology. The module shelves.py uses volume as an alias of
    # book, and qty as an abbreviation of quantity.
    if env.step(
        env.create_session_with_claude({"myapp/shelves.py": SHELVES_PY}),
        env.set_next_stage("analyze-terminology"),
    ):
        pass

    # We run groupy next.
    #
    # Claude should have answered the RFA of the chunk and the RFA that
    # consolidates the glossary, so that the stage finished (which also means
    # that every node has an extract_method_priority) with a clean working
    # tree.
    if env.step(
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.session.next_stage == "propose-renamings"
        assert env.git_status() == ""

    # We look at the node file of shelves.py.
    #
    # The module should have concepts, and every function responsibilities
    # and steps. Claude should have recorded volume as an alias, and qty as an
    # abbreviation.
    if env.step(
        env.load_module_node("myapp/shelves.py"),
    ):
        assert env.module_node.concepts
        for node in env.all_function_nodes():
            assert node.responsibilities, f"{node.name} has no responsibilities"
            assert node.steps, f"{node.name} has no steps"
        assert "volume" in env.node_aliases()
        assert "qty" in env.node_abbreviations()

    # We look at the glossary.
    #
    # It should have an entry for the concept of a book (or volume).
    if env.step(
        env.load_glossary(),
    ):
        assert env.glossary_names() & {"book", "books", "volume"}


class Env(TestEnv):
    def node_aliases(self):
        """Returns the aliases in the function nodes of env.module_node."""
        return {
            alias
            for node in self.all_function_nodes()
            for aliases in node.aliases.values()
            for alias in aliases
        }

    def node_abbreviations(self):
        """Returns the abbreviations in the function nodes of
        env.module_node."""
        return {
            abbreviation
            for node in self.all_function_nodes()
            for abbreviation in node.abbreviations.values()
        }
