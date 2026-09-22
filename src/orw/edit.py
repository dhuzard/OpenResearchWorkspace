"""Byte-preserving structural edits to the block-style YAML records ORW writes.

Mutations must not reformat metadata a researcher wrote by hand. Loading and
re-dumping a document would discard comments, key order and quoting style, so
every edit here replaces one located span of the original text and leaves the
remaining bytes untouched. A reviewer then sees only the lines an operation
actually changed.

The supported subset is the block style ORW generates: mappings, block
sequences of mappings, and empty flow sequences (``[]``). Flow collections with
content, anchors, aliases, tags and multi-document streams are refused rather
than rewritten, because preserving them is not deterministic here.
"""
from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

import yaml

# Sequence items are rendered at the parent key's column plus this indent.
INDENT = 2


class YamlEditError(ValueError):
    """A document cannot be edited deterministically in place."""


class Missing:
    """Marker for a key that is absent from a mapping."""

    __slots__ = ()


MISSING = Missing()


def scalar(value: Any) -> str:
    """Render a YAML scalar with deterministic quoting.

    JSON strings are valid YAML scalars, so ``json.dumps`` gives stable
    escaping without pulling in the emitter's context-dependent style rules.
    """

    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    raise YamlEditError(f"Unsupported scalar type: {type(value).__name__}")


def render_block(value: Any, indent: int) -> str:
    """Render *value* as block YAML lines, each already indented."""

    pad = " " * indent
    if isinstance(value, Mapping):
        if not value:
            return f"{pad}{{}}\n"
        lines = []
        for key, item in value.items():
            if item is None:
                continue
            lines.append(_render_pair(str(key), item, indent))
        return "".join(lines)
    if isinstance(value, (list, tuple)):
        if not value:
            return f"{pad}[]\n"
        lines = []
        for item in value:
            if isinstance(item, Mapping):
                body = render_block(item, indent + INDENT)
                first, _, rest = body.partition("\n")
                lines.append(f"{pad}- {first.strip()}\n")
                if rest:
                    lines.append(rest if rest.endswith("\n") else rest + "\n")
            else:
                lines.append(f"{pad}- {scalar(item)}\n")
        return "".join(lines)
    return f"{pad}{scalar(value)}\n"


def _render_pair(key: str, value: Any, indent: int) -> str:
    pad = " " * indent
    if isinstance(value, (list, tuple)) and not value:
        return f"{pad}{key}: []\n"
    if isinstance(value, Mapping) and not value:
        return f"{pad}{key}: {{}}\n"
    if isinstance(value, (list, tuple, Mapping)):
        return f"{pad}{key}:\n" + render_block(value, indent + INDENT)
    return f"{pad}{key}: {scalar(value)}\n"


def compose(text: str) -> yaml.Node:
    """Compose a single-document node graph, refusing constructs we cannot edit."""

    try:
        nodes = list(yaml.compose_all(text))
    except yaml.YAMLError as exc:
        raise YamlEditError(f"Document is not valid YAML: {exc}") from exc
    if len(nodes) != 1 or nodes[0] is None:
        raise YamlEditError("Editable records must contain exactly one YAML document.")
    root = nodes[0]
    if not isinstance(root, yaml.MappingNode):
        raise YamlEditError("Editable records must have a mapping at their root.")
    return root


def _entry(node: yaml.Node, key: Any) -> tuple[yaml.Node | None, yaml.Node | Missing]:
    """Return the (key node, value node) addressed by *key*, or MISSING."""

    if isinstance(key, int):
        if not isinstance(node, yaml.SequenceNode):
            raise YamlEditError(f"Expected a sequence to index with {key}.")
        if key >= len(node.value):
            return None, MISSING
        return None, node.value[key]
    if not isinstance(node, yaml.MappingNode):
        raise YamlEditError(f"Expected a mapping to look up {key!r}.")
    for key_node, value_node in node.value:
        if isinstance(key_node, yaml.ScalarNode) and key_node.value == key:
            return key_node, value_node
    return None, MISSING


def locate(
    root: yaml.Node, path: Sequence[Any]
) -> tuple[yaml.Node, yaml.Node | None, yaml.Node | Missing]:
    """Resolve *path*, returning (parent node, key node, value node).

    The value node is MISSING when the final step is absent; every earlier step
    must exist, because ORW never invents intermediate structure silently.
    """

    parent: yaml.Node = root
    key_node: yaml.Node | None = None
    value: yaml.Node | Missing = root
    for index, step in enumerate(path):
        if isinstance(value, Missing):
            shown = ".".join(str(part) for part in path[:index])
            raise YamlEditError(f"Record has no {shown!r} to edit.")
        parent = value
        key_node, value = _entry(parent, step)
    return parent, key_node, value


