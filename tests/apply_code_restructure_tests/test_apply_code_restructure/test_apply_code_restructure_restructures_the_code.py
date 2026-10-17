from apply_code_restructure_tests.apply_code_restructure_test_env import (
    BOOK,
    BOOKS,
    CREATE_BOOK,
    CREATE_CHAPTER,
    NEW_CREATE_CHAPTER,
    Context,
    TestEnv,
)
from breaker.functions.actions.add_responsibility import add_responsibility
from breaker.nodes.actions.set_code_unit_type import set_code_unit_type
from breaker.nodes.actions.set_move_to_file import set_move_to_file
from breaker.nodes.actions.set_rename_to import set_rename_to

REPORT = "myapp/reports/report.py"
CREATE_REPORT = "myapp/reports/actions/create_report.py"
REPORT_MODEL = "myapp/reports/models/report.py"
RENDER_REPORT = "myapp/reports/rules/render_report.py"

REPORT_PY = """\
class Report:
    def __init__(self, title):
        self.title = title

    def render(self):
        return "# " + self.title


def create_report(title):
    return Report(title).render()
"""


def create_env(context: Context):
    return Env(context)


def test_apply_code_restructure_restructures_the_code(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-code-restructure, with a valid proposal for the modules of the
    # base env (books.py becomes the file of the action create_book, and Book
    # moves to its own model file). Besides the modules of the base env,
    # myapp has myapp/reports/report.py. Its proposal: the module becomes the
    # file of the action create_report, the model Report moves to its own
    # file, and its method render delegates to the rule render_report.
    if env.step(
        env.create_session_at_apply_code_restructure({REPORT: REPORT_PY}),
        env.edit_node_file(set_rename_to, REPORT, "@module", CREATE_REPORT),
        env.edit_node_file(set_code_unit_type, REPORT, "create_report", "action"),
        env.edit_node_file(set_code_unit_type, REPORT, "Report", "model"),
        env.edit_node_file(set_move_to_file, REPORT, "Report", REPORT_MODEL),
        env.edit_node_file(set_code_unit_type, REPORT, "Report.render", "rule"),
        env.edit_node_file(set_move_to_file, REPORT, "Report.render", RENDER_REPORT),
        env.edit_node_file(
            add_responsibility, REPORT, "Report.render", "Renders the report"
        ),
        env.commit_all("propose the code restructure"),
        env.remember_git_head(),
    ):
        pass

    # We run breaker next.
    #
    # Breaker should have validated the proposal (which follows the
    # dependency direction), restructured the modules one by one, and
    # finished the chunks and the stage.
    if env.step(
        env.run_breaker_next(),
    ):
        assert env.commit_messages_since_remembered_head() == [
            "apply-code-restructure: restructure myapp/books.py",
            "apply-code-restructure: finish group-1/chunk-1",
            "apply-code-restructure: restructure myapp/chapters/create_chapter.py",
            "apply-code-restructure: finish group-2/chunk-1",
            "apply-code-restructure: restructure myapp/reports/report.py",
            "apply-code-restructure: finish group-3/chunk-1",
            "apply-code-restructure: finish the stage",
        ]
        assert env.git_status() == ""
        assert env.output_lines == [
            "The proposed code structure follows the dependency direction."
        ]

    # We look at the modules of myapp/books.
    #
    # books.py should be renamed to the file of create_book, and Book should
    # have moved to its own file, which create_book imports. The new packages
    # should have an __init__.py.
    if env.step():
        assert not env.module_exists(BOOKS)
        assert env.top_level_names(CREATE_BOOK) == [
            "MAX_CHAPTERS",
            "create_book",
            "_normalize_title",
        ]
        assert env.imported_names(CREATE_BOOK) == {"myapp.books.models.book": ["Book"]}
        assert env.top_level_names(BOOK) == ["Book"]
        for package_name in [
            "myapp/books",
            "myapp/books/actions",
            "myapp/books/models",
        ]:
            assert env.module_exists(f"{package_name}/__init__.py")
        assert not env.module_exists(CREATE_CHAPTER)
        assert env.top_level_names(NEW_CREATE_CHAPTER) == ["create_chapter"]
        assert env.python_files_that_do_not_parse() == []

    # We look at the modules of myapp/reports.
    #
    # The method render should delegate to the new rule render_report, which
    # it imports locally (to avoid a circular import). The rule should take
    # the report as its first argument.
    if env.step():
        assert env.top_level_names(CREATE_REPORT) == ["create_report"]
        assert env.top_level_names(REPORT_MODEL) == ["Report"]
        assert env.function_source(REPORT_MODEL, "Report.render") == (
            "def render(self):\n"
            "    from myapp.reports.rules.render_report import render_report\n"
            "    return render_report(self)"
        )
        assert env.function_source(RENDER_REPORT, "render_report") == (
            'def render_report(report):\n    return "# " + report.title'
        )

    # We look at the node files of myapp/books.
    #
    # The node files should follow the code: the renamed module keeps its
    # node file (with the helper function of create_book), and the moved node
    # is in the node file of its new module. The proposal fields should be
    # cleared, but the code_unit_type should be kept.
    if env.step(
        env.load_module_node(CREATE_BOOK),
    ):
        assert not env.file_exists(f"src/{BOOKS}.breaker.yaml")
        assert env.module_node.name == CREATE_BOOK
        assert env.module_node.rename_to is None
        assert env.names(env.module_node.function_nodes) == ["create_book"]
        assert env.names(env.function_node("create_book").helper_function_nodes) == [
            "_normalize_title"
        ]
        assert env.names(env.module_node.class_nodes) == []
        assert env.names(env.module_node.variable_nodes) == ["MAX_CHAPTERS"]

    if env.step(
        env.load_module_node(BOOK),
    ):
        assert env.class_node("Book").code_unit_type == "model"
        assert env.class_node("Book").move_to_file is None

    # We look at the node files of myapp/reports.
    #
    # The rule render_report should have the analysis of the method render,
    # and the node of the method should say that it delegates.
    if env.step(
        env.load_module_node(RENDER_REPORT),
    ):
        render_report_node = env.function_node("render_report")
        assert render_report_node.code_unit_type == "rule"
        assert render_report_node.responsibilities == ["Renders the report"]

    if env.step(
        env.load_module_node(REPORT_MODEL),
    ):
        render_node = env.function_node("Report.render")
        assert render_node.responsibilities == ["Delegates to render_report"]
        assert render_node.code_unit_type is None
        assert render_node.move_to_file is None

    # We look at the package node files and the group file.
    #
    # The new packages should have a package node file, and the modules
    # should keep the group of the module that their code came from.
    if env.step(
        env.load_package_node("myapp/books/actions"),
        env.load_groups(),
    ):
        assert env.package_node.module_names == [
            "myapp/books/actions/__init__.py",
            "myapp/books/actions/create_book.py",
        ]
        assert env.group_of(CREATE_BOOK) == 1
        assert env.group_of(BOOK) == 1
        assert env.group_of(NEW_CREATE_CHAPTER) == 2
        assert env.group_of(RENDER_REPORT) == 3

    # We look at the session, and run breaker next again.
    #
    # The next stage should be done, so breaker next should only report
    # that the refactoring is done.
    if env.step(
        env.load_session(),
        env.remember_git_head(),
        env.run_breaker_next(),
    ):
        assert env.session.next_stage == "done"
        assert env.output_lines == ["The refactoring is done."]
        assert env.commit_messages_since_remembered_head() == []


class Env(TestEnv):
    pass
