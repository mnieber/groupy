from groupy.utils.matches_glob import matches_glob


def test_matches_glob():
    # A * matches within a dir, but not a /
    assert matches_glob("myapp/books.py", "myapp/*.py")
    assert not matches_glob("myapp/reports/summary.py", "myapp/*.py")

    # A ** matches any number of dirs (including none)
    assert matches_glob("myapp/reports/summary.py", "myapp/reports/**")
    assert matches_glob("myapp/reports/daily/totals.py", "myapp/reports/**")
    assert matches_glob("legacy.py", "**/legacy.py")
    assert matches_glob("myapp/old/legacy.py", "**/legacy.py")
    assert not matches_glob("myapp/books.py", "myapp/reports/**")

    # A pattern is matched against the whole path, so a dir does not match the
    # files below it
    assert matches_glob("myapp/legacy.py", "myapp/legacy.py")
    assert not matches_glob("myapp/reports/summary.py", "myapp/reports")
    assert not matches_glob("other/myapp/legacy.py", "myapp/legacy.py")
