import re
import time
from io import BytesIO
import streamlit as st
from audio_gen import generate_music_bytes

GENRES = ["Classical", "Jazz", "Rock", "Electronic", "Folk", "Pop"]
MOODS = ["Very Calm", "Calm", "Neutral", "Energetic", "Very Energetic"]
INSTRUMENTS = ["Piano", "Violin", "Guitar", "Drums"]


def parse_music_request(text):
    """Extract music parameters from a natural-language text request."""
    t = text.lower().strip()
    genres = [g for g in GENRES if g.lower() in t]
    instruments = [i for i in INSTRUMENTS if i.lower() in t]

    # Pick the most specific mood first.
    mood = "Neutral"
    for m in ["Very Energetic", "Very Calm", "Energetic", "Calm", "Neutral"]:
        if m.lower() in t:
            mood = m
            break
    # Common synonyms
    if mood == "Neutral":
        if any(x in t for x in ["relaxed", "peaceful", "soft", "soothing"]):
            mood = "Calm"
        elif any(x in t for x in ["exciting", "upbeat", "fast", "lively"]):
            mood = "Energetic"

    tempo_match = re.search(r"(\d{2,3})\s*(?:bpm|beats?\s*(?:per\s*minute)?)", t)
    tempo = int(tempo_match.group(1)) if tempo_match else 60
    tempo = max(10, min(120, tempo))

    duration = 60
    duration_match = re.search(r"(\d+(?:\.\d+)?)\s*(seconds?|secs?|minutes?|mins?)", t)
    if duration_match:
        value = float(duration_match.group(1))
        unit = duration_match.group(2)
        duration = int(value * 60) if unit.startswith("min") else int(value)
    duration = max(30, min(300, duration))

    if not genres:
        genres = ["Classical"]
    if not instruments:
        instruments = ["Piano"]

    return {
        "genre": genres,
        "mood": mood,
        "instruments": instruments,
        "tempo": tempo,
        "duration": duration,
    }


def get_rotating_disc_html(is_playing):
    animation = "animation: rotate 3s linear infinite;" if is_playing else ""
    status = "♫ Now Playing" if is_playing else "● Paused"
    return f"""
    <div style='width:300px;height:300px;margin:20px auto;position:relative'>
      <style>
      @keyframes rotate {{ from {{transform:rotate(0deg)}} to {{transform:rotate(360deg)}} }}
      .disc {{ width:300px;height:300px;border-radius:50%;background:#171717;box-shadow:0 0 18px #000;position:relative;{animation} }}
      .disc:before {{ content:'';position:absolute;inset:22px;border-radius:50%;border:1px solid #444;box-shadow:inset 0 0 0 20px #1d1d1d,inset 0 0 0 40px #181818,inset 0 0 0 60px #202020; }}
      .label {{ position:absolute;left:105px;top:105px;width:90px;height:90px;border-radius:50%;background:#596273;border:2px solid #333; }}
      .hole {{ position:absolute;left:145px;top:145px;width:10px;height:10px;border-radius:50%;background:#111; }}
      </style>
      <div style='text-align:center;font-weight:bold;font-family:Arial;color:#4CAF50;margin-bottom:8px'>{status}</div>
      <div class='disc'><div class='label'></div><div class='hole'></div></div>
    </div>
    """


def init_state():
    st.session_state.setdefault("generated_music", False)
    st.session_state.setdefault("is_playing", False)
    st.session_state.setdefault("generated_audio_bytes", None)
    st.session_state.setdefault("generated_filename", None)
    st.session_state.setdefault("last_params", None)


def main():
    st.set_page_config(page_title="AI Music Generator - Text Input", page_icon="🎵", layout="wide")
    init_state()

    st.title("🎵 AI Music Generator")
    st.markdown("Describe the music you want in **one text prompt**. The app extracts the genre, mood, instruments, tempo and duration automatically.")

    left, right = st.columns([2, 1])

    with left:
        st.header("✍️ Text Input")
        prompt = st.text_area(
            "Describe your music",
            height=140,
            placeholder="Example: Create calm classical piano and violin music for 60 seconds at 70 BPM.",
        )

        st.caption("Supported genres: Classical, Jazz, Rock, Electronic, Folk, Pop | Instruments: Piano, Violin, Guitar, Drums | Tempo: 10–120 BPM | Duration: 30–300 seconds")

        if st.button("🔍 Understand Request", use_container_width=True):
            if not prompt.strip():
                st.warning("Please enter a music request first.")
            else:
                params = parse_music_request(prompt)
                st.session_state.last_params = params
                st.success("Music requirements extracted successfully.")

        if st.session_state.last_params:
            p = st.session_state.last_params
            st.subheader("Detected Parameters")
            st.write(f"**Genre:** {', '.join(p['genre'])}")
            st.write(f"**Mood:** {p['mood']}")
            st.write(f"**Instruments:** {', '.join(p['instruments'])}")
            st.write(f"**Tempo:** {p['tempo']} BPM")
            st.write(f"**Duration:** {p['duration']} seconds")

        if st.button("🎼 Generate Music", type="primary", use_container_width=True):
            if not prompt.strip():
                st.warning("Please enter a music request first.")
            else:
                params = parse_music_request(prompt)
                st.session_state.last_params = params
                with st.spinner("Generating your music..."):
                    progress = st.progress(0)
                    for i in range(0, 100, 20):
                        time.sleep(0.08)
                        progress.progress(i + 20)
                    try:
                        audio_bytes = generate_music_bytes(
                            params["genre"], params["mood"], params["tempo"], params["instruments"], params["duration"]
                        )
                        filename = f"generated_{int(time.time())}.wav"
                        with open(filename, "wb") as f:
                            f.write(audio_bytes)
                        st.session_state.generated_audio_bytes = audio_bytes
                        st.session_state.generated_filename = filename
                        st.session_state.generated_music = True
                        st.session_state.is_playing = True
                        st.success("Music generation complete!")
                    except Exception as e:
                        st.error(f"Audio generation failed: {e}")

        st.subheader("💡 Example Text Prompts")
        examples = [
            "Create calm classical piano music for 60 seconds at 70 BPM.",
            "Generate energetic electronic music with piano and drums for 1 minute at 110 BPM.",
            "Make relaxing jazz guitar music for 45 seconds at 80 BPM.",
            "Create very energetic rock music with drums and guitar for 30 seconds at 120 BPM.",
        ]
        for ex in examples:
            st.code(ex)

    with right:
        st.header("🎧 Player")
        st.components.v1.html(get_rotating_disc_html(st.session_state.is_playing), height=350)
        if st.session_state.generated_audio_bytes:
            st.audio(BytesIO(st.session_state.generated_audio_bytes), format="audio/wav")
            st.download_button(
                "⬇️ Download WAV",
                data=st.session_state.generated_audio_bytes,
                file_name=st.session_state.generated_filename or "generated_music.wav",
                mime="audio/wav",
                use_container_width=True,
            )
            if st.button("⏯️ Pause / Resume", use_container_width=True):
                st.session_state.is_playing = not st.session_state.is_playing
                st.rerun()


if __name__ == "__main__":
    main()
