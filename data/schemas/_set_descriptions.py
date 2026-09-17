"""Dev helper: rewrite `description` (and optionally `example`) values in place.

Edits are textual and scoped to a single property block so that surrounding
formatting is left untouched. Every edit is verified by reparsing the file.
Usage: fill EDITS, run from the repo root, then delete this file.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def prop_span(text, prop):
    """Return (start, end) of the JSON object that is the value of "<prop>"."""
    spans = []
    for m in re.finditer(r'"%s"\s*:\s*\{' % re.escape(prop), text):
        depth, i = 0, m.end() - 1
        while i < len(text):
            c = text[i]
            if c == '"':  # skip strings, honouring escapes
                i += 1
                while text[i] != '"':
                    i += 2 if text[i] == '\\' else 1
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    spans.append((m.start(), i + 1))
                    break
            i += 1
    if len(spans) != 1:
        raise SystemExit(f'  !! {prop}: expected 1 block, found {len(spans)}')
    return spans[0]


def set_field(text, prop, field, value):
    start, end = prop_span(text, prop)
    block = text[start:end]
    indent = re.match(
        r'\s*', text[text.rfind('\n', 0, start) + 1:start]).group(0)
    encoded = json.dumps(value, ensure_ascii=False)
    scalar = r'"(?:[^"\\]|\\.)*"|-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?|true|false|null'
    pat = re.compile(r'"%s"\s*:\s*(?:%s)' % (field, scalar))
    if pat.search(block):
        new_block = pat.sub(lambda _: f'"{field}": {encoded}', block, count=1)
    else:  # insert as the last key of the block
        tail = block.rfind('\n')
        new_block = (block[:tail].rstrip() + ',\n' + indent + '  '
                     + f'"{field}": {encoded}' + block[tail:])
    return text[:start] + new_block + text[end:]


def apply(edits):
    for rel, props in edits.items():
        path = os.path.join(ROOT, rel)
        text = original = open(path).read()
        for prop, fields in props.items():
            for field, value in fields.items():
                text = set_field(text, prop, field, value)
        json.loads(text)  # fail before writing if we broke the file
        if text != original:
            open(path, 'w').write(text)
        # verify every intended value actually landed
        doc = json.loads(text)
        found = {}

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == 'properties' and isinstance(v, dict):
                        found.update(
                            {p: d for p, d in v.items() if isinstance(d, dict)})
                        # nested properties, e.g. under items
                        walk(list(v.values()))
                    else:
                        walk(v)
            elif isinstance(o, list):
                for i in o:
                    walk(i)
        walk(doc)
        for prop, fields in props.items():
            for field, value in fields.items():
                assert found[prop].get(
                    field) == value, f'{rel}:{prop}.{field} not applied'
        print(f'  ok {rel}  ({sum(len(f) for f in props.values())} values)')


if __name__ == '__main__':
    mod = sys.argv[1]
    apply(__import__(mod).EDITS)
