from glossary_tests.glossary_test_env import Context, TestEnv

# The entries are not sorted, and some fields have their default value.
UNSORTED_GLOSSARY_YAML = """\
- name: title
  description: the name of a book
  aliases: []
  abbreviation: null
- name: report
  description: an error report that is sent to Sentry
- name: book
  description: a written work that consists of chapters
- name: report
  description: a markdown document with the statistics of a user
"""

SORTED_GLOSSARY_YAML = """\
- name: book
  description: a written work that consists of chapters
- name: report
  description: an error report that is sent to Sentry
- name: report
  description: a markdown document with the statistics of a user
- name: title
  description: the name of a book
"""


def create_env(context: Context):
    return Env(context)


def test_save_glossary_sorts_the_entries(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a glossary with unsorted entries, two of them for "report", and
    # with fields that have their default value.
    if env.step(
        env.write_glossary(UNSORTED_GLOSSARY_YAML),
    ):
        pass

    # We load and save the glossary.
    #
    # The entries should be sorted by name, the entries for "report" should
    # keep their order, and the fields with their default value should be left
    # out.
    if env.step(
        env.load_glossary(),
        env.save_glossary(),
    ):
        assert env.glossary_text() == SORTED_GLOSSARY_YAML


def test_load_glossary_without_a_glossary_file(context: Context):
    # Create the test environment
    env = create_env(context)

    # There is no glossary file yet, and we load the glossary.
    #
    # It should be empty.
    if env.step(
        env.load_glossary(),
    ):
        assert not env.glossary_path.exists()
        assert env.names() == []


class Env(TestEnv):
    pass
