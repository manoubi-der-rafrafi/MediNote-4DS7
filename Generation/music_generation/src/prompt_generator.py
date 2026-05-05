from __future__ import annotations

try:
    from .mood_style_model import StylePrediction
    from .preprocess_holidays import OccasionContext
except ImportError:
    from mood_style_model import StylePrediction
    from preprocess_holidays import OccasionContext


def generate_music_prompt(context: OccasionContext, style: StylePrediction, duration: int) -> str:
    base = style.prompt_style.strip()
    if not base:
        base = (
            f"{style.target_mood} {style.genre} background music with {style.instruments} "
            f"for {context.holiday_name} {context.product_theme} social media content"
        )

    return (
        f"{base}. Short {duration}-second instrumental loop, {style.tempo} tempo, "
        f"clean mix, warm healthcare brand tone, subtle dynamics, no vocals, "
        f"suitable for MediNote/VITAL social media."
    )

