# AI Music Generator - Text Input

A Streamlit music generator that accepts a natural-language text prompt and automatically extracts:

- Genre
- Mood
- Instruments
- Tempo (BPM)
- Duration

It then generates a WAV audio file using the project's existing procedural audio generator.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Example

```text
Create calm classical piano and violin music for 60 seconds at 70 BPM.
```

The application detects the requested parameters and generates the music.

## Supported values

Genres: Classical, Jazz, Rock, Electronic, Folk, Pop

Moods: Very Calm, Calm, Neutral, Energetic, Very Energetic

Instruments: Piano, Violin, Guitar, Drums

Tempo: 10-120 BPM

Duration: 30-300 seconds
