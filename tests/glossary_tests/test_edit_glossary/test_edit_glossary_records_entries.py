from glossary_tests.glossary_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_edit_glossary_records_entries(context: Context):
    # Create the test environment
    env = create_env(context)

    # There is no glossary file yet. We add an entry for "title", and two
    # entries for "report", which has two meanings.
    #
    # The glossary should have an entry per meaning, sorted by name.
    if env.step(
        env.add_glossary_entry("title", "the name of a book"),
        env.add_glossary_entry(
            "report",
            "a markdown document with the statistics of a user",
        ),
        env.add_glossary_entry("report", "an error report that is sent to Sentry"),
        env.load_glossary(),
    ):
        assert env.names() == ["report", "report", "title"]
        assert env.descriptions("report") == [
            "a markdown document with the statistics of a user",
            "an error report that is sent to Sentry",
        ]

    # We change the description of "title", and add two aliases and an
    # abbreviation.
    #
    # The entry should hold the new description, the aliases and the
    # abbreviation.
    if env.step(
        env.set_glossary_description("title", "the name on the cover of a book"),
        env.add_glossary_alias("title", "name"),
        env.add_glossary_alias("title", "book_title"),
        env.set_glossary_abbreviation("title", "ttl"),
        env.load_glossary(),
    ):
        title = env.entry("title")
        assert title.description == "the name on the cover of a book"
        assert title.aliases == ["name", "book_title"]
        assert title.abbreviation == "ttl"

    # We add an entry for "heading" with an alias and an abbreviation, and
    # merge it into "title".
    #
    # The entry for "heading" should be gone, and its name and alias should be
    # aliases of "title". The description and the abbreviation of "title"
    # should be unchanged.
    if env.step(
        env.add_glossary_entry("heading", "the name of a book"),
        env.add_glossary_alias("heading", "caption"),
        env.set_glossary_abbreviation("heading", "hdg"),
        env.merge_glossary_entries("heading", "title"),
        env.load_glossary(),
    ):
        title = env.entry("title")
        assert env.names() == ["report", "report", "title"]
        assert title.aliases == ["name", "book_title", "heading", "caption"]
        assert title.description == "the name on the cover of a book"
        assert title.abbreviation == "ttl"

    # We remove the abbreviation of "title". Then we add an entry for "label"
    # with an abbreviation, and merge it into "title".
    #
    # Since "title" has no abbreviation, it should get the abbreviation of
    # "label".
    if env.step(
        env.set_glossary_abbreviation("title", None),
        env.load_glossary(),
    ):
        assert env.entry("title").abbreviation is None

    if env.step(
        env.add_glossary_entry("label", "the name of a book"),
        env.set_glossary_abbreviation("label", "lbl"),
        env.merge_glossary_entries("label", "title"),
        env.load_glossary(),
    ):
        title = env.entry("title")
        assert env.names() == ["report", "report", "title"]
        assert title.aliases == ["name", "book_title", "heading", "caption", "label"]
        assert title.abbreviation == "lbl"


class Env(TestEnv):
    pass
