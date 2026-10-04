#!/usr/bin/env python3
"""Generate README.md + characters/<slug>/README.md from characters.json and the characters/ tree.

usage: python3 scripts/build_readme.py          # write files
       python3 scripts/build_readme.py --check  # validate + fail if committed READMEs are stale; exit 1 on problems
"""
import html, json, os, re, sys, unicodedata
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS = os.path.join(ROOT, "characters")
REPO = "https://github.com/balaboom123/awesome-italian-brainrot"
MAX_BYTES = 5_000_000     # hard cap per in-tree file; larger originals use explicit URLs
MAX_THUMB = 200_000       # README loads every thumbnail at once
MAX_AUDIO = 1_000_000
COLS = 3                  # compact gallery with 120 px thumbnails
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KINDS = {"original", "fusion"}
# source key -> (display name, what its files are, whether a per-character url is required)
SOURCES = {
    "commons":   ("Wikimedia Commons", "licensed per file on its Commons page (most are tagged public domain as AI output; check each)", True),
    "wikioasis": ("Italian Brainrot Wiki (WikiOasis)", "fan uploads of TikTok/AI images; the wiki text is CC BY-SA 4.0, the files are not", True),
    "miraheze": ("Italian Brainrot Wiki (Miraheze archive)", "archived fan uploads; media rights recorded per file", True),
    "kym":       ("Know Your Meme", "fan uploads, rights with the original poster", True),
    "namuwiki":  ("Namu Wiki", "fan uploads, rights with the original poster (wiki text is CC BY-NC-SA 2.0 KR)", True),
    "fandom":    ("Fandom", "fan uploads, rights with the original poster; no live page to link", False),
}

def load():
    with open(os.path.join(ROOT, "characters.json"), encoding="utf-8") as f:
        return json.load(f)

def files_of(c):
    """(folder, thumb filename, {source: hires filename or None if hosted externally}, audio filename|None)"""
    d = os.path.join(CHARS, c["slug"])
    thumb = f'{c["slug"]}_{c["thumb"]}.webp'
    hires = {}
    for src, s in c["sources"].items():
        if s.get("hires"):
            local = f'{c["slug"]}_{src}_full.png'
            hires[src] = local if os.path.isfile(os.path.join(d, local)) else None
    audio = f'{c["slug"]}.mp3' if os.path.exists(os.path.join(d, f'{c["slug"]}.mp3')) else None
    return d, thumb, hires, audio

def valid_url(value):
    if not isinstance(value, str) or any(ch.isspace() for ch in value):
        return False
    try:
        parts = urlsplit(value)
        return parts.scheme in {"http", "https"} and bool(parts.hostname)
    except ValueError:
        return False


def check_credit(credit, label):
    errs = []
    if not isinstance(credit, dict):
        return [f"{label}: credit must be an object"]
    for key in ("attribution", "license", "page_title"):
        if key in credit and (not isinstance(credit[key], str) or not credit[key].strip() or any(ch in credit[key] for ch in "\r\n")):
            errs.append(f"{label}.{key}: must be a non-empty single-line string")
    if "license_url" in credit and (not valid_url(credit["license_url"]) or not credit.get("license")):
        errs.append(f"{label}.license_url: requires an HTTP(S) URL and license name")
    return errs


