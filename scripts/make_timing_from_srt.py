#!/usr/bin/env python3
"""Build timing.js from the original .srt for the first 180s, so rebuilt graphics
can key to the SAME seconds as the reused original audio. We define our own
segment ids at the real cue seconds; words inside a segment are spread evenly
across the segment span (good enough for caption karaoke + visual cues)."""
import json, re, sys

SRT = r"C:\Users\Ahmad\.kiro\crew\workspace\videos\copy-21G0C\_ref\ref.en.srt"

# our scene segments: (id, start, end, text). Times are the real subtitle seconds.
SEGS = [
    ("hook",     2.6,  16.6, "On Friday, Indonesia's stock market had its worst day since 1998. 11.6% evaporated in a single day."),
    ("billions", 10.0, 16.6, "Since January, about 270 billion dollars of share value has gone up in flames."),
    ("msci",     16.6, 24.7, "Wall Street blames one big company, MSCI, and you've probably never heard of them."),
    ("lists",    24.7, 30.0, "But it writes the lists of stocks that most of the world's big funds copy."),
    ("kick",     27.6, 33.0, "And on Thursday night, it voted to kick Indonesia off its emerging markets list."),
    ("notfast",  33.0, 38.0, "So MSCI did it. Video's over. Not so fast."),
    ("banks",    38.0, 49.1, "I want you to look at the banks. Before MSCI even lifted a finger, Indonesia's three biggest banks had already lost over a quarter of their value."),
    ("index",    49.1, 60.4, "Over that same stretch, the index, which tracks the entire market, rose 19%. The banks were bleeding while everything else went up."),
    ("whodunnit",60.4, 73.6, "So who really crashed Indonesia? We did the grunt work, fueled on unhealthy amounts of coffee. We screened 962 stocks and read 30 years of IMF files."),
    ("suspects", 73.6, 90.3, "As in every murder mystery, there are several suspects. One did an insane amount of the damage, and it's the reason we're buying one bank that pays 14% dividend."),
    ("chapter1", 90.3, 107.8, "Suspect one, the index company MSCI. Think of MSCI as the people who write the menu. They sort every country into lists: developed, emerging, and frontier."),
    ("funds",    107.8,129.5, "Then enter index funds. Autopilot funds. They buy whatever is on MSCI's list. If you get kicked off, those funds have to sell. And in January, MSCI froze Indonesia."),
    ("freeze",   129.5,145.0, "No new Indonesian stocks could get on the menu. Nobody could tell who owned the companies. And locals had a word for these stocks."),
    ("gorengan", 145.0,167.7, "In menu terms, it's fried food. The locals called it gorengan. A few insiders owned almost all the shares, pumped the price, then dumped on whoever was left."),
    ("fix",      167.7,180.0, "After the freeze, the index fell 8% in two days. The heads of the stock exchange and the regulator both quit. So what did Jakarta do to fix this?"),
]

def words_for(text, start, end):
    toks = text.split()
    n = len(toks)
    span = max(0.3, end - start)
    out = []
    for i, w in enumerate(toks):
        ws = start + span * (i / n)
        we = start + span * ((i + 1) / n)
        out.append({"w": w, "start": round(ws, 2), "end": round(we, 2)})
    return out

def lines_for(words, maxw=6):
    lines = []
    for i in range(0, len(words), maxw):
        chunk = words[i:i + maxw]
        lines.append({"start": chunk[0]["start"], "end": chunk[-1]["end"], "words": chunk})
    return lines

segments = []
for sid, a, b, text in SEGS:
    w = words_for(text, a, b)
    segments.append({"id": sid, "start": a, "end": b, "text": text,
                     "words": w, "lines": lines_for(w)})

data = {"segments": segments, "duration": 180.0}
with open(r"C:\Users\Ahmad\.kiro\crew\workspace\videos\copy-21G0C\assets3\timing.js", "w", encoding="utf-8") as f:
    f.write("window.__TIMING = " + json.dumps(data) + ";\n")
with open(r"C:\Users\Ahmad\.kiro\crew\workspace\videos\copy-21G0C\assets3\timing.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
print("wrote timing.js with", len(segments), "segments, duration 180s")
