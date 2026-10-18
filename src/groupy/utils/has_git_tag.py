from groupy.utils.run_git import run_git


def has_git_tag(tag: str) -> bool:
    return run_git("tag", "--list", tag) != ""