def check_schema(chars):
    """Reject malformed metadata before any paths or generated links are used."""
    if not isinstance(chars, list) or not chars:
        return ["characters.json must be a non-empty list of objects"]
    errs, slugs, names = [], set(), {}
    for i, c in enumerate(chars):
        if not isinstance(c, dict):
            errs.append(f"entry {i}: must be an object")
            continue
        slug = c.get("slug")
        if isinstance(slug, str):
            if slug in slugs:
                errs.append(f"duplicate slug: {slug}")
            slugs.add(slug)
    for i, c in enumerate(chars):
        if not isinstance(c, dict):
            continue
        s = c.get("slug", f"entry {i}")
        for k in ("name", "slug", "kind", "aliases", "thumb", "sources"):
            if k not in c:
                errs.append(f"{s}: missing key {k}")
        if not isinstance(s, str) or not SLUG_RE.fullmatch(s) or len(s) > 60:
            errs.append(f"bad slug format: {s}")
        if not isinstance(c.get("name"), str) or not c["name"].strip():
            errs.append(f"{s}: name must be a non-empty string")
        if c.get("kind") not in ("original", "fusion"):
            errs.append(f"{s}: kind must be one of {sorted(KINDS)}")
        aliases = c.get("aliases")
        if not isinstance(aliases, list) or any(not isinstance(a, str) or not a.strip() for a in aliases):
            errs.append(f"{s}: aliases must be a list of non-empty strings")
            aliases = []
        for n in [c.get("name")] + aliases:
            if not isinstance(n, str):
                continue
            key = n.casefold().strip()
            if key in names:
                errs.append(f"name/alias collision: '{n}' in {s} and {names[key]}")
            names[key] = s
        if c.get("kind") == "fusion":
            comps = c.get("components")
            if not isinstance(comps, list) or any(not isinstance(x, str) for x in comps):
                errs.append(f"{s}: components must be a list of slugs")
            else:
                if len(set(comps)) < 2 or len(set(comps)) != len(comps):
                    errs.append(f"{s}: fusion needs >= 2 distinct components, without duplicates")
                for x in comps:
                    if x not in slugs or x == s:
                        errs.append(f"{s}: unknown or self-referencing component {x}")
        srcs = c.get("sources")
        if not isinstance(srcs, dict) or not srcs:
            errs.append(f"{s}: sources must be a non-empty object")
            srcs = {}
        for k, v in srcs.items():
            if k not in SOURCES:
                errs.append(f"{s}: unknown source key '{k}' (allowed: {sorted(SOURCES)})")
                continue
            if not isinstance(v, dict):
                errs.append(f"{s}: sources.{k} must be an object")
                continue
            errs += check_credit(v, f"{s}: sources.{k}")
            if (SOURCES[k][2] or "url" in v) and not valid_url(v.get("url")):
                errs.append(f"{s}: sources.{k}.url must be an HTTP(S) source page URL")
            if "hires" in v and (not isinstance(v["hires"], str) or not re.fullmatch(r"[1-9][0-9]*x[1-9][0-9]*", v["hires"])):
                errs.append(f"{s}: sources.{k}.hires must be dimensions such as 900x900")
            if "hires_url" in v and (not valid_url(v["hires_url"]) or "hires" not in v):
                errs.append(f"{s}: sources.{k}.hires_url requires an HTTP(S) URL and hires dimensions")
        if not isinstance(c.get("thumb"), str) or c["thumb"] not in srcs:
            errs.append(f"{s}: thumb must name a listed source")
        if "audio_source" in c and not valid_url(c["audio_source"]):
            errs.append(f"{s}: audio_source must be an HTTP(S) URL")
        if "audio_credit" in c:
            errs += check_credit(c["audio_credit"], f"{s}: audio_credit")
            if not c.get("audio_source"):
                errs.append(f"{s}: audio_credit requires audio_source")
        if "origin" in c:
            o = c["origin"]
            if not isinstance(o, dict) or any(not isinstance(o.get(k), str) or not o[k].strip() for k in ("creator", "platform", "date")) or not valid_url(o.get("url")):
                errs.append(f"{s}: origin requires creator, platform, date and an HTTP(S) source URL")
    return errs


