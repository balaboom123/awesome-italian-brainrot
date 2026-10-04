# Plan: find and add more sources

Improve existing characters first, then add verified new ones in small batches.

Based on `/home/gorden/Downloads/ib/sources.md` and `plan.md` (September 30, 2026), plus the current [contribution rules](../CONTRIBUTING.md). The source availability, archive sizes and site counts in those notes are leads to recheck during execution. This plan does not download anything.

## Starting point

The repo currently has 48 characters: 11 with audio and 3 with origin citations. All images use Fandom or Namu Wiki source keys. None of the existing audio has an `audio_source` link.

Keep existing slugs and the alphabetical gallery. Do not repeat the completed file migration.

## Source order

| Priority | Source | Use |
|----------|--------|-----|
| 1 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/Category:Italian_brainrot) | Images with per-file rights information; inspect possible original audio |
| 2 | [Know Your Meme](https://knowyourmeme.com/memes/italian-brainrot-ai-italian-animals), [Wikipedia](https://en.wikipedia.org/wiki/Italian_brainrot), [Wikidata](https://www.wikidata.org/wiki/Q133869040) | Names, aliases, creators, dates and original-post links |
| 3 | [MyInstants](https://www.myinstants.com/en/search/?name=italian+brainrot), [Voicemod Tuna](https://tuna.voicemod.net/) | Missing original character voice clips |
| 4 | [August 2025 Miraheze archive](https://archive.org/details/wiki-italianbrainrot.miraheze.org_w-20250801) | Discover new characters and retrieve their lead images |
| 5 | [WikiOasis](https://italianbrainrot.wikioasis.org), [August 2026 archive](https://archive.org/details/wiki-italianbrainrot.wikioasis.org_w-20260819) | Fill gaps left by the smaller archive |
| 6 | [Namu Wiki](https://en.namu.wiki/w/Italian%20Brainrot/%EB%93%B1%EC%9E%A5%20%EC%BA%90%EB%A6%AD%ED%84%B0) | Confirm existing sources and unresolved variants |

Use playbrainrot.org, brainrotcharacters.net and italianbrainrotwiki.com only as name leads, then verify elsewhere. Do not import game-exclusive assets, fan inventions or replacement AI generations. The reference also excludes media from the Steal a Brainrot wiki and generator-promotion repositories.

## 1. Inventory and prepare

1. Read `characters.json`, `CONTRIBUTING.md` and `scripts/build_readme.py` again; the repo may have changed.
2. Build a lookup of existing names, aliases and slugs. Normalize case, accents and spacing for matching; review ambiguous matches manually.
3. List missing audio, missing origin citations and characters without Commons images.
4. Use `/tmp/brainrot-source-import/` for downloads and extraction. Keep bulk archives out of Git.
5. Create `docs/source-import-report.md` for results and `data/source-imports.jsonl` for provenance during execution.

Each provenance record should include the character slug, source key, source page, direct download URL, retrieval date, stated license or `unknown`, attribution, original SHA-256, final repository path and final SHA-256. For archived files, also record the archive item and member path. Record any resizing or audio conversion.

Before adding files requiring credit, extend the generator to display optional source `attribution`, `license` and `license_url` fields. Validate these fields and test their rendering. Add equivalent audio credit support only if needed. Keep image credit beside its source and audio credit beside its download.

## 2. Improve existing images and citations

Use the Commons MediaWiki API to enumerate category files and relevant subcategories. Follow pagination and inspect each file page, image metadata and rights statement.

For each match:

- Confirm it depicts the existing character, not a variant or unrelated artwork.
- Check for duplicates by hash and visual inspection.
- Download one suitable image per character; record the actual file-page URL.
- Create `<slug>_commons.webp`. Keep earlier sources; set `thumb` to `commons` when the image is suitable.
- Save a full PNG only when it adds useful detail and fits the size limit.

Use KYM, Wikipedia and Wikidata to fill aliases and `origin`. Follow links to original posts when available. Preserve the precision of the source date: do not invent a day for a month-only citation. Skip uncertain creator claims.

The reference estimated roughly 13 Commons matches. Treat that as a lead, not a required quota.

## 3. Fill audio gaps

Start with **Brri Brri Bicus Dicus Bombicus**, identified as an audio request in the reference. Then search the other 36 missing-audio characters using their names and aliases.

Check Commons first, then MyInstants and Voicemod. Inspect and listen to each clip before accepting it. Use the original character narration; reject songs, remixes, compilations and game voices.

The reference mentions `Italian Brainrot music.opus` and a music video. Do not import these merely because they are available: they may conflict with the repo's original-clip rule. Inspect `Tung Tung Tung Sahur.webm` separately; that character already has audio, so avoid a redundant replacement.

Save accepted clips as `<slug>.mp3` and set `audio_source` to the source page. Convert containers/codecs only as needed; do not trim narration to force it under the limit. Log any conversion. For the 11 existing clips, add source links only when a match is supported; do not guess their provenance.

## 4. Find new characters in the smaller archive

Inspect the Internet Archive item metadata before downloading. Confirm actual filenames, sizes and available checksums. The reference describes the August 2025 image archive as about 909 MB; the later archives are much larger.

1. Fetch the small site metadata and XML dump first.
2. Stream the XML, retaining the latest available revision per page. Exclude redirects, discussion pages, categories and templates from the candidate list.
3. Extract candidate names, aliases, lead-image filenames and cited original posts.
4. Match against the current index. Verify that each new candidate is a distinct meme character, not just an article or game entry.
5. Select up to **20 new characters** for the first batch, prioritizing clear sources and complete media.
6. Retrieve only their lead images where individual downloads are available. Otherwise, download the smaller archive once, verify it and extract selected members.

Do not assume selecting members from a `.7z` avoids downloading the archive; check the available access method first. Leave the reported 14–20 GB archives for a later batch if the smaller source cannot fill a documented gap.

The validator has no `miraheze` source key. If importing old Miraheze files, add that key with an accurate display name and tests. Preserve the original page title, archived page evidence and dump location. Use `wikioasis` only for media actually verified there; a successor wiki name is not sufficient attribution for an older download.

## 5. Normalize and integrate

| Asset | Repository path | Limit |
|-------|-----------------|-------|
| Thumbnail | `characters/<slug>/<slug>_<source>.webp` | 200,000 bytes |
| Full image | `characters/<slug>/<slug>_<source>_full.png` | 5,000,000 bytes |
| Audio | `characters/<slug>/<slug>.mp3` | 1,000,000 bytes |

Resize thumbnails proportionally without upscaling. Reduce dimensions or quality until they fit, then inspect the result. Record the actual full-image dimensions in `hires`.

For larger originals, use a verified direct `hires_url` or keep the file staged for later release upload. Do not add `hires` metadata without a local PNG or working URL. Do not publish a release as part of a download-only run.

Every image source needs a thumbnail and source-page URL. Audio websites belong in `audio_source`, not the image-source map. New entries must meet the existing schema; fusions need at least two known component slugs. Regenerate pages instead of editing them by hand.

For downloads, use timeouts, limited concurrency, retry limits and backoff. Verify file content as well as HTTP status: an HTML error page is not an image. Cache successful downloads and check hashes before reusing them. A second run must not create duplicates or overwrite existing media without a documented reason.

If a site blocks automated access, record the failure and try its archive or another listed source. Continue with independent candidates rather than stopping the whole batch.

## 6. Verify and report

Run:

```sh
python3 scripts/build_readme.py
python3 scripts/build_readme.py --check
python3 -m unittest discover -s tests
```

Also verify that images decode, audio plays, file limits hold, local links resolve and new external download URLs work. Check attribution against each file's stated terms; wiki text licensing does not establish media licensing. Do not describe new media as covered by the repo's CC0 license.

The report should list:

- Sources attempted, access results and retrieval dates.
- Characters updated or added, audio gaps filled and citations added.
- Downloads accepted, rejected or blocked, with reasons.
- Bytes downloaded versus bytes added to the repo.
- Validation results and remaining candidates.

A useful first batch consists of all suitable Commons matches, verified citation updates, available missing-audio clips and up to 20 verified new characters. Fewer additions are acceptable when evidence or downloads are unavailable; report the gaps instead of filling them with guesses.

## Prompt for the executing agent

> Execute `docs/source-expansion-plan.md` for the first batch. Verify the source leads online, download and inspect suitable assets, record provenance, update metadata and regenerate the alphabetical gallery. Start with Commons and missing audio, then use the smaller Miraheze archive for up to 20 new characters. Keep bulk downloads outside Git, continue past blocked sources, run the checks and write the import report. Leave the results ready for review; do not commit, push or publish releases in this run.
