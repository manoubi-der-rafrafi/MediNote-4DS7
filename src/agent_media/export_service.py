from __future__ import annotations

import json
from typing import Any

import pandas as pd

from .profile_builder import profils_to_csv_frame, profils_to_json_ready
from .retrieval import RetrievalEngine


class ExportService:
    def __init__(self, outputs) -> None:
        self.outputs = outputs

    def export_all(
        self,
        df_profils: pd.DataFrame,
        fetes_mapping: dict[str, dict[str, Any]],
        retrieval_engine: RetrievalEngine,
    ) -> dict[str, bool]:
        results: dict[str, bool] = {}
        profils_to_csv_frame(df_profils).to_csv(self.outputs.profils_csv, index=False, encoding="utf-8-sig")
        results["profils_csv"] = True

        with self.outputs.profils_json.open("w", encoding="utf-8") as handle:
            json.dump(profils_to_json_ready(df_profils), handle, ensure_ascii=False, indent=2)
        results["profils_json"] = True

        with self.outputs.fetes_mapping_json.open("w", encoding="utf-8") as handle:
            json.dump(fetes_mapping, handle, ensure_ascii=False, indent=2)
        results["fetes_mapping_json"] = True

        results["rag_index"] = retrieval_engine.save_index(self.outputs.rag_index)
        return results
