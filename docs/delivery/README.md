# EDITOR PACKAGES — Premiere + After Effects

One package per film, beside the review MP4s in the parent folder. Download the
zip for the film you are working on, **extract it fully**, then open either the
Premiere XML or the After Effects script inside.

| Film | Package | Size | Premiere | After Effects | Captions |
|---|---|---|---|---|---|
| Zendaya V1 | `ZENDAYA_V1_PREMIERE_PORTABLE.zip` | 1.04 GB | yes | yes | estimated |
| Matt Damon V1 | `MATT_DAMON_V1_PREMIERE_PORTABLE.zip` | 1.10 GB | yes | yes | estimated |
| Priyanka Chopra V1 | `PRIYANKA_CHOPRA_V1_PREMIERE_PORTABLE.zip` | 1.05 GB | yes | yes | estimated |
| Dita Von Teese V2 | `DITA_VON_TEESE_V2_PREMIERE_PORTABLE.zip` | 0.73 GB | yes | yes | estimated |
| Jennifer Aniston V13 | `JENNIFER_ANISTON_V13_PREMIERE_PORTABLE.zip` | 1.12 GB | yes | yes | estimated |
| Bruce Lee V1 | `BRUCE_LEE_V1_PREMIERE_PORTABLE.zip` | 0.46 GB | yes | yes | **exact** |
| MrBeast V12 | `MRBEAST_V12_EDITOR_PACKAGE.zip` | 0.2 MB | no — cut list only | no | transcripts |
| Michael Jordan V2 | — | — | — | — | — |

## What is in a package

```
<FILM>.xml                    Premiere / Resolve timeline (File > Import)
<FILM>_AfterEffects.jsx       After Effects project builder (File > Scripts > Run Script File)
<FILM>_NARRATION.srt          narration captions
<FILM>_CHAPTERS.txt           YouTube chapter markers
Media/                        every clip the timeline needs, already trimmed
Graphics_Source/              overlay sources, fonts, card props
Editor Notes/                 script, transcripts, source ranges, rights
TIMELINE_EDL.json             the machine-readable edit
MEDIA_MANIFEST.json           sha256 + original path for every media file
HOW TO OPEN.txt               Premiere path
AE_HOW_TO_OPEN.txt            After Effects path, and how it differs
COPYRIGHT_REVIEW.md           clip-rule measurement for this film
```

## After Effects

There is no `.aep` — this pipeline renders straight to MP4 and never had one,
and After Effects cannot import a Premiere XML. Instead each package carries a
`.jsx` that **builds the comp natively**: it imports the media, lays every cut
on the timeline at the right in/out points, sets layer order and colour labels,
files everything into project-panel folders, and drops comp markers at the
block boundaries with the narration in the marker comments.

1. Extract the zip. Keep the `.jsx` beside the `Media` folder.
2. After Effects → File → Scripts → Run Script File…
3. Pick `<FILM>_AfterEffects.jsx`.

If AE blocks the script, enable Preferences → Scripting & Expressions → *Allow
Scripts to Write Files and Access Network*.

**Known limit:** After Effects has no multi-track audio mixer, so dialogue,
narration and music arrive as separate audio layers rather than the A1–A6 track
pairs in the Premiere sequence, and levels are unmixed. The rendered review MP4
in the parent folder stays the reference for the final balance.

Each script was executed against a mock After Effects API before delivery, and
every clip's in-point, out-point, source trim, layer order and marker position
was checked against the EDL. Import into the real application was **not** tested
here.

## Captions

`*_NARRATION.srt` for the six film packages is **estimated**: block start and
end times are exact, but sentence splits inside a block are interpolated by
character count and will drift a second or two. Conform them against the
narration audio before publishing.

The exception is **Bruce Lee**, whose beat timings are real per-beat values
aligned to the narration file — those cues are exact.

## Two films are not full packages

- **MrBeast V12** — the build tree was overwritten and no source media survives.
  The package is the complete cut list (every segment's source video and in/out
  timecode), the 37 soundbites with transcripts, the owner's shot-by-shot edit
  notes, and a `yt-dlp` script to re-download the five sources. No XML, no AE
  script: both would point at files that do not exist.
- **Michael Jordan V2** — nothing survives on disk beyond the review MP4. There
  is no package to build.

## Before you re-cut anything

Read `COPYRIGHT_REVIEW.md` inside the package, and
`COPYRIGHT_REVIEW_ALL_FILMS.md` beside this file. Several of these edits carry a
recorded footage waiver; MrBeast V12 and Bruce Lee V1 predate it and do not meet
the current clip rules.
