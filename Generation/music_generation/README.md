# MediNote/VITAL Music Generation Pipeline

This project generates short holiday and occasion-based background music prompts for MediNote/VITAL social media content. It does not use paid APIs or API keys. Audio generation is optional and uses the open-source Meta MusicGen implementation from `audiocraft` when it is installed.

## Pipeline

Holiday / Occasion + Product Theme
-> occasion preprocessing
-> mood and style mapping or ML prediction
-> prompt generation
-> optional open-source MusicGen audio generation
-> metadata storage
-> evaluation report

## Data

Input CSVs live in `data/`:

- `Global_Holidays_2025_2035_with_TN.csv`
- `music_style_mapping.csv`

The style mapping provides supervised labels for `target_mood` and `genre`, plus instruments, tempo, and example prompt style.

## Data Science Component

`src/mood_style_model.py` trains two lightweight classifiers:

- TF-IDF + Logistic Regression for `target_mood`
- TF-IDF + Logistic Regression for `genre`

The pipeline first tries a direct mapping match by holiday and product theme. If no exact style row exists, it falls back to the trained classifiers and borrows tempo/instrument defaults from the closest predicted genre.

## Audio Generation

`src/musicgen_generator.py` checks whether `audiocraft` and `torch` are importable. If they are available, the pipeline loads `facebook/musicgen-small`, generates a short waveform, and saves it to `outputs/audio/`.

If `audiocraft` is unavailable, the generator falls back to the Hugging Face `transformers` implementation using `AutoProcessor`, `MusicgenForConditionalGeneration`, `facebook/musicgen-small`, and `scipy.io.wavfile.write`.

If MusicGen is not installed, the pipeline still works in prompt-only mode and records that status in metadata.

## Install

```bash
cd music_generation
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional audio generation:

```bash
pip install torch torchaudio audiocraft
```

Optional Hugging Face fallback when `audiocraft` is not available:

```bash
pip install torch transformers scipy
```

## Run

```bash
python main.py --holiday "Ramadan" --product_theme "digestion" --duration 15
python main.py --holiday "New Year's Day" --product_theme "wellness" --duration 15
```

Force prompt-only mode:

```bash
python main.py --holiday "Ramadan" --product_theme "digestion" --duration 15 --prompt_only
```

Evaluate generated rows:

```bash
python src/evaluator.py
```

## Outputs

- `outputs/audio/*.wav` when MusicGen is installed
- `outputs/generated_music_metadata.csv`
- `outputs/evaluation_report.csv`

Evaluation includes:

- style coverage score
- prompt completeness score
- generated file existence check
- overall score
