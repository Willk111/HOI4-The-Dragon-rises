#!/usr/bin/env python3
"""Static checks for The Dragon Rises.

Catches the mistakes that HOI4 otherwise only reports in error.log (or silently
ignores): unbalanced braces, references to ideas/decisions/events/sprites that
don't exist, missing localisation, and file-name case mismatches (which only
break on Linux/macOS).

It does not know about vanilla content, so references to vanilla ideas, GFX or
traits are not checked. Use CWTools in VS Code for full validation.

Usage:  python3 tools/check_mod.py [mod_dir]      (default: TDR-Release)
Exit code is 1 if any errors were found, so it can run in CI.
"""

import re
import sys
from collections import Counter
from pathlib import Path

MOD = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent.parent / "TDR-Release")
PREFIX = "WAL_"

# Child blocks a decision category may have, and blocks only a decision has
CATEGORY_KEYS = {"allowed", "visible", "available", "visibility_type", "on_map_area", "priority", "picture"}
DECISION_ONLY_KEYS = {"complete_effect", "remove_effect", "ai_will_do", "cancel_effect", "timeout_effect"}

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def strip_comments(text):
    # Remove # comments, but not # inside quoted strings
    out = []
    for line in text.splitlines():
        in_str = False
        for i, ch in enumerate(line):
            if ch == '"':
                in_str = not in_str
            elif ch == "#" and not in_str:
                line = line[:i]
                break
        out.append(line)
    return "\n".join(out)


def read(path):
    return strip_comments(path.read_text(encoding="utf-8-sig", errors="replace"))


def script_files(*subdirs, exts=(".txt",)):
    for sub in subdirs:
        d = MOD / sub
        if d.exists():
            yield from (p for p in sorted(d.rglob("*")) if p.suffix.lower() in exts)


def rel(p):
    return p.relative_to(MOD)


def top_level_blocks(text, depth=0):
    """Return [(name, body)] of blocks opened at the given brace depth."""
    blocks, level, i = [], 0, 0
    token_re = re.compile(r'"[^"]*"|[{}=]|[\w.:@-]+')
    last_names = []
    start = None
    name = None
    for m in token_re.finditer(text):
        tok = m.group()
        if tok == "{":
            if level == depth:
                name = last_names[-2] if len(last_names) >= 2 and last_names[-1] == "=" else None
                start = m.end()
            level += 1
        elif tok == "}":
            level -= 1
            if level == depth and start is not None:
                blocks.append((name, text[start:m.start()]))
                start = None
        last_names.append(tok)
    return blocks


# ---------------------------------------------------------------- braces
def check_braces():
    for p in script_files("common", "history", "events", "interface", exts=(".txt", ".gfx", ".gui")):
        text = re.sub(r'"[^"]*"', '""', read(p))
        level = 0
        for n, line in enumerate(text.splitlines(), 1):
            level += line.count("{") - line.count("}")
            if level < 0:
                err(f"{rel(p)}:{n}: unmatched closing brace")
                break
        else:
            if level:
                err(f"{rel(p)}: {level} unclosed brace(s)")
        if "```" in p.read_text(encoding="utf-8-sig", errors="replace"):
            err(f"{rel(p)}: contains a markdown ``` fence")


