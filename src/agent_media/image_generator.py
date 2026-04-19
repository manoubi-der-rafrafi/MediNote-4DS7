from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont


class ImageGenerator:
    def __init__(
        self,
        project_root: Path,
        output_dir: Path,
        logo_path: Path | None = None,
        hf_api_key: str | None = None,
        gemini_api_key: str | None = None,
        mistral_api_key: str | None = None,
    ) -> None:
        self.project_root = project_root
        self.output_dir = output_dir
        self.logo_path = logo_path if logo_path and logo_path.exists() else None
        self.hf_api_key = hf_api_key
        self.gemini_api_key = gemini_api_key
        self.mistral_api_key = mistral_api_key
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_dual_holiday_images(
        self,
        fete_nom: str,
        top_produit: str | None,
        fete_info: dict,
        df_profils: pd.DataFrame,
    ) -> dict[str, dict]:
        safe_fete = self._safe_name(fete_nom)
        
        # Image 1: Fêtes/Institutionnelle (corporate, no product)
        instit_data = self.create_holiday_campaign_image(
            produit_nom=None,  # Force institutional
            fete_nom=fete_nom,
            fete_info=fete_info,
            df_profils=df_profils,
        )
        
        # Image 2: Saisonnière/Produit (top product + seasonal)
        product_data = self.create_holiday_campaign_image(
            produit_nom=top_produit,
            fete_nom=fete_nom,
            fete_info=fete_info,
            df_profils=df_profils,
        )
        
        return {
            "fetes_instit": instit_data,
            "saison_produit": product_data,
        }
    
    def create_holiday_campaign_image(
        self,
        produit_nom: str | None,
        fete_nom: str,
        fete_info: dict,
        df_profils: pd.DataFrame,
    ) -> dict[str, object]:
        safe_fete = self._safe_name(fete_nom)
        categorie = fete_info.get("categorie", fete_info.get("type", "publique"))
        necessite_vital = bool(fete_info.get("necessite_produit_vital", False))
        profil = df_profils[df_profils["produit"] == produit_nom] if produit_nom else pd.DataFrame()

        if produit_nom:
            url_image_produit = self.rechercher_image_produit_web(produit_nom, fete_nom)
        else:
            url_image_produit = None

        if not url_image_produit and produit_nom and not profil.empty:
            fallback_url = profil.iloc[0].get("url_image")
            if pd.notna(fallback_url) and str(fallback_url).startswith("http"):
                url_image_produit = str(fallback_url)

        use_product_image = False
        if categorie == "institutionnel" or produit_nom is None:
            use_product_image = False
        elif necessite_vital and len(profil) > 0 and pd.notna(url_image_produit):
            use_product_image = True

        visual_style = self.get_fete_visual_prompt(fete_nom, fete_info)
        if use_product_image and produit_nom:
            prompt_image = f"""
Professional luxury pharmaceutical product photography, square Instagram format 1:1,
clean minimalist studio style, pure white background with very subtle soft gradient,
seasonal Tunisian celebration mood, subtle festive elements,
{produit_nom} bottle/box perfectly centered, sharp focus on packaging and label,
elegant product placement with realistic soft shadow underneath,
premium commercial product shot, soft diffused studio lighting,
blue white gold color palette, high-end aesthetic,
Vital Laboratories logo visible in bottom right corner, small and elegant,
NO people, NO lifestyle scene, NO text on image, NO watermark, NO badge, NO "NOUVEAU"
""".strip()
            save_path = self.output_dir / f"image_{self._safe_name(produit_nom)[:25]}_{safe_fete}_saison.jpg"
        else:
            prompt_image = f"""
Elegant corporate brand poster for Tunisian holiday, abstract geometric composition,
{visual_style}, Tunisian national colors subtle festive mood,
premium soft gradient background, cinematic lighting,
luxury pharmaceutical aesthetic, 8k ultra detailed,
NO TEXT, NO WORDS, NO LETTERS, NO WATERMARK
""".strip()
            save_path = self.output_dir / f"image_fetes_{safe_fete}.jpg"

        img = self.generer_image_multi(
            prompt=prompt_image,
            save_path=save_path,
            url_image_produit=url_image_produit,
            produit_nom=produit_nom,
            df_profils=df_profils,
        )
        if img and save_path.exists():
            self.add_fete_text_to_image(save_path, fete_nom)

        return {
            "image_locale": str(save_path) if save_path.exists() else None,
            "url_image_produit": url_image_produit,
            "use_product_image": use_product_image,
            "categorie": categorie,
        }

    def create_season_campaign_image(
        self,
        produit_nom: str,
        nom_saison: str,
        saison_info: dict,
        df_profils: pd.DataFrame,
    ) -> dict[str, object]:
        url_image_produit = self.rechercher_image_produit_web(produit_nom, nom_saison)
        save_path = self.output_dir / f"image_saison_{self._safe_name(nom_saison)[:30]}.jpg"
        prompt_image = self.get_saison_visual_prompt(nom_saison, saison_info)
        img = self.generer_image_multi(
            prompt=prompt_image,
            save_path=save_path,
            url_image_produit=url_image_produit,
            produit_nom=produit_nom,
            df_profils=df_profils,
        )
        if img and save_path.exists():
            self.add_season_text_to_image(save_path, nom_saison)
        return {
            "image_locale": str(save_path) if save_path.exists() else None,
            "url_image_produit": url_image_produit,
        }

    def rechercher_image_produit_web(self, produit_nom: str, fete_nom: str | None = None) -> str | None:
        del fete_nom
        try:
            slug = produit_nom.lower().strip()
            slug = re.sub(r"[^a-z0-9\s-]", "", slug)
            slug = re.sub(r"[\s-]+", "-", slug)
            product_url = f"https://vital.com.tn/products/{slug}/"
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
                )
            }
            response = requests.get(product_url, headers=headers, timeout=12)
            if response.status_code != 200:
                return None
            html = response.text
            patterns = [
                r'<img[^>]+class="[^"]*(?:wp-post-image|attachment-product|product-image)[^"]*"[^>]+src="([^"]+)"',
                r'<img[^>]+src="([^"]*wp-content/uploads[^"]+\.(?:jpg|jpeg|png|webp))"',
                rf'<img[^>]+alt="[^"]*{re.escape(produit_nom)}[^"]*"[^>]+src="([^"]+)"',
            ]
            for pattern in patterns:
                match = re.search(pattern, html, re.I)
                if match:
                    image_url = match.group(1)
                    if image_url.startswith("/"):
                        image_url = "https://vital.com.tn" + image_url
                    return image_url
            return None
        except Exception:
            return None

    def add_fete_text_to_image(self, image_path: Path, fete_nom: str) -> bool:
        if not image_path.exists():
            return False
        try:
            img = Image.open(image_path).convert("RGB")
            draw = ImageDraw.Draw(img)
            fete_lower = fete_nom.lower()
            if "eid al-adha" in fete_lower:
                text = "Eid Al-Adha Mubarak"
            elif "eid al-fitr" in fete_lower:
                text = "Eid Mubarak"
            elif "ramadan" in fete_lower:
                text = "Ramadan Mubarak"
            elif "mawlid" in fete_lower:
                text = "Mawlid Al-Nabi"
            elif "martyrs" in fete_lower or "9 avril" in fete_lower:
                text = "Journee des Martyrs"
            elif "independence" in fete_lower or "20 mars" in fete_lower:
                text = "Fete de l'Independance"
            else:
                text = fete_nom.upper()

            font = self._load_font(85)
            w, h = img.size
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (w - text_width) // 2
            y = h - 140
            draw.text((x + 4, y + 4), text, font=font, fill="#000000")
            draw.text((x + 3, y + 3), text, font=font, fill="#000000")
            draw.text((x - 2, y - 2), text, font=font, fill="#FFD700")
            draw.text((x + 2, y - 2), text, font=font, fill="#FFD700")
            draw.text((x - 2, y + 2), text, font=font, fill="#FFD700")
            draw.text((x + 2, y + 2), text, font=font, fill="#FFD700")
            draw.text((x, y), text, font=font, fill="#FFFFFF")
            img.save(image_path)
            return True
        except Exception:
            return False

    def add_season_text_to_image(self, image_path: Path, nom_saison: str) -> bool:
        if not image_path.exists():
            return False
        try:
            img = Image.open(image_path).convert("RGB")
            draw = ImageDraw.Draw(img)
            text = nom_saison.upper()
            font_size = 70
            font = self._load_font(font_size)
            w, h = img.size
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            while tw > w - 80 and font_size > 30:
                font_size -= 5
                font = self._load_font(font_size)
                bbox = draw.textbbox((0, 0), text, font=font)
                tw = bbox[2] - bbox[0]
            x, y = (w - tw) // 2, h - 120
            draw.text((x + 3, y + 3), text, font=font, fill="#000000")
            draw.text((x - 2, y - 2), text, font=font, fill="#FFD700")
            draw.text((x + 2, y + 2), text, font=font, fill="#FFD700")
            draw.text((x, y), text, font=font, fill="#FFFFFF")
            logo_path = self._resolve_logo_path()
            if logo_path:
                logo = Image.open(logo_path).convert("RGBA")
                logo = logo.resize((160, 55), Image.LANCZOS)
                img.paste(logo, (w - logo.width - 30, h - logo.height - 30), logo)
            img.save(image_path)
            return True
        except Exception:
            return False

    def get_fete_visual_prompt(self, fete_nom: str, fete_info: dict) -> str:
        nom = fete_nom.lower()
        if "eid al-adha" in nom or "aid" in nom:
            return "Eid al-Adha celebration Tunisia, sheep, family feast, warm golden festive atmosphere, subtle Tunisian decoration"
        if "ramadan" in nom:
            return "Ramadan atmosphere Tunisia, lanterns, crescent moon, iftar, warm night lighting"
        if "martyrs" in nom or "9 avril" in nom:
            return "solemn patriotic remembrance, Tunisian flag colors, red white green, dignified atmosphere"
        if "independence" in nom or "20 mars" in nom:
            return "Tunisian Independence Day, national pride, flags waving, festive patriotic mood"
        return fete_info.get("style_visuel", "festive Tunisian atmosphere")

    def get_saison_visual_prompt(self, nom_saison: str, saison_info: dict) -> str:
        nom = nom_saison.lower()
        base_style = """
ultra professional Instagram pharmaceutical advertisement,
high-end medical marketing visual,
clean studio composition, premium branding,
soft cinematic lighting,
depth of field, luxury healthcare aesthetic,
NO TEXT, NO WORDS, NO WATERMARK, NO LOGOS
""".strip()
        if "bac" in nom or "exam" in nom or "examen" in nom:
            return base_style + """
 STUDY / EXAM PERIOD THEME:
 focused atmosphere, students studying concept (NO faces),
 stress relief, mental clarity, energy support,
 soft blue tones, calm academic environment feel
""".strip()
        if "hiver" in nom or "winter" in nom:
            return base_style + """
 WINTER HEALTH THEME:
 cold season protection, immunity, cozy warm lighting,
 subtle frost background, soft blue-white palette,
 health protection concept
""".strip()
        if "été" in nom or "ete" in nom or "summer" in nom:
            return base_style + """
 SUMMER WELLNESS THEME:
 heat protection, hydration, energy boost,
 bright clean sunlight, fresh vibrant tones,
 refreshing medical wellness feeling
""".strip()
        if "printemps" in nom or "spring" in nom:
            return base_style + """
 SPRING HEALTH THEME:
 renewal, vitality, freshness,
 soft green pastel tones, natural light,
 rejuvenation and wellness atmosphere
""".strip()
        return base_style + f" GENERAL SEASONAL HEALTH THEME: {saison_info.get('style_visuel', 'premium pharmaceutical aesthetic')}, wellness, vitality, medical professionalism"

    def generer_image_multi(
        self,
        prompt: str,
        save_path: Path,
        url_image_produit: str | None = None,
        produit_nom: str | None = None,
        df_profils: pd.DataFrame | None = None,
    ) -> Image.Image | None:
        width, height = 1024, 1024
        img_produit = self._charger_image_produit(url_image_produit, produit_nom, df_profils)
        img_sans_fond = self._extraire_produit(img_produit)
        if img_sans_fond is not None:
            fond = self._generer_fond_studio(width=width, height=height)
        else:
            fond = self._generer_fond_festif_flux(prompt, width=width, height=height)
        logo_path = self._resolve_logo_path()
        if logo_path:
            try:
                logo = Image.open(logo_path).convert("RGBA")
                logo = logo.resize((180, 60), Image.LANCZOS)
                fond.paste(logo, (width - logo.width - 40, height - logo.height - 40), logo)
            except Exception:
                pass

        if img_sans_fond is None:
            result = fond.convert("RGB")
            result.save(save_path, quality=95)
            return result

        target_h = int(height * 0.62)
        ratio = target_h / img_sans_fond.height
        target_w = int(img_sans_fond.width * ratio)
        img_resized = img_sans_fond.resize((target_w, target_h), Image.LANCZOS)
        x_prod = (width - target_w) // 2
        y_prod = int(height * 0.10)

        ombre = Image.new("RGBA", (target_w + 40, target_h + 40), (0, 0, 0, 0))
        draw_ombre = ImageDraw.Draw(ombre)
        draw_ombre.ellipse([target_w // 4, target_h - 5, 3 * target_w // 4, target_h + 18], fill=(0, 0, 0, 75))
        ombre = ombre.filter(ImageFilter.GaussianBlur(radius=22))
        lueur = img_resized.filter(ImageFilter.GaussianBlur(radius=18))
        lueur_rgba = lueur.copy()
        lueur_rgba.putalpha(35)
        fond.paste(ombre, (x_prod - 20, y_prod + 15), ombre)
        fond.paste(lueur_rgba, (x_prod, y_prod), lueur_rgba)
        fond.paste(img_resized, (x_prod, y_prod), img_resized)
        result = fond.convert("RGB")
        result.save(save_path, quality=95)
        return result

    def _charger_image_produit(
        self,
        url_image_produit: str | None,
        produit_nom: str | None,
        df_profils: pd.DataFrame | None,
    ) -> Image.Image | None:
        if url_image_produit and str(url_image_produit).startswith("http"):
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                resp = requests.get(url_image_produit, headers=headers, timeout=15)
                resp.raise_for_status()
                return Image.open(BytesIO(resp.content)).convert("RGBA")
            except Exception:
                pass
        if produit_nom and df_profils is not None:
            try:
                row = df_profils[df_profils["produit"] == produit_nom]
                if not row.empty:
                    url_old = row.iloc[0].get("url_image")
                    if pd.notna(url_old) and str(url_old).startswith("http"):
                        resp = requests.get(str(url_old), headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                        resp.raise_for_status()
                        return Image.open(BytesIO(resp.content)).convert("RGBA")
            except Exception:
                pass
        return None

    def _extraire_produit(self, img_pil: Image.Image | None) -> Image.Image | None:
        if img_pil is None:
            return None
        try:
            import numpy as np

            img = img_pil.convert("RGBA")
            data = np.array(img)
            r, g, b = data[:, :, 0], data[:, :, 1], data[:, :, 2]
            data[(r > 240) & (g > 240) & (b > 240), 3] = 0
            return Image.fromarray(data)
        except Exception:
            return img_pil.convert("RGBA")

    def _generer_fond_festif_flux(self, prompt_fond: str, width: int = 1024, height: int = 1024) -> Image.Image:
        if self.hf_api_key:
            try:
                from huggingface_hub import InferenceClient

                client_hf = InferenceClient(api_key=self.hf_api_key)
                fond = client_hf.text_to_image(
                    prompt=(
                        f"{prompt_fond}, elegant abstract luxury background, soft cinematic lighting, "
                        f"premium pharmaceutical aesthetic, NO product, NO bottle, NO people, "
                        f"NO students, NO books, NO text, NO watermark"
                    ),
                    model="black-forest-labs/FLUX.1-schnell",
                    width=width,
                    height=height,
                )
                return fond.convert("RGBA")
            except Exception:
                pass

        image = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(image)
        for y in range(height):
            t = y / height
            color = (int(10 + t * 25), int(37 + t * 45), int(64 + t * 90), 255)
            draw.line((0, y, width, y), fill=color, width=1)
        return image

    def _generer_fond_studio(self, width: int = 1024, height: int = 1024) -> Image.Image:
        image = Image.new("RGBA", (width, height), (245, 246, 248, 255))
        draw = ImageDraw.Draw(image)
        for y in range(height):
            t = y / height
            color = (
                int(250 - t * 12),
                int(251 - t * 15),
                int(252 - t * 18),
                255,
            )
            draw.line((0, y, width, y), fill=color, width=1)

        spotlight = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(spotlight)
        sdraw.ellipse((140, 40, width - 140, height - 260), fill=(255, 255, 255, 140))
        spotlight = spotlight.filter(ImageFilter.GaussianBlur(radius=80))
        image.alpha_composite(spotlight)

        floor = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        fdraw = ImageDraw.Draw(floor)
        fdraw.ellipse((180, height - 250, width - 180, height - 120), fill=(210, 215, 222, 95))
        floor = floor.filter(ImageFilter.GaussianBlur(radius=40))
        image.alpha_composite(floor)
        return image

    def _resolve_logo_path(self) -> Path | None:
        if self.logo_path and self.logo_path.exists():
            return self.logo_path
        return None

    def _load_font(self, size: int):
        for candidate in [
            self.project_root / "assets" / "fonts" / "LiberationSans-Bold.ttf",
            Path("C:/Windows/Fonts/arialbd.ttf"),
            Path("C:/Windows/Fonts/arial.ttf"),
        ]:
            if candidate.exists():
                try:
                    return ImageFont.truetype(str(candidate), size)
                except Exception:
                    continue
        return ImageFont.load_default()

    def _safe_name(self, value: str) -> str:
        return "".join(char if char.isalnum() else "_" for char in value).strip("_").lower()
