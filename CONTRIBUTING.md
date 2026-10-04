# Contributing

[Suggest a character](https://github.com/balaboom123/awesome-italian-brainrot/issues/new?template=add-character.yml) or [add audio](https://github.com/balaboom123/awesome-italian-brainrot/issues/new?template=add-audio.yml). Include a source link.

## Add a character

1. Search names and aliases in [characters.json](characters.json) to avoid duplicates.
2. Create `characters/<slug>/` and add the files below.
3. Copy an entry in `characters.json` and update its metadata.
4. Generate the pages and run the checks:

   ```sh
   python3 scripts/build_readme.py
   python3 scripts/build_readme.py --check
   python3 -m unittest discover -s tests
   ```

5. Open a pull request with the files, metadata and generated pages.

The gallery groups characters by first letter and sorts names automatically.

## Names

- `name`: the original spelling when documented; otherwise the common spelling.
- `aliases`: other spellings of the same character.
- `slug`: a permanent folder ID, using lowercase ASCII letters, numbers and hyphens; at most 60 characters.

For example, `lirilì larilà` uses `lirili-larila`. Shorten long chants in the slug and keep the full name in `name`. Change display names without renaming existing slugs.

## Files

Use one thumbnail per source. Source keys: `commons`, `wikioasis`, `kym`, `namuwiki`, `fandom`. Prefer Commons when available.

| File | Limit |
|------|-------|
| `<slug>_<source>.webp` | Required thumbnail, ≤ 200 KB |
| `<slug>_<source>_full.png` | Optional full image, ≤ 5 MB |
| `<slug>.mp3` | Optional original TTS clip, ≤ 1 MB |
| `README.md` | Generated; do not edit |

Link larger originals in the PR for a maintainer to upload. Use meme images or wiki copies; skip redraws, alternate poses, remixes and songs.

## Metadata

```json
{
  "name": "tralalero tralala",
  "slug": "tralalero-tralala",
  "kind": "original",
  "aliases": [],
  "thumb": "fandom",
  "sources": {
    "fandom": {"hires": "900x900"}
  }
}
```

All fields above are required except `hires`.

| Field | Use |
|-------|-----|
| `thumb` | Source key for the gallery image |
| `sources.<key>.url` | Source page; required except for the closed Fandom wiki |
| `sources.<key>.hires` | Full-image dimensions, such as `900x900` |
| `sources.<key>.hires_url` | Direct download URL when the full image is hosted elsewhere |
| `audio_source` | Audio source URL, when known |
| `origin` | Optional `creator`, `platform`, `date` and citation `url` |
| `components` | At least two distinct character slugs when `kind` is `fusion` |

Each listed source needs a thumbnail. Each `hires` entry needs a local PNG or a working `hires_url`.

## What belongs here?

| Submission | Action |
|------------|--------|
| Another spelling or source | Update the existing character |
| Mashup of known characters | Use `fusion` and list its `components` |
| Separately viral character | Add as `original` with a source |
| Fan invention or game exclusive | Skip unless it also became a TikTok/Instagram meme |

To merge duplicates, keep the older slug, move the files and add the other name as an alias. Do not reuse the removed slug.

## Large originals

Six migrated originals use links pinned to the old Git revision. Local copies are in the ignored `release-assets/` folder. A maintainer can publish them with:

```sh
gh release create hires --title "Hi-res images over 5 MB" --notes "Original images under normalized filenames." release-assets/*.png
```

After upload, set each `hires_url` to `https://github.com/balaboom123/awesome-italian-brainrot/releases/download/hires/<filename>` and regenerate the pages. Use the fixed release tag, not `latest`.

Old files remain in Git history. ZIP downloads and shallow clones avoid that history.
