from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any

from .calendar_utils import build_fetes_mapping, prochaine_fete, saisons_actives_ce_mois
from .config import Settings
from .content_generator import ContentGenerator
from .data_loader import DataLoader
from .export_service import ExportService
from .image_generator import ImageGenerator
from .post_store import PostStore
from .profile_builder import construire_profils
from .retrieval import RetrievalEngine
from .scoring import ScoringEngine


@dataclass(slots=True)
class PipelineArtifacts:
    fetes_mapping: dict[str, dict[str, Any]]
    profils_count: int
    next_holiday: dict[str, Any] | None
    holiday_campaign: dict[str, Any] | None
    seasonal_campaigns: list[dict[str, Any]]
    retrieval_backend: str
    exports: dict[str, bool]


class AgentMediaApp:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.loader = DataLoader(settings)
        self.post_store = PostStore(settings.outputs.posts_dataset)
        self.image_generator = ImageGenerator(
            project_root=settings.project_root,
            output_dir=settings.output_dir / "campaign_images",
            logo_path=settings.project_root / "logo.png",
            hf_api_key=settings.hf_api_key,
            gemini_api_key=settings.gemini_api_key,
            mistral_api_key=settings.mistral_api_key,
        )
        self.export_service = ExportService(settings.outputs)

    def run(self) -> None:
        print("=== Agent Media ===")
        artifacts = self.run_pipeline()
        self._print_summary(artifacts)

    def run_pipeline(self) -> PipelineArtifacts:
        loaded = self.loader.load_all()
        fetes_mapping = build_fetes_mapping(loaded.tunisian_holidays)
        df_profils = construire_profils(loaded)
        retrieval_engine = RetrievalEngine.build(df_profils)
        scoring = ScoringEngine(loaded.encoded, df_profils, fetes_mapping)
        content = ContentGenerator(
            df_profils=df_profils,
            df_tn=loaded.tunisian_holidays,
            fetes_mapping=fetes_mapping,
            mistral_api_key=self.settings.mistral_api_key,
        )

        holiday_campaign = self._build_dual_holiday_campaign(loaded.tunisian_holidays, scoring, content)
        seasonal_campaigns = self._build_active_season_campaigns(scoring, content)
        exports = self.export_service.export_all(df_profils, fetes_mapping, retrieval_engine)

        snapshot = {
            "generated_at": str(date.today()),
            "next_holiday": holiday_campaign,
            "seasonal_campaigns": seasonal_campaigns,
            "retrieval_backend": retrieval_engine.backend,
        }
        with self.settings.outputs.snapshot_json.open("w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, ensure_ascii=False, indent=2)

        next_row = prochaine_fete(loaded.tunisian_holidays)
        return PipelineArtifacts(
            fetes_mapping=fetes_mapping,
            profils_count=len(df_profils),
            next_holiday=None if next_row is None else {"date": str(next_row["Date"])[:10], "fete": str(next_row["Holiday_Name"])},
            holiday_campaign=holiday_campaign,
            seasonal_campaigns=seasonal_campaigns,
            retrieval_backend=retrieval_engine.backend,
            exports=exports,
        )

    def _build_dual_holiday_campaign(self, df_tn, scoring: ScoringEngine, content: ContentGenerator) -> dict[str, Any] | None:
        next_row = prochaine_fete(df_tn)
        if next_row is None:
            return None

        fete_nom = str(next_row["Holiday_Name"])
        fete_info = scoring.fetes_mapping.get(fete_nom, {})
        top = scoring.top_produits_pour_fete(fete_nom, top_k=1)
        top_product = None if top.empty else str(top.iloc[0]["produit"])
        # Dual images (always 2)
        dual_images = self.image_generator.generate_dual_holiday_images(
            fete_nom=fete_nom,
            top_produit=top_product,
            fete_info=fete_info,
            df_profils=scoring.df_profils,
        )
        instit_image_data = dual_images["fetes_instit"]
        product_image_data = dual_images["saison_produit"]
        instit_fb = content.generate_post(None, fete_nom, "Facebook")
        instit_ig = content.generate_post(None, fete_nom, "Instagram")
        
        # Image 2: Saisonnière/Produit (top product)
        top_product = None if top.empty else str(top.iloc[0]["produit"])
        # Product image data already from dual_images
        product_fb = content.generate_post(top_product, fete_nom, "Facebook")
        product_ig = content.generate_post(top_product, fete_nom, "Instagram")
        
        # Store both
        instit_ids = [
            self.post_store.add_post("Corporate", "Facebook", instit_fb, fete=fete_nom, campagne_type="fete_instit"),
            self.post_store.add_post("Corporate", "Instagram", instit_ig, fete=fete_nom, campagne_type="fete_instit"),
        ]
        product_ids = []
        if top_product:
            product_ids = [
                self.post_store.add_post(top_product, "Facebook", product_fb, fete=fete_nom, campagne_type="fete_produit"),
                self.post_store.add_post(top_product, "Instagram", product_ig, fete=fete_nom, campagne_type="fete_produit"),
            ]
        
        return {
            "fete": fete_nom,
            "date": str(next_row["Date"])[:10],
            "top_produit": top_product,
            "score": None if top.empty else float(top.iloc[0]["score"]),
            "images": [
                {"type": "fetes_instit", "data": instit_image_data, "posts": {"facebook": instit_fb, "instagram": instit_ig}, "post_ids": instit_ids},
                {"type": "saison_produit", "data": product_image_data, "posts": {"facebook": product_fb, "instagram": product_ig}, "post_ids": product_ids},
            ]
        }

    def _build_active_season_campaigns(self, scoring: ScoringEngine, content: ContentGenerator) -> list[dict[str, Any]]:
        campagnes: list[dict[str, Any]] = []
        for nom_saison, info in saisons_actives_ce_mois():
            top = scoring.top_produits_pour_saison(nom_saison, top_k=1)
            if top.empty:
                continue
            produit_nom = str(top.iloc[0]["produit"])
            facebook = content.generate_season_post(produit_nom, nom_saison, "Facebook")
            instagram = content.generate_season_post(produit_nom, nom_saison, "Instagram")
            image_data = self.image_generator.create_season_campaign_image(
                produit_nom=produit_nom,
                nom_saison=nom_saison,
                saison_info=info,
                df_profils=scoring.df_profils,
            )
            campagnes.append(
                {
                    "saison": nom_saison,
                    "produit": produit_nom,
                    "score": float(top.iloc[0]["score"]),
                    "facebook": facebook,
                    "instagram": instagram,
                    "image_locale": image_data.get("image_locale"),
                    "url_image_produit": image_data.get("url_image_produit"),
                }
            )
        return campagnes

    def _print_summary(self, artifacts: PipelineArtifacts) -> None:
        print(f"Profils produits: {artifacts.profils_count}")
        print(f"Backend RAG: {artifacts.retrieval_backend}")
        if artifacts.next_holiday:
            print(f"Prochaine fete: {artifacts.next_holiday['fete']} le {artifacts.next_holiday['date']}")
        if artifacts.holiday_campaign:
            print(f"Campagne fete: {artifacts.holiday_campaign['fete']} -> Dual images generated!")
            print(f"Images: {len(artifacts.holiday_campaign.get('images', []))} (instit + produit)")
        if artifacts.seasonal_campaigns:
            print("Campagnes saisonnieres actives:")
            for campagne in artifacts.seasonal_campaigns:
                print(f"- {campagne['saison']} -> {campagne['produit']} ({campagne['score']}/10)")
        else:
            print("Aucune campagne saisonniere active ce mois.")
        print("Exports:")
        for key, value in artifacts.exports.items():
            print(f"- {key}: {'ok' if value else 'skip'}")


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value).strip("_").lower()
