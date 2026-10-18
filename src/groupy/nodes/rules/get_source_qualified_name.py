from groupy.nodes.models.class_node import ClassNode
from groupy.nodes.models.located_node import LocatedNode


def get_source_qualified_name(located_node: LocatedNode) -> str:
    # In the source, a method is qualified by its class, and a helper function is
    # a top-level function
    if isinstance(located_node.parent, ClassNode):
        return f"{located_node.parent.name}.{located_node.node.name}"
    return located_node.node.name
