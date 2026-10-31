---
name: tscs-finance-explainer
description: Make a TSCS-style finance / markets documentary video in code - the off-white topographic background, dark-red accent, bold top-left titles with one red keyword, charts that draw on (bars grow, line charts trace to a dot), framed real-footage/photo cards, numbered chapter slates, news-ticker lower-thirds, karaoke captions, and a "Follow the dividend." end card. One continuous 1920x1080 film, free edge-tts voice, HyperFrames render. Use for "markets explainer", "finance breakdown", "stock crash story", or to copy the TSCS / finance-YouTube look.
---

# tscs-finance-explainer: the finance-documentary look in code

> **Read ..\video-automation\QUALITY.md first.** Start every film with `vm new <name> --from indo-crash`; never from a blank page.

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

## Real media: map + document + footage (the news workflow)
This style is for REAL news, so it pulls in real sources and SHOWS the source on screen
(you also credit in the video description). Three capabilities, each with a visible credit:

**A. Real satellite MAP opener** - a white LINE draws around the country's coast (not dots).
Country outline: Natural Earth `ne_50m_admin_0_countries.geojson` (GitHub nvkelso/natural-earth-vector),
pick the country, keep island rings with >= 12 points, save the bare geometry (NOT a FeatureCollection),
add `"areas":[{"id":"indo","file":"indonesia.geojson"}]` to shots.json and bake. The track then has
`areas[0].xy[frame]` (flat x,y list) + `rings` (points per island). Draw one SVG path per ring with
`pathLength=1`, `stroke-dasharray="1 1"`, animate `stroke-dashoffset` 1 -> 0 (all islands together),
a wide faint glow path under a thin white line, then a faint fill. Template: `templates\real-media.html`.
(The old city-dot version is below; use dots only for named cities, after the outline.)
Use the `map-video` skill's baker - it is free + keyless on Esri imagery:
1. Nominatim (1 req/s, with a User-Agent) for each city's lat/lng.
2. `map\shots.json`: `"style":"satellite"` (NOT "dark" - CartoDB dark now needs an API key),
   `"projection":"globe"`, `places[]` for every dot, `keys[]` for the camera (globe -> dive).
   Stills check first: `node bake-map.mjs shots.json --stills 0,8,16`.
3. Full bake (background): `Start-Process node bake-map.mjs ...` -> `indo.mp4` + `indo-track.json`
   (per-frame screen x/y of each place, as `xy[frame] = [[x,y],...]` in `places` order).
4. In the film: `<video src="assets/indo.mp4" muted>` under the graphics (filter brightness 0.6
   to darken like the original), city dots = absolutely-positioned DOM moved from the track each
   frame (`TSCS.mapReveal`). Credit on screen: "Map: Esri World Imagery / OpenStreetMap".

**B. Real DOCUMENT, zoom to the exact line.** Use `ai-news-video\tools\capture.mjs`:
`node capture.mjs <url> --out source --name doc --phrases phrases.json` -> `doc.png` (3840 wide)
+ `doc.boxes.json` (phrase boxes in PNG px). Put the PNG in a red-bordered `#docview` with an
inner `#docwrap` you transform; `TSCS.docZoom({wrap,box,...})` pushes the camera to the box and
sweeps a red `#hl` highlight over the line on the spoken word. Credit: 'Source: <site>, "<title>" (<url>)'.

**C. Real NEWS footage** - the newest clips about the story, not archive film:
1. Find: `python -m yt_dlp "ytsearch12:<story keywords>" --flat-playlist --print "%(id)s | %(channel)s | %(title)s"`.
   Prefer news desks (Reuters, Bloomberg, CNA, AP) and clips from the last days of the story.
2. Take only a short part: `python -m yt_dlp <url> -f "bv*[height<=720]" --download-sections "*00:00:15-00:00:23" --force-keyframes-at-cuts -o raw\reuters.%(ext)s`.
3. Look before using: `ffmpeg -i raw\x.mp4 -vf "fps=0.5,scale=480:-2,tile=4x1" -frames:v 1 _x.jpg` - keep the shot
   that shows the thing (trading board, exchange lobby, price table), skip presenters talking.
4. Convert + credit: `get_footage.py --file raw\x.mp4 --out assets --name news_board --start 2 --dur 6 --credit "Source: Reuters"`.
5. On screen: a red-framed `<video muted>` + "Footage: Reuters" in the corner.
People photos (presidents, ministers, CEOs): `get_image.py "<name> official portrait"` - official portraits are
usually public domain on Wikimedia; print "Photo: <author> / Wikimedia Commons".
Charts from real numbers: see the `finance-charts` skill.