def _line_start(text: str, index: int) -> int:
    return text.rfind("\n", 0, index) + 1


def _content_end(text: str, start: int, end: int) -> int:
    """Return the end of the last content line of the span ``text[start:end]``.

    PyYAML ends a block collection at the next token, so the raw span trails
    into blank lines and into whole-line comments that introduce the following
    key. Those belong to what comes after, not to the collection being extended.
    """

    cursor = min(end, len(text))
    while cursor > start:
        probe = cursor - 1
        while probe > start and text[probe] in " \t\n\r":
            probe -= 1
        if probe <= start:
            break
        line = _line_start(text, probe)
        stripped = text[line : probe + 1].lstrip()
        if stripped.startswith("#"):
            cursor = line
            continue
        return probe + 1
    return start


def _value_span(text: str, key_node: yaml.Node | None, value_node: yaml.Node) -> tuple[int, int]:
    """Span from just after the ``key:`` colon to the end of its value content."""

    end = _content_end(text, value_node.start_mark.index, value_node.end_mark.index)
    if key_node is None:
        return value_node.start_mark.index, end
    colon = text.find(":", key_node.end_mark.index)
    if colon == -1 or colon >= value_node.start_mark.index:
        raise YamlEditError(f"Could not locate the ':' after {key_node.value!r}.")
    return colon + 1, end


def _insert_key(
    text: str, mapping: yaml.MappingNode, key: str, value: Any, *, blank_line: bool
) -> str:
    """Append ``key: value`` to *mapping*, keeping the document's indentation."""

    if not mapping.value:
        raise YamlEditError("Cannot extend an empty mapping deterministically.")
    indent = mapping.value[0][0].start_mark.column
    insert = _content_end(text, mapping.start_mark.index, mapping.end_mark.index)
    block = _render_pair(key, value, indent)
    separator = "\n\n" if blank_line else "\n"
    return text[:insert] + separator + block.rstrip("\n") + text[insert:]


def set_value(text: str, path: Sequence[Any], value: Any) -> str:
    """Set the scalar or collection at *path*, inserting the key when absent."""

    root = compose(text)
    parent, key_node, value_node = locate(root, path)
    key = path[-1]
    if isinstance(value_node, Missing):
        if not isinstance(key, str):
            raise YamlEditError("Cannot insert a value at a missing sequence index.")
        return _insert_key(text, parent, key, value, blank_line=parent is root)

    if isinstance(value, (list, tuple)) and value:
        indent = (key_node.start_mark.column if key_node else 0) + INDENT
        replacement = "\n" + render_block(value, indent).rstrip("\n")
    elif isinstance(value, Mapping) and value:
        indent = (key_node.start_mark.column if key_node else 0) + INDENT
        replacement = "\n" + render_block(value, indent).rstrip("\n")
    elif isinstance(value, (list, tuple)):
        replacement = " []"
    else:
        if not isinstance(value_node, yaml.ScalarNode):
            raise YamlEditError(
                f"Refusing to replace the collection at {'.'.join(map(str, path))} with a scalar."
            )
        replacement = f" {scalar(value)}"

    start, end = _value_span(text, key_node, value_node)
    return text[:start] + replacement + text[end:]


def append_item(text: str, path: Sequence[Any], item: Any) -> str:
    """Append *item* to the block sequence at *path*, creating the key if absent."""

    root = compose(text)
    parent, key_node, value_node = locate(root, path)
    key = path[-1]

    if isinstance(value_node, Missing):
        if not isinstance(key, str):
            raise YamlEditError("Cannot append to a missing sequence index.")
        return _insert_key(text, parent, key, [item], blank_line=parent is root)

    if not isinstance(value_node, yaml.SequenceNode):
        raise YamlEditError(f"{'.'.join(map(str, path))} is not a sequence.")

    indent = (key_node.start_mark.column if key_node else 0) + INDENT

    if not value_node.value:
        # An empty ``[]`` carries no items to align with; use the key's column.
        start, end = _value_span(text, key_node, value_node)
        block = "\n" + render_block([item], indent).rstrip("\n")
        return text[:start] + block + text[end:]

    if value_node.flow_style:
        raise YamlEditError(
            f"{'.'.join(map(str, path))} uses flow style; rewrite it as a block sequence first."
        )

    indent = value_node.start_mark.column
    insert = _content_end(text, value_node.start_mark.index, value_node.end_mark.index)
    block = render_block([item], indent).rstrip("\n")
    return text[:insert] + "\n" + block + text[insert:]
