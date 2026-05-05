from __future__ import annotations

import argparse

from src.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate MediNote/VITAL holiday music prompts and optional MusicGen audio.")
    parser.add_argument("--holiday", required=True, help="Holiday or occasion name, for example 'Ramadan'.")
    parser.add_argument("--product_theme", required=True, help="Product theme, for example 'digestion' or 'wellness'.")
    parser.add_argument("--duration", type=int, default=15, help="Audio duration in seconds.")
    parser.add_argument("--country", default=None, help="Optional country code filter, for example TN.")
    parser.add_argument("--year", type=int, default=None, help="Optional year filter, for example 2026.")
    parser.add_argument("--prompt_only", action="store_true", help="Skip audio generation even when MusicGen is installed.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_pipeline(
        holiday=args.holiday,
        product_theme=args.product_theme,
        duration=args.duration,
        country=args.country,
        year=args.year,
        prompt_only=args.prompt_only,
    )
    print("\nGenerated music prompt:\n")
    print(result["prompt"])
    print(f"\nStyle source: {result['style_source']}")
    print(f"Generation status: {result['generation_status']}")
    if result["audio_path"]:
        print(f"Audio saved to: {result['audio_path']}")
    print("Metadata saved to: outputs/generated_music_metadata.csv")
    print("Evaluation saved to: outputs/evaluation_report.csv")


if __name__ == "__main__":
    main()