# ---------------------------------------------------------------- definitions
def collect():
    d = {}
    ideas_text = "\n".join(read(p) for p in script_files("common/ideas"))
    d["ideas"] = set(re.findall(r"^\s*(%s\w+)\s*=\s*\{" % PREFIX, ideas_text, re.M))

    d["focuses"] = []
    for p in script_files("common/national_focus"):
        text = read(p)
        tree_ids = set(re.findall(r"focus_tree\s*=\s*\{\s*id\s*=\s*(\w+)", text))
        d["focuses"] += [f for f in re.findall(r"\bid\s*=\s*(%s\w+)" % PREFIX, text) if f not in tree_ids]

    # decisions: category = { decision = { ... } }
    d["categories"] = set()
    for p in script_files("common/decisions/categories"):
        d["categories"] |= {n for n, _ in top_level_blocks(read(p)) if n}
    d["decisions"] = set()
    for p in script_files("common/decisions"):
        if "categories" in p.parts:
            continue
        for cat, body in top_level_blocks(read(p)):
            children = {n for n, _ in top_level_blocks(body)}
            if cat not in d["categories"]:
                err(f"{rel(p)}: top-level block '{cat}' is not a category defined in "
                    f"common/decisions/categories (decisions must be nested inside a category)")
            if children & DECISION_ONLY_KEYS or re.search(r"^\s*cost\s*=", body, re.M) and not children - CATEGORY_KEYS:
                err(f"{rel(p)}: '{cat}' is a decision placed at the top level; it must be nested inside a category")
                continue
            d["decisions"] |= {n for n in children if n and n not in CATEGORY_KEYS}

    d["events"] = set()
    for p in script_files("events"):
        d["events"] |= set(re.findall(r"\bid\s*=\s*([\w]+\.\d+)", read(p)))

    d["characters"] = set()
    for p in script_files("common/characters"):
        for _, body in top_level_blocks(read(p)):
            d["characters"] |= {n for n, _ in top_level_blocks(body) if n}

    d["sprites"] = {}
    for p in script_files("interface", exts=(".gfx",)):
        for m in re.finditer(r'name\s*=\s*"?(\w+)"?\s+texturefile\s*=\s*"([^"]+)"', read(p)):
            d["sprites"][m.group(1)] = (m.group(2), p)

    d["loc"] = Counter()
    for p in sorted((MOD / "localisation").rglob("*.yml")):
        raw = p.read_bytes()
        if not raw.startswith(b"\xef\xbb\xbf"):
            err(f"{rel(p)}: localisation must be UTF-8 *with BOM*")
        for key in re.findall(r"^\s+([\w.]+):\d*\s", raw.decode("utf-8-sig"), re.M):
            d["loc"][key] += 1
    return d


# ---------------------------------------------------------------- references
def all_script_text():
    return "\n".join(read(p) for p in script_files("common", "history", "events"))


def check_references(d):
    text = all_script_text()

    for idea in set(re.findall(r"\b(?:add_ideas|has_idea|remove_ideas|add_idea|remove_idea)\s*=\s*(%s\w+)" % PREFIX, text)):
        if idea not in d["ideas"]:
            err(f"idea '{idea}' is used but not defined")
    for block in re.findall(r"\b(?:add_ideas|remove_ideas)\s*=\s*\{([^}]*)\}", text):
        for idea in re.findall(r"%s\w+" % PREFIX, block):
            if idea not in d["ideas"]:
                err(f"idea '{idea}' is used but not defined")

    for dec in set(re.findall(r"\b(?:unlock_decision_tooltip|activate_decision|has_decision)\s*=\s*(\w+)", text)):
        if dec not in d["decisions"]:
            err(f"decision '{dec}' is referenced but not defined")

    for focus in set(re.findall(r"\b(?:focus|has_completed_focus)\s*=\s*(%s\w+)" % PREFIX, text)):
        if focus not in d["focuses"]:
            err(f"focus '{focus}' is referenced but not defined")

    for ev in set(re.findall(r"\b(?:country_event|news_event|state_event)\s*=\s*\{[^}]*?\bid\s*=\s*([\w]+\.\d+)", text)) | \
              set(re.findall(r"\b(?:country_event|news_event|state_event)\s*=\s*([\w]+\.\d+)", text)):
        if ev not in d["events"]:
            err(f"event '{ev}' is fired but not defined")

    for c in set(re.findall(r"\b(?:recruit_character|promote_character|retire_character)\s*=\s*(\w+)", text)):
        if c not in d["characters"]:
            err(f"character '{c}' is used but not defined")

    flags_set = set(re.findall(r"\bset_country_flag\s*=\s*\{?\s*(?:flag\s*=\s*)?(\w+)", text))
    for flag in set(re.findall(r"\bhas_country_flag\s*=\s*\{?\s*(?:flag\s*=\s*)?(\w+)", text)):
        if flag not in flags_set:
            err(f"country flag '{flag}' is checked but never set")

    for gfx in set(re.findall(r"\bicon\s*=\s*(GFX_focus_\w+)", text)):
        if gfx not in d["sprites"]:
            err(f"sprite '{gfx}' is used but not defined in interface/*.gfx")

    for name, (tex, p) in d["sprites"].items():
        target = MOD / tex
        if not target.exists():
            # look for a case-insensitive match to give a better message
            matches = [q for q in target.parent.glob("*") if q.name.lower() == target.name.lower()] if target.parent.exists() else []
            if matches:
                err(f"{rel(p)}: {name} -> '{tex}' only matches '{matches[0].name}' case-insensitively (breaks on Linux/macOS)")
            else:
                err(f"{rel(p)}: {name} -> '{tex}' does not exist")

    # mutually_exclusive must be reciprocal
    for p in script_files("common/national_focus"):
        excl = {}
        for _, tree in top_level_blocks(read(p)):
            for name, body in top_level_blocks(tree):
                if name != "focus":
                    continue
                fid = re.search(r"\bid\s*=\s*(\w+)", body)
                if fid:
                    excl[fid.group(1)] = set(re.findall(r"mutually_exclusive\s*=\s*\{\s*focus\s*=\s*(\w+)", body))
        for a, others in excl.items():
            for b in others:
                if a not in excl.get(b, set()):
                    err(f"{rel(p)}: {a} is mutually exclusive with {b}, but not the other way round")

        # overlapping focus positions
        pos = Counter()
        for _, tree in top_level_blocks(read(p)):
            for name, body in top_level_blocks(tree):
                if name == "focus" and "relative_position_id" not in body:
                    x = re.search(r"\bx\s*=\s*(-?\d+)", body)
                    y = re.search(r"\by\s*=\s*(-?\d+)", body)
                    if x and y:
                        pos[(int(x.group(1)), int(y.group(1)))] += 1
        for xy, n in pos.items():
            if n > 1:
                err(f"{rel(p)}: {n} focuses share position x={xy[0]} y={xy[1]}")