def check_files(chars):
    errs = []
    slugs = {c["slug"] for c in chars}
    for name in sorted(os.listdir(CHARS)) if os.path.isdir(CHARS) else []:
        p = os.path.join(CHARS, name)
        if name not in slugs or not os.path.isdir(p) or os.path.islink(p):
            errs.append(f"unexpected entry without a character folder: characters/{name}")
    for c in chars:
        d, thumb, hires, audio = files_of(c)
        if not os.path.isdir(d):
            errs.append(f"missing folder: characters/{c['slug']}")
            continue
        allowed = {"README.md", f"{c['slug']}.mp3"}
        for source, metadata in c["sources"].items():
            thumbnail = f"{c['slug']}_{source}.webp"
            allowed.add(thumbnail)
            if not os.path.isfile(os.path.join(d, thumbnail)):
                errs.append(f"missing source thumbnail: {c['slug']}/{thumbnail}")
            if "hires" in metadata:
                allowed.add(f"{c['slug']}_{source}_full.png")
                if not hires[source] and not metadata.get("hires_url"):
                    errs.append(f"{c['slug']}/{source}: missing hi-res file; supply a local PNG or explicit hires_url")
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            rel = os.path.relpath(p, ROOT)
            if not os.path.isfile(p) or os.path.islink(p):
                errs.append(f"expected a regular file: {rel}")
                continue
            if f not in allowed:
                errs.append(f"file does not follow naming rules or lacks source metadata: {rel}")
            size = os.path.getsize(p)
            if f.endswith(".webp") and size > MAX_THUMB:
                errs.append(f"thumbnail over {MAX_THUMB//1000} KB: {rel}")
            elif f.endswith(".mp3") and size > MAX_AUDIO:
                errs.append(f"audio over {MAX_AUDIO//1000} KB: {rel}")
            if size > MAX_BYTES:
                errs.append(f"file over {MAX_BYTES//1_000_000} MB, host externally: {rel}")
    return errs

def title(s): return " ".join(w[:1].upper() + w[1:] for w in str(s).split())
def esc(s): return html.escape(title(s), quote=True)
def md(s): return str(s).replace("|", "\\|")

def cell(c):
    d, thumb, hires, audio = files_of(c)
    badges = ("🔊 " if audio else "") + ("🔗 " if c["kind"] == "fusion" else "")
    href = f'characters/{c["slug"]}'
    return (f'<a href="{href}"><img src="{href}/{thumb}" width="120" alt="{esc(c["name"])}"></a><br>'
            f'<a href="{href}"><b>{esc(c["name"])}</b></a><br><sub>{badges}</sub>')

def alphabet_key(c):
    return "".join(ch for ch in unicodedata.normalize("NFKD", c["name"].strip())
                   if not unicodedata.combining(ch)).casefold()


def alphabet_gallery(chars):
    groups = {}
    for c in sorted(chars, key=alphabet_key):
        first = alphabet_key(c)[0].upper()
        letter = first if first in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" else "Other"
        groups.setdefault(letter, []).append(c)
    sections = []
    for letter, group in sorted(groups.items()):
        rows = [group[i:i + COLS] for i in range(0, len(group), COLS)]
        table = "\n".join(
            "<tr>" + "".join(
                f'<td align="center" valign="top" width="33%">{cell(c)}</td>' for c in row
            ) + "</tr>" for row in rows
        )
        sections.append(f"### {letter}\n\n<table>\n{table}\n</table>")
    navigation = " · ".join(f"[{letter}](#{letter.lower()})" for letter in sorted(groups))
    return navigation + "\n\n" + "\n\n".join(sections)


def main_readme(chars):
    chars = sorted(chars, key=alphabet_key)
    n_audio = sum(1 for c in chars if files_of(c)[3])
    aliases = "\n".join(f'| [{md(title(c["name"]))}](characters/{c["slug"]}) | {md(", ".join(c["aliases"]))} |' for c in chars if c["aliases"])
    audio_list = "\n".join(f'- [{title(c["name"])}](characters/{c["slug"]}/{c["slug"]}.mp3)' for c in chars if files_of(c)[3])
    return f"""<!-- Generated by scripts/build_readme.py; edit characters.json and regenerate. -->

# Awesome Italian Brainrot [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

Italian brainrot characters, images and audio.

**{len(chars)} characters · {n_audio} with audio** · 🔊 Audio · 🔗 Fusion

[Characters](#characters) · [Audio](#audio) · [Other spellings](#other-spellings) · [Download](#download) · [Contribute](#contributing)

## Characters

{alphabet_gallery(chars)}

## Audio

Open or download an MP3:

{audio_list}

## Other spellings

Use Ctrl+F to find a name or alias.

| Character | Also spelled |
|-----------|--------------|
{aliases}

## Download

- [Download ZIP]({REPO}/archive/refs/heads/main.zip) or open a character page for individual files.
- Large originals are linked from each character page.
- [characters.json](characters.json) contains the full index.

For a smaller clone, skip the older file history:

```sh
git clone --depth 1 {REPO}.git
```

## Contributing

[Suggest a character]({REPO}/issues/new?template=add-character.yml) or [add audio]({REPO}/issues/new?template=add-audio.yml).

For pull requests, add the files and metadata, then run `python3 scripts/build_readme.py`.
See [CONTRIBUTING.md](CONTRIBUTING.md) for naming and file limits.

## License

The index, READMEs and scripts use [CC0](LICENSE). Images and audio retain their original rights; this repo grants no media license. Source links appear on each character page. Wiki text licenses do not automatically cover media. Rights holders may request removal.
"""


