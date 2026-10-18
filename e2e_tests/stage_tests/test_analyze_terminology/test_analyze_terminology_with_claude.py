from stage_tests.e2e_test_env import Context, TestEnv

CUSTOMERS = "myapp/customers.py"

CUSTOMERS_PY = """\
def register_customer(customers, name):
    customers.append({"name": name})
    return customers


def find_client(customers, name):
    return next(client for client in customers if client["name"] == name)
"""


def create_env(context: Context):
    return Env(context)


def test_analyze_terminology_with_claude(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses Claude, whose next stage is
    # analyze-terminology. The module customers.py uses client as an alias of
    # customer. Haiku uses activities (e.g. book counting) as concepts, and
    # misuses the glossary callbacks, so this test uses Sonnet.
    if env.step(
        env.create_session_with_claude(
            {CUSTOMERS: CUSTOMERS_PY}, claude_model="sonnet"
        ),
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

    # We look at the node file of customers.py and at the glossary.
    #
    # The module should have concepts, and every function responsibilities
    # and steps. The glossary should have an entry for the concept of a
    # customer. Claude should have recorded client as an alias (in the node
    # files or in the glossary).
    if env.step(
        env.load_module_node(CUSTOMERS),
        env.load_glossary(),
    ):
        assert env.module_node.concepts
        for node in env.all_function_nodes():
            assert node.responsibilities, f"{node.name} has no responsibilities"
            assert node.steps, f"{node.name} has no steps"
        assert env.glossary_names() & {"customer", "customers"}
        assert "client" in env.node_aliases() | env.glossary_aliases()


class Env(TestEnv):
    def node_aliases(self):
        """Returns the aliases in the function nodes of env.module_node."""
        return {
            alias
            for node in self.all_function_nodes()
            for aliases in node.aliases.values()
            for alias in aliases
        }

    def glossary_aliases(self):
        return {alias for entry in self.glossary.entries for alias in entry.aliases}
