'use strict'
/**
 * Voice a ready script with the app's Gemini voice (saved keys, key rotation), then time every word
 * with the app's Whisper + aligner. Writes the same files as video-automation's tts.py, so any
 * HyperFrames film that reads assets/timing.js works unchanged.
 *
 *   electron scripts/voice-script.js --script <script.json> --out <assets dir> [--voice en-us-enzo] [--style "..."]
 *
 * script.json: { "segments": [ { "id": "hook", "text": "...", "pause_after": "short|long|none" }, ... ],
 *                "caption_words": 6, "voice": "...", "style": "..." }
 * Text may hold <short pause> / <long pause> tags (never spoken, never captioned).
 * Writes voice.wav (normalised to about -15 LUFS), timing.json, timing.js. Keys are never printed.
 */
const fs = require('fs')
const path = require('path')
const { app } = require('electron')

const argv = process.argv.slice(2)
const arg = (n, d) => { const i = argv.indexOf('--' + n); return i >= 0 && argv[i + 1] ? argv[i + 1] : d }
app.setPath('userData', process.env.FL_USER_DATA ? path.resolve(process.env.FL_USER_DATA) : path.join(app.getPath('appData'), 'Free Lunch'))
const M = f => require(path.join(__dirname, '..', 'src', 'main', f))
const say = t => console.log(`[${new Date().toISOString().slice(11, 19)}] ${t}`)

const STYLE = 'You are a documentary YouTuber telling a true financial thriller to a friend. Warm, curious and confident, ' +
  'like a story you cannot wait to tell - not a newsreader reading copy. Vary your pitch and pace: lean in and slow down ' +
  'on big numbers and reveals, speed up a little through set-up lines, let a short silence land before a twist. ' +
  'Stress the one word in each sentence that carries the meaning. Rhetorical questions rise and hang for a beat. ' +
  'Dry, understated humour on the ironic lines. No breathing sounds, sighs, laughter or music.'

app.whenReady().then(async () => {
  try {
    const scriptPath = path.resolve(arg('script'))
    const out = path.resolve(arg('out'))
    const S = JSON.parse(fs.readFileSync(scriptPath, 'utf8'))
    const voice = arg('voice', S.voice_gemini || 'en-us-enzo')
    const style = arg('style', S.style || STYLE)
    const capN = S.caption_words || 6
    fs.mkdirSync(out, { recursive: true })
    const speech = M('speech.js'), tts = M('tts.js'), fx = M('ffmpeg.js'), whisper = M('whisper.js')
    const { alignWords } = M('align.js')
    if (!whisper.ready()) throw new Error('Whisper model is not downloaded in the app yet.')

    // one continuous take keeps the voice even; pause tags mark section breaks
    const segs = S.segments.map(s => ({ ...s, text: speech.cleanNarrationText(s.text) }))
    let take = ''
    segs.forEach((s, i) => {
      take += (i ? ' ' : '') + s.text
      const p = s.pause_after || 'none'
      if (i < segs.length - 1 && p !== 'none' && !/<(short|long) pause>\s*$/.test(s.text)) take += ` <${p} pause>`
    })
    const raw = path.join(out, 'voice_raw.wav')
    say(`Voice: ${voice}, ${speech.spokenWords(take).length} words, one take`)
    await tts.speak(take, voice, style, 'en', raw, null, say)

    // normalise to about -15 LUFS and add 0.4 s lead-in so the first word is not on frame 0
    const wavOut = path.join(out, 'voice.wav')
    await fx.ff(['-i', raw, '-af', 'adelay=400|400,loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000', '-ac', '1', '-c:a', 'pcm_s16le', wavOut])
    const dur = await fx.duration(wavOut)

    say('Timing: Whisper is listening...')
    const v16 = path.join(out, 'voice16k.wav')
    await fx.ff(['-i', wavOut, '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', v16])
    const heard = await whisper.recognize(v16, 'en', null)
    const tokens = segs.flatMap(s => speech.spokenWords(s.text).map(w => ({ w, seg: s.id })))
    const timed = alignWords(tokens.map(t => t.w), heard, [0, dur])

    const segments = segs.map(s => {
      const words = timed.map((w, i) => ({ w: w.text, start: +w.start.toFixed(3), end: +w.end.toFixed(3), seg: tokens[i].seg }))
        .filter(w => w.seg === s.id).map(({ w, start, end }) => ({ w, start, end }))
      const lines = []
      for (let i = 0; i < words.length; i += capN) {
        const ws = words.slice(i, i + capN)
        lines.push({ start: ws[0].start, end: ws[ws.length - 1].end, words: ws })
      }
      return { id: s.id, text: speech.stripVoiceTags(s.text), start: words[0]?.start || 0, end: words[words.length - 1]?.end || 0, words, lines }
    })
    const data = { duration: +dur.toFixed(3), voice, engine: 'gemini', segments }
    fs.writeFileSync(path.join(out, 'timing.json'), JSON.stringify(data, null, 1))
    fs.writeFileSync(path.join(out, 'timing.js'), 'window.__TIMING = ' + JSON.stringify(data) + ';\n')
    fs.rmSync(v16, { force: true })
    segments.forEach(s => say(`  ${s.id.padEnd(10)} ${s.start.toFixed(2).padStart(7)} -> ${s.end.toFixed(2).padStart(7)}  (${s.words.length} words)`))
    console.log(`RESULT ok ${wavOut} ${dur.toFixed(2)}s, ${tokens.length} words, Whisper heard ${heard.length}`)
  } catch (e) {
    console.log('RESULT failed ' + (e && e.message || e))
  }
  app.quit()
})
