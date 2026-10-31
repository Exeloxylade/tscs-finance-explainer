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
| `scripts/tscs.js` | `window.TSCS` runtime. Primitives: `init`, `cue(id[,word])`, `ramp`/`ease`, `seeded`, `contour` (bg lines), `title`, `chip`, `card`, `captions`, `stage` (fade a list in sequence). Charts/scenes: `barChart`, `lineChart`, `dualLine` (two lines one axis), `dotGridCount` (dots fill + number counts up), `tiers` (developed/emerging/frontier ladder, one highlighted). Pure function of t, HyperFrames-safe. |
| `scripts/make_timing_from_srt.py` | Build `timing.js` from a source `.srt` when you REUSE the original audio (see below). Define your scene segments at the real subtitle seconds; words spread evenly across each span. |
| `templates/index.html` | A ~40s opening film (own voice). Copy for a short piece. |
| `templates/index-3min.html` | The full 3-minute 6-scene film (reused original audio): hook -> MSCI-did-it -> banks dual-line -> who-crashed dot-grid + doc cards -> three suspects -> chapter-1 MSCI tiers. Copy this for a long, multi-scene finance breakdown. |

## Reuse the original audio (exact-copy mode)
When the goal is a 1:1 timing copy, skip `tts.py` and use the source's own audio:
1. `ffmpeg -ss 0 -t <sec> -i <ref.mp4> -vn -c:a pcm_s16le -ar 48000 assets/voice.wav` (voice+music together).
2. Edit `make_timing_from_srt.py`: list your scene segments `(id, start, end, text)` at the REAL
   subtitle seconds, run it -> `assets/timing.js`. Now `cue("id","word")` lines graphics up to the audio.
3. Do NOT add your own music clip - the reused track already has it. Measure, don't add.

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

## New scene builders (added for the 3-min build)
- `dualLine({svg,x,y,w,h,lineA:{pts,color,label},lineB:{...},cueOn,span})` - two lines trace
  together on one axis with gridlines + end dots + labels. Use for "X down while Y up".
- `dotGridCount({host,cols,rows,from,to,numEl,cueOn,span})` - a grid of red dots fills while a
  big number counts up (e.g. "962 stocks screened"). `host`/`numEl` are positioned DOM.
- `tiers({host,rows:[{label,note,hot}],cueOn,stagger})` - the menu ladder (developed/emerging/
  frontier), the `hot` row in red. Rows slide in staggered.
- `stage(els, t, cueOn, stagger, dur)` - fade a list of DOM els in one after another (doc cards,
  suspect cards). Gate each scene's whole group with a `ramp(in)*(1-ramp(out))` opacity so a
  chart from one scene does NOT linger into the next (the bug caught in the 3-min test).

## Tested
- 2026-10-31 (opening): reverse-engineered TSCS "WTF Just Happened to Indonesia?" (1920x1080,
  1094s, 154.6 wpm, -15.98 LUFS). Rebuilt ~42s opening (own voice): chapter slate, red "worst
  day" title, $270bn, Jakarta card + ticker, MSCI beat, banks bar chart, end card. 42s, -14.61 LUFS.
- 2026-10-31 (first 3 min, exact-copy mode): reused the source's own 0-180s audio, rebuilt 6
  scenes keyed to the real subtitle seconds - hook, MSCI-did-it (NY card + "THE END / not so
  fast"), banks dual-line (-29% vs +19%), who-crashed (dot-grid counting to 962 + IMF/World Bank
  doc cards + CASE OPEN), three suspects (MSCI/rupiah/state cards, suspect 3 red-boxed, 14%),
  chapter-1 MSCI (tiers menu + freeze + gorengan). Rendered 180.0s, measured -17.54 LUFS, peak
  -1.15 dBTP. `compare.py` vs the original's first 3 min: **84% overall** (colour 85, bright 85,
  layout 82), duration delta 0.01s. The weak seconds (2-13s) are exactly where the original uses
  borrowed broadcast footage (IGR anchor, CNA "$138bn" ticker) - that footage is other channels'
  and is intentionally re-expressed in the TSCS house style, not copied pixel-for-pixel.
