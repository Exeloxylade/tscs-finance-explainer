#!/usr/bin/env python3
"""build_film.py - turn film.html (times as voice cues) into index.html (times as seconds).

HyperFrames reads data-start on <video>/<audio> as fixed numbers, but the voice decides when
things happen. film.html uses tokens; this script fills them from assets/timing.json:
  __DUR__ __MAPDUR__ __BOARD__ __TABLE__ __LOBBY__ and <!--SFX--> (all transition sounds).
Re-run after every new voice take: python build_film.py
"""
import json, re

T = json.load(open("assets/timing.json", encoding="utf-8"))
segs = T["segments"]
vdur = round(T["duration"], 2)
dur = round(T["duration"] + 2.5, 2)          # tail: the closing slate needs ~2 s after the last word
S = {s["id"]: s["start"] for s in segs}


def W(sid, word):
    key = re.sub(r"[^a-z0-9]", "", word.lower())
    for w in next(s for s in segs if s["id"] == sid)["words"]:
        if re.sub(r"[^a-z0-9]", "", w["w"].lower()) == key:
            return w["start"]
    return S[sid]


map_end = W("hook", "By") - 0.1
tok = {"__VDUR__": vdur, "__MDUR__": min(dur, 145.0), "__DUR__": dur, "__MAPDUR__": round(min(16, map_end + 0.6), 2), "__BOARD__": round(map_end, 2),
       "__TABLE__": round(W("hook", "has"), 2), "__LOBBY__": round(W("freeze", "paused") - 0.4, 2)}

# transition swish on every scene change, chip ticks and stamp thuds on their words
sfx = []
def add(file, at, vol, d):
    sfx.append('<audio id="x%d" class="clip" src="assets/%s.wav" data-start="%.2f" data-duration="%.2f" data-volume="%.2f"></audio>'
               % (len(sfx), file, max(0.05, at), d, vol))
cuts = [map_end] + [S[k] - 0.2 for k in ["lost", "blame", "proposal", "butbanks", "chart", "who", "suspects", "ch1", "menu",
                                         "freeze", "why", "gorengan", "pump", "drop", "quit", "fix", "end"]]
for i, c in enumerate(cuts):
    add("swish_" + "abc"[i % 3], c + 0.12, 0.22, 0.3)
add("swish_c", W("end", "currency") + 0.6, 0.22, 0.3)          # the closing red wipe
for sid, w in [("hook", "twelve"), ("chart", "sank"), ("kicked", "sell"), ("gorengan", "Gorengan"), ("gorengan", "Fried"),
               ("pump", "sell"), ("fix", "twice")]:
    add("thud", W(sid, w), 0.32, 0.6)
for sid, w in [("blame", "trillions"), ("chart", "BCA"), ("chart", "Mandiri"), ("menu", "size"), ("menu", "openness"),
               ("menu", "foreigners"), ("funds", "buy"), ("funds", "sell"), ("pump", "Push"), ("pump", "attract"),
               ("suspects", "index"), ("suspects", "currency"), ("suspects", "government")]:
    add("tick", W(sid, w), 0.3, 0.06)

h = open("film.html", encoding="utf-8").read()
for k, v in tok.items():
    h = h.replace(k, str(v))
h = h.replace("<!--SFX-->", "\n  ".join(sfx))
open("index.html", "w", encoding="utf-8").write(h)
print("index.html: %.2f s, %d sounds, map ends %.2f" % (dur, len(sfx), map_end))