def credit_text(metadata):
    details = []
    for key in ("page_title", "attribution"):
        if metadata.get(key):
            details.append(html.escape(metadata[key]))
    if metadata.get("license"):
        name = html.escape(metadata["license"])
        details.append(f"[{name}]({metadata['license_url']})" if metadata.get("license_url") else name)
    return " · " + " · ".join(details) if details else ""


def char_readme(c):
    d, thumb, hires, audio = files_of(c)
    lines = [
        "<!-- Generated by scripts/build_readme.py; edit characters.json and regenerate. -->",
        "", f"# {title(c['name'])}", "",
        f'<img src="{thumb}" width="300" alt="{esc(c["name"])}">', "",
    ]
    if c["aliases"]:
        lines.append(f"**Also spelled:** {', '.join(c['aliases'])}\n")
    if c["kind"] == "fusion":
        lines.append("**Fusion of:** " + ", ".join(
            f"[{title(x.replace('-', ' '))}](../{x})" for x in c["components"]
        ) + "\n")
    if c.get("origin"):
        o = c["origin"]
        lines.append(f"**Origin:** {o['creator']} · {o['platform']} · {o['date']} ([source]({o['url']}))\n")
    lines += ["## Downloads", ""]
    if audio:
        credit = f" · [source]({c['audio_source']})" if c.get("audio_source") else ""
        lines.append(f"- [Audio (MP3)]({audio}){credit}{credit_text(c.get('audio_credit', {}))}")
    for source in c["sources"]:
        filename = f"{c['slug']}_{source}.webp"
        lines.append(f"- [Thumbnail · {SOURCES[source][0]}]({filename})")
    for src, local in hires.items():
        metadata = c["sources"][src]
        url = local or metadata["hires_url"]
        lines.append(f"- [Full image · {SOURCES[src][0]} · {metadata['hires']}]({url})")
    lines += ["", "## Sources", ""]
    for key, source in c["sources"].items():
        label = SOURCES[key][0]
        entry = f"- [{label}]({source['url']})" if source.get("url") else f"- {label} (wiki closed)"
        lines.append(entry + credit_text(source))
    lines.append("\n[← All characters](../../README.md)")
    return "\n".join(lines) + "\n"

def outputs(chars):
    yield os.path.join(ROOT, "README.md"), main_readme(chars)
    for c in chars: yield os.path.join(CHARS, c["slug"], "README.md"), char_readme(c)

if __name__ == "__main__":
    try:
        chars = load()
    except (OSError, ValueError) as exc:
        print(f"ERROR: cannot load characters.json: {exc}", file=sys.stderr)
        sys.exit(1)
    errs = check_schema(chars)
    if not errs:
        chars = sorted(chars, key=alphabet_key)
    if not errs: errs = check_files(chars)          # file checks assume a valid schema
    if "--check" in sys.argv and not errs:
        for p, text in outputs(chars):
            cur = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
            if cur != text: errs.append(f"stale, run scripts/build_readme.py: {os.path.relpath(p, ROOT)}")
    for e in errs: print("ERROR:", e, file=sys.stderr)
    if errs: sys.exit(1)
    if "--check" not in sys.argv:
        for p, text in outputs(chars):
            with open(p, "w", encoding="utf-8") as f: f.write(text)
        print(f"wrote README.md + {len(chars)} character READMEs")
