def get_dotted_name(module_name: str) -> str:
    # E.g. myapp/books/models/book.py becomes myapp.books.models.book, and
    # myapp/__init__.py becomes myapp
    parts = module_name[: -len(".py")].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)
