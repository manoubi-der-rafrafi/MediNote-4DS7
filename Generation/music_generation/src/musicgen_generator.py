from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


ROOT_DIR = Path(__file__).resolve().parents[1]
AUDIO_DIR = ROOT_DIR / "outputs" / "audio"
DEFAULT_MODEL_NAME = "facebook/musicgen-small"


def is_audiocraft_available() -> bool:
    try:
        import audiocraft  # noqa: F401
        import torch  # noqa: F401
    except Exception:
        return False
    return True


def is_transformers_musicgen_available() -> bool:
    try:
        import scipy  # noqa: F401
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except Exception:
        return False
    return True


def is_musicgen_available() -> bool:
    return is_audiocraft_available() or is_transformers_musicgen_available()


def slugify(value: str, max_length: int = 80) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")
    return slug[:max_length] or "musicgen_output"


def _output_path(holiday_name: str, product_theme: str, duration: int, output_dir: Path) -> Path:
    stem = slugify(f"{holiday_name}_{product_theme}_{duration}s")
    return output_dir / f"{stem}.wav"


def _generate_with_audiocraft(
    prompt: str,
    holiday_name: str,
    product_theme: str,
    duration: int,
    output_dir: Path,
    model_name: str,
) -> Optional[Path]:
    from audiocraft.data.audio import audio_write
    from audiocraft.models import MusicGen

    model = MusicGen.get_pretrained(model_name)
    model.set_generation_params(duration=duration)
    wav = model.generate([prompt])[0].cpu()

    output_path = _output_path(holiday_name, product_theme, duration, output_dir)
    output_stem = output_path.with_suffix("")
    audio_write(str(output_stem), wav, model.sample_rate, strategy="loudness", loudness_compressor=True)
    return output_path


def _generate_with_transformers(
    prompt: str,
    holiday_name: str,
    product_theme: str,
    duration: int,
    output_dir: Path,
    model_name: str,
) -> Optional[Path]:
    import torch
    from scipy.io.wavfile import write
    from transformers import AutoProcessor, MusicgenForConditionalGeneration

    processor = AutoProcessor.from_pretrained(model_name)
    model = MusicgenForConditionalGeneration.from_pretrained(model_name)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    inputs = processor(text=[prompt], padding=True, return_tensors="pt").to(device)
    frame_rate = getattr(model.config.audio_encoder, "frame_rate", 50)
    max_new_tokens = max(1, int(duration * frame_rate))

    with torch.no_grad():
        audio_values = model.generate(**inputs, max_new_tokens=max_new_tokens)

    sampling_rate = model.config.audio_encoder.sampling_rate
    audio = audio_values[0].detach().cpu()

    if audio.ndim == 2:
        audio = audio.transpose(0, 1)
    audio_array = audio.numpy()

    output_path = _output_path(holiday_name, product_theme, duration, output_dir)
    write(output_path, rate=sampling_rate, data=audio_array)
    return output_path


def generate_audio_with_musicgen(
    prompt: str,
    holiday_name: str,
    product_theme: str,
    duration: int,
    output_dir: Path = AUDIO_DIR,
    model_name: str = DEFAULT_MODEL_NAME,
) -> Optional[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    if is_audiocraft_available():
        return _generate_with_audiocraft(
            prompt=prompt,
            holiday_name=holiday_name,
            product_theme=product_theme,
            duration=duration,
            output_dir=output_dir,
            model_name=model_name,
        )

    if is_transformers_musicgen_available():
        return _generate_with_transformers(
            prompt=prompt,
            holiday_name=holiday_name,
            product_theme=product_theme,
            duration=duration,
            output_dir=output_dir,
            model_name=model_name,
        )

    return None
