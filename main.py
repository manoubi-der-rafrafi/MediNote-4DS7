from pathlib import Path

from src.agent_media.config import build_settings
from src.agent_media.orchestrator import AgentMediaApp


def main() -> None:
    project_root = Path(__file__).resolve().parent
    settings = build_settings(project_root)
    app = AgentMediaApp(settings)
    app.run()


if __name__ == "__main__":
    main()
