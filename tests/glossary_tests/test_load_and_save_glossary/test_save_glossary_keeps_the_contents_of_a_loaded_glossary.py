from glossary_tests.glossary_test_env import Context, TestEnv

# A glossary in the format that Groupy writes: the entries are sorted by name,
# and fields that have their default value are left out.
GLOSSARY_YAML = """\
- name: report
  description: a markdown document with the statistics of a user
- name: report
  description: an error report that is sent to Sentry
  aliases: [error_doc]
- name: title
  description: the name of a book
  aliases: [name, book_title]
  abbreviation: ttl
"""


def create_env(context: Context):
    return Env(context)


def test_save_glossary_keeps_the_contents_of_a_loaded_glossary(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a glossary with two entries for "report" (one per meaning), and
    # an entry for "title" with aliases and an abbreviation.
    if env.step(
        env.write_glossary(GLOSSARY_YAML),
    ):
        pass

    # We load the glossary.
    #
    # It should have an entry per meaning, in the order of the file.
    if env.step(
        env.load_glossary(),
    ):
        assert env.names() == ["report", "report", "title"]
        assert env.descriptions("report") == [
            "a markdown document with the statistics of a user",
            "an error report that is sent to Sentry",
        ]
        assert env.entry("report", meaning_nr=1).aliases == []
        assert env.entry("report", meaning_nr=2).aliases == ["error_doc"]
        assert env.entry("report", meaning_nr=2).abbreviation is None
        assert env.entry("title").aliases == ["name", "book_title"]
        assert env.entry("title").abbreviation == "ttl"

    # We save the glossary to another file.
    #
    # The file should have the same contents as the original file.
    if env.step(
        env.save_glossary("copy.groupy.yaml"),
    ):
        assert env.read_file("copy.groupy.yaml") == GLOSSARY_YAML


class Env(TestEnv):
    pass
