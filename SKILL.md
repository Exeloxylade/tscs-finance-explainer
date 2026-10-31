---
name: tscs-finance-explainer
description: Make a TSCS-style finance / markets documentary video in code - the off-white topographic background, dark-red accent, bold top-left titles with one red keyword, charts that draw on (bars grow, line charts trace to a dot), framed real-footage/photo cards, numbered chapter slates, news-ticker lower-thirds, karaoke captions, and a "Follow the dividend." end card. One continuous 1920x1080 film, free edge-tts voice, HyperFrames render. Use for "markets explainer", "finance breakdown", "stock crash story", or to copy the TSCS / finance-YouTube look.
---

# tscs-finance-explainer: the finance-documentary look in code

The look (reverse-engineered from TSCS "WTF Just Happened to Indonesia", 2026):
off-white paper background with faint grey topographic contour lines; one dark red
accent (`#8d1b2d` fill, `#a8203a` text) over black/grey text; a bold sans title top-left
with ONE red keyword; "TSCS" brand lockup top-right every frame; a small footer tag
bottom-left ("01 - THE WORST DAY SINCE 1998"). Content is data journalism: bar charts
that grow on the voice cue, line charts that trace left-to-right to a red dot, small red
or black callout chips pinned to the chart, big number lockups ("$270bn"), framed real
footage/photo cards with a red border + caption tab, numbered chapter slates on black,
news-ticker lower-thirds early on, and a clean "TSCS / Follow the dividend." end card.
Calm, fast VO (~150 wpm). Target ~-15 LUFS.

## Files

| File | Job |
|---|---|
| `scripts/tscs.js` | `window.TSCS` runtime: `init`, `cue`, `ramp`/`ease`, `contour` (bg lines), `title`, `chip`, `card`, `barChart`, `lineChart`, `captions`. Pure function of t, HyperFrames-safe. |
| `templates/index.html` | A full working ~40s film (the Indonesia opening). Copy it, swap the script, the chart data, the chapter text, the footage card. |

Leans on the shared video-automation tools (do not edit, copy if needed):
`tts.py`, `words.py`, `get_image.py`, `get_footage.py`, `make_audio.py`, `probe.mjs`, under
`C:\Users\Ahmad\.kiro\crew\skills\video-automation\tools\` (+ `make_audio.py` in `3d-motion-video\scripts`).
Pin `npx.cmd -y hyperframes@0.8.222`. Write HTML UTF-8 **without BOM** - use the file-edit
tools, NOT PowerShell `Set-Content -NoNewline` (it double-encodes `-`, `.`, `/` into mojibake).

## Route

1. **Script** `script.json`: a hook (the worst number), one segment per beat (each beat = one
   chart / number / card), a payoff. `"rate": "+6%"` ~150 wpm. One `id` per beat -> animation cue.
2. **Voice**: `python ...\tools\tts.py script.json --out assets` -> `voice.wav` + `timing.js`.
   Then `python ...\tools\words.py assets\timing.json` to copy exact cue words.
3. **Sound**: `python ...\3d-motion-video\scripts\make_audio.py --out assets --duration <len> --bpm 92 --mood dark`.
4. **Project**: make `assets lib renders`; copy `templates\index.html` -> `index.html`,
   `scripts\tscs.js` -> `lib\tscs.js`, and a `hyperframes.json` + `package.json` (pin 0.8.222);
   `meta.json` `{id,name}`.
5. **Build**: edit `index.html` - swap the title text, the chart data (`barChart`/`lineChart`
   cfg), the chapter slate, the footage card `src`. Key every reveal to a cue: `cue("beat","word")`.
   Real footage: `get_footage.py` (or `--file` your own) sits in a `.card` with a red border;
   real photos: `get_image.py` -> `.card` + the printed credit on screen. Only free/licensed
   or your-own media; never pass someone else's broadcast footage as your own.
6. **Finish**: `probe.mjs` for JS errors, `check --json` (fix every error - `content_overlap`
   = two blocks share a box while both visible; `contrast_aa_failure` = darken the text),
   `snapshot --at <cue times>` and READ the contact sheet, `render -q delivery`, ffmpeg share
   copy, measure LUFS with `loudnorm=print_format=json` (want ~-15, peak <= -1 dBTP).

## Craft rules (what makes it read as TSCS)
- Background is NEVER plain white - it is `#f3f1ec` paper + faint contour lines (`TSCS.contour`).
- Exactly ONE red. Everything else is black/grey. The red marks the thing that matters.
- Title top-left, red keyword, short. Brand top-right, footer bottom-left, every frame.
- Charts DRAW ON (grow/trace) on the voice word, never pop in finished. Value label rides the bar.
- Numbers are big lockups with a small grey caption under them ("$270bn / of share value gone").
- Footage/photos are FRAMED cards (red border + caption tab), not full-bleed - they float on the paper.
- Chapters are numbered black slates ("05 / Jakarta doesn't need MSCI") between sections.
- Captions: one line, current word red, bottom band. Ticker lower-third only in the news-y open.
- End on the brand + tagline + a small disclaimer. Calm VO; music 0.13 under the voice.

## Honesty / rights
- You can't WATCH or hear a source video; read frames (contact sheets) + subtitle text and
  MEASURE sound with ffmpeg. Say "measured", never "I heard it".
- This rebuilds the STYLE. A 1:1 copy of someone's video - their footage, their exact wording,
  their numbers - is for learning or a private remake, not for re-publishing as your own.
  Swap owned footage/logos for free or original assets before anything goes public.

## Tested
2026-10-31: reverse-engineered TSCS "WTF Just Happened to Indonesia?" (1920x1080, 1094s,
154.6 wpm, -15.98 LUFS). Rebuilt the ~42s opening in this style: chapter slate -> red "worst
day" title -> $270bn lockup -> framed Jakarta card + ticker -> MSCI beat -> "look at the banks"
bar chart (3 banks down, index up) -> TSCS end card. Rendered 42s, measured -14.61 LUFS,
true peak -1.45 dBTP. The house style matches; raw broadcast footage in the original is not
reproduced (it is other channels' footage).