**C2. Archive / generic footage card.** `video-automation\tools\get_footage.py`:
- Wikimedia: `get_footage.py "<query>" --out assets --name clip --list` then `--pick N --start s --dur d`.
- The SOURCE's own clip (the realistic path for news): download it yourself (yt-dlp etc.), then
  `get_footage.py --file <path> --name clip --credit "<source>"` to convert + credit.
Put `<video src="assets/clip.mp4" muted>` in a red-bordered card; `TSCS.footageCard(el,t,on,off)`
slides it in. The on-card caption IS the credit (from `window.__CREDITS[name]` or your `--credit`).

Rule: EVERY real asset shows its source on screen. Copyright is handled by crediting on screen +
in the description; keep excerpts short and commentary-driven (fair use), rebuild numbers as your
own charts, and never present another channel's footage as your own unlabelled.

Runtime helpers for all three: `TSCS.mapReveal`, `TSCS.docZoom`, `TSCS.footageCard` (in `tscs.js`).
Template: `templates\real-media.html` (map -> document -> footage, each credited).

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
2. **Voice**: Gemini with feeling - `vm voice <name>` (project.json `"voice": {"engine": "gemini"}`), see "Voice with feeling". edge-tts (`tts.py`) only if Automated Lunch Free is not available.
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

## Voice with feeling (Gemini, via Automated Lunch Free)
edge-tts reads flat. Use the Gemini voice the user already set up in Automated Lunch Free; it takes
a delivery direction (lean in on numbers, pause before twists, stress one word per sentence).
```
cd "D:\Agentic AI\Automated Lunch Free"
Start-Process node_modules\electron\dist\electron.exe -ArgumentList 'scripts/voice-script.js --script "<proj>\script.json" --out "<proj>\voice_gemini"' -WorkingDirectory (Get-Location) -RedirectStandardOutput $log -WindowStyle Hidden
```
- One continuous take (even voice), saved keys + key rotation, Whisper + the app's aligner for word times.
- Writes `voice.wav`, `timing.json`, `timing.js` in the same shape as `tts.py` - films need no change.
- Script text may hold `<short pause>` / `<long pause>`; per segment `"pause_after": "short|long"`.
- Default voice `en-us-enzo` (storyteller); `--style "..."` overrides the direction. Keys are never printed.
- Then normalise TWO-PASS (`loudnorm` measure, then `linear=true`) to -14; one pass undershoots ~2 dB.
Tested: 342 words, 134 s, Whisper matched 336; loudness range 4.6 LU vs 3.7 for edge-tts.

## Cue-driven film (every time follows the voice)
`templates\film.html` (lives in a project as `src\film.html`) + `scripts\build_film.py` + `templates\project.json`: the film never holds a hand-typed second. Fastest start: `vm new <name> --from indo-crash`, then `vm all <name>`. JS uses
`S(seg)`, `E(seg)`, `W(seg, word)` from timing.js; `<video>`/`<audio>` start times are tokens
(`__DUR__`, `__BOARD__`, `<!--SFX-->`) that `build_film.py` fills from timing.json. New voice take ->
`python build_film.py` -> render. Motion helpers in the template (use them on every element):
`scene()` slide-in/out, `card()` pop with overshoot + Ken Burns push on its photo, `bk()` note slide,
`stamp()` drop-in, `title()` headline rising out of a mask, `count()` numbers counting to the spoken
value, `bg()` full-bleed photo with slow push + drift, `flow()` dots travelling between boxes,
red diagonal `wipe` into chapter slates. Rule: a real photo or footage in EVERY scene
(`image_hunt.py`), something new on screen every 1-2 s.
SFX level: swish 0.22, thud 0.32, tick 0.30 (peaks ~17 dB under the voice). At a cut that starts a
new sentence the voice itself dominates `reva\scripts\sfx_probe.py`, so check SFX against a voice-only run.

## Technique: transition sound (measured)
Reference transitions (first 3 min, 13 cuts): bright part ~0.2 s, +19.4 dB in 4-8 kHz over its surroundings,
+4.9 dB low body. The old 0.9 s whoosh was 3.5x longer and played at 0.45-0.6 under a -1 dBFS peak.
Use `swish_a/b/c.wav` (make_audio.py) at 0.55, 0.15 s after each cut; `tick.wav` 0.5 for chips; `thud.wav` 0.6
for a stamp. No risers. Verify with `reva\scripts\sfx_probe.py`. Result on `videos\indo-crash`:
+17.1 dB / 0.20 s / +6.4 dB, film at -13.8 LUFS.

