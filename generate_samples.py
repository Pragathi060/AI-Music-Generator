from audio_gen import generate_music_bytes
from io import BytesIO
import wave, math

samples = [
    {"name": "calm_classical_piano_5s", "genre": ["Classical"], "mood": "Very Calm", "tempo": 50, "instruments": ["Piano"], "duration": 5},
    {"name": "energetic_electronic_piano_drums_10s", "genre": ["Electronic"], "mood": "Very Energetic", "tempo": 120, "instruments": ["Piano","Drums"], "duration": 10},
    {"name": "jazz_neutral_guitar_7s", "genre": ["Jazz"], "mood": "Neutral", "tempo": 80, "instruments": ["Guitar"], "duration": 7}
]

reports = []
for s in samples:
    print(f"Generating: {s['name']}")
    b = generate_music_bytes(s['genre'], s['mood'], s['tempo'], s['instruments'], s['duration'])
    filename = s['name'] + '.wav'
    with open(filename, 'wb') as f:
        f.write(b)
    buf = BytesIO(b)
    wf = wave.open(buf, 'rb')
    nch = wf.getnchannels(); sw = wf.getsampwidth(); fr = wf.getframerate(); nframes = wf.getnframes(); dur = nframes / fr
    data = wf.readframes(nframes)
    # compute peak and rms
    import struct
    fmt = '<' + 'h' * (len(data)//2)
    ints = struct.unpack(fmt, data[:(len(data)//2)*2])
    peak = max(abs(x) for x in ints)
    rms = math.sqrt(sum(x*x for x in ints)/len(ints))
    hdr_hex = b[:64].hex()
    wf.close()
    report = {
        'file': filename,
        'bytes': len(b),
        'nchannels': nch,
        'sampwidth': sw,
        'framerate': fr,
        'nframes': nframes,
        'duration': dur,
        'peak': peak,
        'rms': rms,
        'header_hex': hdr_hex
    }
    reports.append(report)
    print(report)

print('\nAll generated files saved in the project folder.')

# print a short summary
for r in reports:
    print(f"{r['file']}: {r['bytes']} bytes, duration {r['duration']}s, sr={r['framerate']}, peak={r['peak']}, rms={r['rms']}")
