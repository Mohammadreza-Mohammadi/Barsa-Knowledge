"""A strict, tiny YAML subset -- enough for this protocol's own files.

Why not a real YAML parser: this repository is standard-library only, and a
manifest is written by the manager and read by the manager. A full parser would
accept far more than the protocol allows, which is the opposite of what a
fail-closed store needs.

So the subset is deliberately narrow, and anything outside it is an error
rather than a guess:

    key: scalar                 # scalar: string, int, float, bool, null
    key: [a, b]                 # inline array
    key: [{a: 1, b: two}]       # inline array of flow mappings
    key:                        # nested block, exactly two spaces deeper
      inner: 1
    key:                        # block list of scalars
      - one
      - two
    # comment, or trailing comment after a value

A flow mapping is supported only with scalar values, and only because the
reviewer's evidence table is written that way -- a table of one-line rows is
exactly what a flow mapping is for, and forcing it into block form would make
the one artifact a human reads most the hardest one to write. Nothing else
nests: no anchors, no multi-line strings, no tabs. A quoted string keeps its
content verbatim, including a '#'.
"""

import re

_KEY = re.compile(r"^(?P<indent> *)(?P<key>[A-Za-z_][A-Za-z0-9_.-]*):(?P<rest>.*)$")
_ITEM = re.compile(r"^(?P<indent> *)- (?P<value>.*)$")


class YamlError(Exception):
    """The document is outside the supported subset, or malformed."""


def loads(text):
    """Parse the subset into dicts, lists and scalars."""
    root = {}
    # Each frame is (indent, container). A frame's container is a dict, or a
    # list once the first '- ' item is seen at that indent.
    stack = [(-2, root)]
    pending = None  # (indent, parent_dict, key) awaiting a nested block

    for lineno, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw:
            raise YamlError("line %d: tabs are not allowed" % lineno)
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue

        item = _ITEM.match(raw)
        if item:
            indent = len(item.group("indent"))
            value = _scalar(_strip_comment(item.group("value")), lineno)
            if pending and indent >= pending[0]:
                lst = []
                pending[1][pending[2]] = lst
                stack.append((indent, lst))
                pending = None
            target = _frame_for(stack, indent, lineno)
            if not isinstance(target, list):
                raise YamlError("line %d: list item outside a list" % lineno)
            target.append(value)
            continue

        m = _KEY.match(raw)
        if not m:
            raise YamlError("line %d: not a key or a list item: %r"
                            % (lineno, raw))
        indent = len(m.group("indent"))
        key = m.group("key")
        rest = m.group("rest")

        if pending and indent > pending[0]:
            block = {}
            pending[1][pending[2]] = block
            stack.append((indent, block))
            pending = None

        target = _frame_for(stack, indent, lineno)
        if not isinstance(target, dict):
            raise YamlError("line %d: key inside a list" % lineno)

        body = _strip_comment(rest)
        if body == "":
            # Either a nested block or an empty value; the next line decides.
            pending = (indent + 1, target, key)
            target[key] = None
        else:
            target[key] = _scalar(body, lineno)
    return root


def _frame_for(stack, indent, lineno):
    while len(stack) > 1 and stack[-1][0] > indent:
        stack.pop()
    if stack[-1][0] != indent and len(stack) > 1:
        # Allow the root frame to accept indent 0.
        if not (len(stack) == 1 or stack[-1][0] < indent):
            raise YamlError("line %d: unexpected indentation" % lineno)
    return stack[-1][1]


def _strip_comment(text):
    out = []
    quote = None
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
            out.append(ch)
        elif ch == "#" and (not out or out[-1] in " \t"):
            break
        else:
            out.append(ch)
        i += 1
    return "".join(out).strip()


def _scalar(text, lineno):
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [_scalar(part.strip(), lineno) for part in _split_inline(inner)]
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        return text[1:-1]
    low = text.lower()
    if low in ("null", "~", ""):
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?\d+\.\d+", text):
        return float(text)
    if text.startswith("{"):
        if not text.endswith("}"):
            raise YamlError("line %d: unterminated flow mapping" % lineno)
        inner = text[1:-1].strip()
        row = {}
        for part in _split_inline(inner) if inner else ():
            if ":" not in part:
                raise YamlError("line %d: flow mapping entry without a colon: "
                                "%r" % (lineno, part))
            key, value = part.split(":", 1)
            key = key.strip()
            if not key:
                raise YamlError("line %d: flow mapping key is empty" % lineno)
            value = _scalar(value.strip(), lineno)
            if isinstance(value, (dict, list)):
                raise YamlError("line %d: a flow mapping takes scalar values "
                                "only" % lineno)
            row[key] = value
        return row
    return text


def _split_inline(inner):
    """Split on commas that are not inside quotes, braces or brackets."""
    parts, buf, quote, depth = [], [], None, 0
    for ch in inner:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
            buf.append(ch)
        elif ch in "[{":
            depth += 1
            buf.append(ch)
        elif ch in "]}":
            depth -= 1
            buf.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if quote or depth:
        raise YamlError("unbalanced quotes or brackets in %r" % inner)
    if buf:
        parts.append("".join(buf))
    return parts


def dumps(data):
    """Emit the subset. Deterministic: key order is insertion order."""
    lines = []
    _emit(data, 0, lines)
    return "\n".join(lines) + "\n"


def _emit(node, indent, lines):
    pad = " " * indent
    for key, value in node.items():
        if isinstance(value, dict):
            if not value:
                lines.append("%s%s: {}" % (pad, key))
                raise YamlError("empty mappings are not emitted; use null")
            lines.append("%s%s:" % (pad, key))
            _emit(value, indent + 2, lines)
        elif isinstance(value, list):
            lines.append("%s%s: %s" % (pad, key, _inline(value)))
        else:
            lines.append("%s%s: %s" % (pad, key, _fmt(value)))


def _inline(values):
    out = []
    for value in values:
        if isinstance(value, dict):
            out.append("{" + ", ".join(
                "%s: %s" % (k, _fmt(v)) for k, v in value.items()) + "}")
        elif isinstance(value, list):
            raise YamlError("a nested inline array is outside the subset")
        else:
            out.append(_fmt(value))
    return "[" + ", ".join(out) + "]"


def _fmt(value):
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return repr(value)
    text = str(value)
    if text == "" or re.search(r'[:#\[\]{}",]|^\s|\s$|^-', text) \
            or text.lower() in ("null", "true", "false", "~") \
            or re.fullmatch(r"-?\d+(\.\d+)?", text):
        return '"%s"' % text.replace("\\", "\\\\").replace('"', '\\"')
    return text
