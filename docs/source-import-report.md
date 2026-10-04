# Source import — October 4, 2026

Executed the [source expansion plan](source-expansion-plan.md), using the references in `/home/gorden/Downloads/ib`. The download run left the results ready for review and did not commit, push or publish a release.

| Coverage | Before | After |
|----------|-------:|------:|
| Characters | 48 | 68 |
| Characters with audio | 11 | 31 |
| Audio with source credits | 0 | 25 |
| Characters with origin citations | 3 | 21 |
| Characters with Commons images | 0 | 16 |

The gallery still groups characters by first letter. Existing slugs, sources and media remain intact. Credits now appear beside images and audio.

## Sources checked

All checks were made on October 4, 2026. Exact URLs, timestamps and response hashes are in [source access](../data/source-access.json).

| Source | Result |
|--------|--------|
| Wikimedia Commons | API and downloads accessible; 34 files across three categories, 16 thumbnails imported |
| Know Your Meme | Nine character pages accessible; seven new origin citations and two existing citations updated |
| Wikipedia / Wikidata | Accessible; used to cross-check names and existing history |
| MyInstants | Accessible; 68 gap/alias searches and 11 existing-clip checks |
| Voicemod Tuna | Accessible; 45 further searches, uploader credits retrieved |
| August 2025 Miraheze archive | Metadata, XML and 909 MB image archive accessible; checksums verified |
| WikiOasis / Namu Wiki | Live pages returned HTTP 403 |
| August 2026 WikiOasis archive | Metadata accessible; 20.22 GB image archive deferred because the smaller archive filled the batch |
| TikTok original posts | Two of 29 oEmbed checks succeeded; 27 returned HTTP 429 |

## Imported and excluded

Added 20 distinct characters with archived lead images and original-video citations. The XML was streamed and reduced to the latest revision per title; archived titles, image members, dump URLs and evidence hashes are preserved in [source pages](../data/source-pages.json).

Added 36 thumbnails, two full PNGs and 20 MP3s, including [Brri Brri Bicus Dicus Bombicus](../characters/brri-brri-bicus-dicus-bombicus). Fifteen existing characters gained Commons images; Ecco Cavallo Virtuoso gained both Commons and archive sources. Five existing MP3s matched downloaded files exactly, allowing credits without replacement. Six existing clips remain without confirmed source links.

**Audio review used FFmpeg decoding and speech recognition. Human listening was not performed.** The selected narration/name excerpts were identifiable; [audio review](../data/audio-review.json) records the method and decisions. Audition the clips before publication. Three downloaded candidates were excluded: Piccione Macchina was labelled a song, Garam Mararam was an unconfirmed loud edit, and “Mateo” did not identify the intended character.

Excluded Commons music, photographs, toys, commentary, alternate variants and redundant Tung audio. Bombardiro Gatino and Merluzzini Marraquetini remain leads without verified original-post evidence. Il Mago Tiramisù was excluded as a fan creation with another character's cited video. Only one suitable Commons image per character was retained; duplicate originals did not get extra full PNGs.

Added 18 origin citations and 13 aliases. Uncertain creator claims were omitted. Penguinelli Cactussini keeps only the month because the archived day conflicts with its post ID timestamp. Post IDs were used only to detect inconsistencies, never to invent publication dates. [Citation records](../data/source-citations.json) distinguish facts from unresolved claims.

Commons files retain their stated per-file terms. Archived images and soundboard uploads have unknown media licenses. Wiki text terms and the repository's CC0 license do not establish media rights.

## Downloads and checks

Successful cached source payloads total **946,223,033 bytes**; the image archive accounts for 909,474,839. Added media totals **9,814,432 bytes** across 58 files; new files including metadata and pages total about **10.2 MB**. Package/model installs, failed responses, retries and HTTP overhead are excluded from the download measurement. Bulk files remain under `/tmp/brainrot-source-import/` outside Git.

[Provenance](../data/source-imports.jsonl) contains 63 records: 58 new files and five existing audio matches, with original/final SHA-256 hashes and transformations. Thumbnails were resized proportionally without upscaling. Audio was copied unchanged; no clip was trimmed or converted.

Generation and `--check` passed; all nine tests passed. All 38 imported images and 25 recorded audio files decoded, size limits held, local links resolved, and all 42 direct download URLs returned HTTP 200. A repeat import reused cached downloads and preserved all 183 media files without duplicate characters or provenance records. Details are in [validation](../data/source-validation.json).

There are **37 remaining audio gaps** and **150 unreviewed archive leads**. [Source discovery](../data/source-discovery.json) lists names, searches, exclusions and access failures for the next batch; unreviewed leads are not approved additions.