def check_buildings(text_by_file):
    for p, text in text_by_file:
        for m in re.finditer(r"type\s*=\s*(coastal_bunker|naval_base)\s*(.*?)instant_build", text, re.S):
            body = m.group(2)
            if "province" in body and not re.search(r"limit_to_(coastal|naval_base)\s*=\s*yes", body):
                err(f"{rel(p)}: {m.group(1)} province selection needs limit_to_coastal / limit_to_naval_base")


def check_loc(d):
    loc = d["loc"]
    for f in d["focuses"]:
        if f not in loc:
            err(f"focus '{f}' has no localisation")
        if f + "_desc" not in loc:
            warn(f"focus '{f}' has no _desc localisation")
    for i in d["ideas"]:
        if i not in loc:
            err(f"idea '{i}' has no localisation")
    for x in d["decisions"] | d["categories"]:
        if x not in loc:
            err(f"decision/category '{x}' has no localisation")
    for e in d["events"]:
        for suffix in (".t", ".d"):
            if e + suffix not in loc:
                err(f"event '{e}' has no '{e}{suffix}' localisation")
    dups = sorted(k for k, n in loc.items() if n > 1)
    if dups:
        warn(f"{len(dups)} localisation keys are defined more than once (last one wins), e.g. {', '.join(dups[:5])}")


def check_misc():
    units = MOD / "history" / "units"
    if units.exists():
        for p in units.glob("*.oob"):
            err(f"{rel(p)}: HOI4 only loads .txt files from history/units")
    hist = MOD / "history" / "countries"
    for p in hist.glob("*.txt"):
        if re.search(r"^\s*buildings\s*=", read(p), re.M):
            err(f"{rel(p)}: 'buildings' is not valid in country history (put it in history/states)")


def main():
    if not MOD.exists():
        sys.exit(f"mod folder not found: {MOD}")
    check_braces()
    d = collect()
    check_references(d)
    check_buildings([(p, read(p)) for p in script_files("common")])
    check_loc(d)
    check_misc()

    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR:   {e}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