## Technique: data line chart with photo cards (measured, eye-checked)
Template `templates\technique-linechart.html` (27 s, own script). Numbers measured at 1920x1080:
- Paper `#e9e8e6`, contour lines `TSCS.topo({levels:34, scale:1600, octaves:3, stroke:"#c6c2bd", width:2.6})`.
- Title Poppins ExtraBold 52 px, all accent red `#8b1a2b`, x 90 / top 62. Note line Poppins 24 px grey at x 205 / top 183.
- Plot x 205..1220, y(120)=307, y(60)=835; ticks every 10; axis text 32 px; baseline 45 px under the plot.
- Lines are RAW daily closes (`curve:"linear"`): hero red 6 px, others grey/tan 3-3.5 px; hollow ring end markers r 9;
  end labels 30 px bold in the line colour, shown only once the line finishes, 56 px apart.
- Bank lines draw in 2.0 s from the word naming them; the comparison line arrives on its own word, also 2.0 s.
- Photo cards 220x135, 4 px border `#c8323e`, tilted -2 / +1.5 / -1 deg, black name tab under the left edge,
  pop in 0.4 s apart (rise 26 px + scale 0.92 -> 1), cleared before the next line arrives.
- Black notes `#1c1c1c`, Poppins Bold 28 px, x 1490, width fits text (max 360), stacked 90 px apart, slide in 24 px.
- Stamp: red, ExtraBold 40 px, rotated -2 deg, lands from scale 1.25 on the number word, impact SFX.
- Something new appears every 1-2 s. No camera move on this scene.
Fonts: Poppins (OFL, Google Fonts) in `lib/fonts`, loaded with @font-face - system fonts do not match.

## Technique: document card + highlighter (measured, eye-checked)
Template `templates\technique-document.html` (14 s, self-contained). Numbers measured at 1920x1080:
- Paper `#f3f1ec` background with faint contour lines `TSCS.contour(svg, 1920, 1080, 14)`.
- Viewport `#docview`: x 120, top 250, 960x640 px, border 4 px solid `#8d1b2d`, box-shadow `0 24px 70px rgba(0,0,0,0.32)`, `overflow: hidden`.
- Document image: 3840 px wide high-res capture (`capture.mjs`). Overview scale `s0 = 960 / 3840 = 0.25`.
- Target phrase box: `box = { x, y, w, h }` in 3840 px coordinates.
- Camera push: smooth 2.0 s ease from overview (`s0`) to close-up `s1 = (viewW * 0.68) / box.w`.
- Red highlighter `#dochl`: `background: rgba(141,27,45,0.32); border-bottom: 6px solid #8d1b2d;` sweeps `scaleX(0 -> 1)` over 0.8 s across the phrase on the spoken cue.
- Chip: x 1140, top 250, red `#8d1b2d` background, white text, 18 px uppercase, pops in before the highlight.
- Side card `.doc-card`: x 1140, top 310, width 660 px, background `#fbfaf6`, border 3 px solid `#8d1b2d`, shadow `0 18px 50px rgba(0,0,0,0.18)`.
- Synchronized quote highlight: `background: linear-gradient(90deg, rgba(168,32,58,0.25) 0 var(--p), transparent var(--p))` sweeping at the exact same moment as the document line.
- Audio: `swish_a.wav` (vol 0.22) on entry; `tick.wav` (vol 0.30) on highlight sweep trigger.

## Full news explainer template (best result so far)
`templates\news-explainer.html` - 2 min 24 s, 20 scenes, own script + own edge-tts voice,
tested 2026-10-31 (`videos\indo-crash`, -14.9 LUFS, peak -1.45 dBTP). Uses every skill:
coastline-line map opener (map-video) -> real news clips (yt-dlp sections) -> real-data charts
(finance-charts: YTD area, rebased bank lines with a "took office" marker, January drop line,
float bars, currency area) -> document zoom (capture.mjs) -> menu/tier board with real flag
images (flagcdn.com, local PNGs - emoji flags do not render on Windows Chrome) -> leader photos
(Wikimedia) -> numbered black chapter slates -> karaoke captions -> source line on every moment.
Lessons from this build:
- Fact-check every number in the script against the data you pulled BEFORE making the voice
  (the first draft said the wrong date and "a third this year"; the data said 16 Oct and -41.5%).
- End a chart's draw-on on the word that states its number, so the chip and the line agree.
- Captions sit 96 px from the bottom: keep chart boxes <= y 840 so axis labels are not covered.
- Captions need two looks: dark text with a paper stroke on light scenes, white with a black
  stroke on dark scenes - toggle a class from the same `dark` value that drives the background.
- Mark made-up shapes on screen ("Illustration, not real data").
- No photo of a person? Use a plain name card, never a wrong face.

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
