import numpy as np
from io import BytesIO
import wave

# Simple procedural audio generator that maps UI parameters to a synthesized audio clip.
# This is intentionally lightweight and dependency-free so it runs in most environments.

NOTE = 440.0  # not used directly; kept for reference

MOOD_MAP = {
    "Very Calm": {"amp": 0.3, "minor": True, "tempo_scale": 0.6},
    "Calm": {"amp": 0.5, "minor": True, "tempo_scale": 0.8},
    "Neutral": {"amp": 0.7, "minor": False, "tempo_scale": 1.0},
    "Energetic": {"amp": 0.9, "minor": False, "tempo_scale": 1.2},
    "Very Energetic": {"amp": 1.0, "minor": False, "tempo_scale": 1.4},
}

# Scales: lists of semitone offsets from root (C4=60)
MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11, 12]
MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10, 12]

INSTRUMENTS = ["Piano", "Violin", "Guitar", "Drums"]


def midi_to_freq(midi):
    return 440.0 * (2 ** ((midi - 69) / 12.0))


def sine_wave(freq, length, sr):
    t = np.linspace(0, length, int(sr * length), endpoint=False)
    return np.sin(2 * np.pi * freq * t)


def saw_wave(freq, length, sr):
    t = np.linspace(0, length, int(sr * length), endpoint=False)
    return 2.0 * (t * freq - np.floor(0.5 + t * freq))


def square_wave(freq, length, sr):
    return np.sign(sine_wave(freq, length, sr))


def envelope(samples, sr, attack=0.01, release=0.05):
    N = len(samples)
    env = np.ones(N)
    a = int(sr * attack)
    r = int(sr * release)
    if a > 0:
        env[:a] = np.linspace(0, 1.0, a)
    if r > 0:
        env[-r:] = np.linspace(1.0, 0.0, r)
    return samples * env


def mix_instrument(waveform, instrument):
    # simple timbre shaping per instrument
    if instrument == "Piano":
        # add a few harmonics
        return waveform * 0.8
    if instrument == "Violin":
        return waveform * 0.6
    if instrument == "Guitar":
        return waveform * 0.7
    if instrument == "Drums":
        return waveform * 0.9
    return waveform


def generate_music_bytes(genre, mood, tempo, instruments, duration, sr=22050):
    """
    Generate a WAV bytes object based on simple procedural rules.

    Inputs:
    - genre: list of selected genres (ignored for deep modelling; used for rhythmic/scale flavour)
    - mood: mood string
    - tempo: bpm integer
    - instruments: list of selected instruments
    - duration: seconds
    - sr: sample rate

    Returns bytes of a 16-bit PCM WAV file.
    """
    # deterministic seed so changes in params produce deterministic but varied outputs
    seed_str = "|".join(sorted(genre)) + f"|{mood}|{tempo}|" + "|".join(sorted(instruments)) + f"|{duration}"
    seed = abs(hash(seed_str)) % (2 ** 32)
    rng = np.random.default_rng(seed)

    mood_cfg = MOOD_MAP.get(mood, MOOD_MAP["Neutral"])
    amp = mood_cfg["amp"]
    minor = mood_cfg["minor"]
    tempo_scale = mood_cfg["tempo_scale"]

    effective_tempo = max(20, int(tempo * tempo_scale))
    beat_sec = 60.0 / effective_tempo

    # choose scale
    scale = MINOR_SCALE if minor else MAJOR_SCALE
    root_midi = 60  # C4

    total_samples = int(duration * sr)
    audio = np.zeros(total_samples, dtype=np.float32)

    # Build a melody/chord progression
    t = 0.0
    idx = 0
    while t < duration:
        # determine note length: quarter or eighth or dotted depending on genre/mood
        if "Electronic" in genre:
            note_len = beat_sec * (rng.choice([0.5, 1.0, 1.0, 0.25]))
        elif "Jazz" in genre:
            note_len = beat_sec * (rng.choice([0.5, 1.0, 1.5]))
        else:
            note_len = beat_sec * (rng.choice([1.0, 1.0, 0.5]))

        note_len = float(np.clip(note_len, 0.05, duration - t))
        # pick a degree
        degree = rng.choice(range(len(scale)))
        octave_shift = rng.choice([0, 12, 12, 24])
        midi = root_midi + scale[degree] + octave_shift
        freq = midi_to_freq(midi)

        # create waveform for this note
        samples = int(note_len * sr)
        if samples <= 0:
            break

        # instrument mixing: sum of partials depending on instruments selected
        note_wave = np.zeros(samples, dtype=np.float32)
        for inst in instruments:
            if inst == "Piano":
                w = sine_wave(freq, note_len, sr)
                w = w + 0.5 * sine_wave(freq * 2, note_len, sr)
                w = w * np.exp(-3.0 * np.linspace(0, 1, samples))  # percussive
            elif inst == "Violin":
                w = saw_wave(freq, note_len, sr) * 0.5
                w = w * np.linspace(0.2, 1.0, samples)  # slow attack
            elif inst == "Guitar":
                w = sine_wave(freq, note_len, sr)
                w = w * np.exp(-5.0 * np.linspace(0, 1, samples))  # pluck
            elif inst == "Drums":
                # add a drum on downbeats
                if (abs((t / beat_sec) - round(t / beat_sec)) < 0.1) or rng.random() < 0.1:
                    noise = rng.normal(0, 1, samples)
                    w = noise * np.exp(-15.0 * np.linspace(0, 1, samples))
                else:
                    w = np.zeros(samples)
            else:
                w = sine_wave(freq, note_len, sr)

            # apply a small random pitch modulation for realism
            detune = rng.uniform(-0.5, 0.5)
            w = np.interp(np.linspace(0, len(w), len(w)) + detune, np.arange(len(w)), w, left=0, right=0)
            note_wave += mix_instrument(w, inst)

        # envelope
        note_wave = envelope(note_wave, sr, attack=0.01, release=0.05)

        # place into audio buffer
        start = int(t * sr)
        end = start + samples
        if end > total_samples:
            end = total_samples
            note_wave = note_wave[: end - start]
        audio[start:end] += note_wave * amp * (0.6 + 0.4 * rng.random())

        t += note_len
        idx += 1

    # normalize
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.95

    # convert to 16-bit PCM
    ints = np.int16(audio * 32767)

    # write to WAV bytes
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(ints.tobytes())

    buffer.seek(0)
    return buffer.getvalue()
