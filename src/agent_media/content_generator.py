from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .calendar_utils import SAISONS_MAPPING


@dataclass(slots=True)
class ContentGenerator:
    df_profils: pd.DataFrame
    df_tn: pd.DataFrame
    fetes_mapping: dict[str, dict[str, Any]]
    mistral_api_key: str | None = None

    def generate_dual_holiday_posts(self, fete_nom: str, top_produit: str | None, plateformes: list[str] = ["Facebook", "Instagram"]) -> dict[str, dict]:
        fete_info = self.fetes_mapping.get(fete_nom, {})
        fete_data = self.df_tn[self.df_tn["Holiday_Name"] == fete_nom]
        fete_desc = self._safe_value(fete_data, "Description")
        fete_local = self._safe_value(fete_data, "Local_Name")
        
        result = {"instit": {}, "produit": {}}
        
        # Posts 1: Fêtes/Institutionnels (corporate)
        for plateforme in plateformes:
            post = self.generate_post(None, fete_nom, plateforme)  # None = institutional
            result["instit"][plateforme.lower()] = post
        
        # Posts 2: Saisonnières/Produit (top product)
        if top_produit:
            for plateforme in plateformes:
                post = self.generate_post(top_produit, fete_nom, plateforme)
                result["produit"][plateforme.lower()] = post
        else:
            for plateforme in plateformes:
                # Fallback seasonal without specific product
                post = self.generate_season_post("Vital Complex", "Hiver - Immunite & Grippe", plateforme)
                result["produit"][plateforme.lower()] = post.replace("Hiver - Immunite & Grippe", fete_nom)
        
        return result
    
    def generate_post(self, produit_nom: str | None, fete_nom: str, plateforme: str = "Facebook") -> str:
        fete_info = self.fetes_mapping.get(fete_nom, {})
        fete_data = self.df_tn[self.df_tn["Holiday_Name"] == fete_nom]
        fete_desc = self._safe_value(fete_data, "Description")
        fete_local = self._safe_value(fete_data, "Local_Name")
        ton = fete_info.get("ton", "professionnel et chaleureux")
        horaire = fete_info.get("horaire", "18h00")
        fete_type = fete_info.get("type", "avec_produit")

        if fete_type == "institutionnel" or not produit_nom:
            prompt = self._build_institutional_prompt(
                fete_nom=fete_nom,
                fete_local=fete_local,
                fete_desc=fete_desc,
                plateforme=plateforme,
                ton=ton,
                horaire=horaire,
                message=fete_info.get("message_institutionnel", ""),
            )
            generated = self._call_mistral(prompt)
            if generated:
                return generated
            return self._fallback_institutional_post(fete_nom)

        profil = self._find_profil(produit_nom)
        if profil is None:
            return f"Produit introuvable: {produit_nom}"
        contexte_sante = fete_info.get("contexte_sante", "")
        prompt = self._build_product_prompt(
            profil=profil,
            fete_nom=fete_nom,
            fete_local=fete_local,
            plateforme=plateforme,
            ton=ton,
            horaire=horaire,
            contexte_sante=contexte_sante,
        )
        generated = self._call_mistral(prompt)
        if generated:
            return generated
        return self._fallback_product_post(profil, fete_nom, contexte_sante)

    def generate_season_post(self, produit_nom: str, nom_saison: str, plateforme: str = "Facebook") -> str:
        profil = self._find_profil(produit_nom)
        if profil is None:
            return f"Produit introuvable: {produit_nom}"
        saison_info = SAISONS_MAPPING[nom_saison]
        prompt = self._build_season_prompt(
            profil=profil,
            nom_saison=nom_saison,
            plateforme=plateforme,
            saison_info=saison_info,
        )
        generated = self._call_mistral(prompt)
        if generated:
            return generated
        return self._fallback_season_post(profil, nom_saison, saison_info)

    def _build_institutional_prompt(
        self,
        fete_nom: str,
        fete_local: str,
        fete_desc: str,
        plateforme: str,
        ton: str,
        horaire: str,
        message: str,
    ) -> str:
        longueur = {"Facebook": "100 mots max", "Instagram": "60 mots max + emojis"}.get(plateforme, "100 mots")
        return f"""Tu es le responsable communication de Vital Laboratories Tunisie.

CONTEXTE :
- Fete : {fete_nom} ({fete_local})
- Description : {fete_desc}
- Ton : {ton}
- Plateforme : {plateforme}
- Message suggere : {message}

MISSION :
Redige un post {plateforme} de marque pour cette fete nationale.
Ce post ne doit PAS mentionner de produit.
Il exprime la solidarite et les valeurs de Vital Laboratories.

REGLES DE STYLE :
- Longueur : {longueur}
- Commence directement par l'accroche
- Ton chaleureux et sincere, adapte a la culture tunisienne
- Mentionne "Vital Laboratories" naturellement
- 3-4 hashtags pertinents
- Horaire recommande : {horaire}

EXEMPLES DE BON STYLE :
✅ "En ce jour de commemoration, Vital Laboratories s'incline devant..."
✅ "Chaque 9 avril, nous nous souvenons..."
❌ EVITER : "En ce jour special, nous tenons a vous souhaiter..."
❌ EVITER : phrases trop formelles ou generiques

FORMAT :
Ecris DIRECTEMENT le texte sans titre, sans introduction.
Commence immediatement par l'accroche en francais naturel.
HASHTAGS: #...
HORAIRE: {horaire}"""

    def _build_product_prompt(
        self,
        profil: pd.Series,
        fete_nom: str,
        fete_local: str,
        plateforme: str,
        ton: str,
        horaire: str,
        contexte_sante: str,
    ) -> str:
        longueur = {
            "Facebook": "120-150 mots",
            "Instagram": "70-90 mots + emojis pertinents + hashtags",
            "LinkedIn": "150-200 mots, ton professionnel medical",
        }.get(plateforme, "120-150 mots")

        pts_pos = str(profil.get("points_positifs", ""))[:300]
        verdict = str(profil.get("verdict", ""))[:150]
        points_negatifs = str(profil.get("points_negatifs", ""))

        return f"""Tu es le responsable marketing de Vital Laboratories Tunisie.
Tu rediges des posts sociaux professionnels et naturels, jamais trop commerciaux.

=== CONTEXTE DE LA FETE ===
Fete : {fete_nom} ({fete_local})
Contexte sante lie : {contexte_sante}
Ton a adopter : {ton}

=== PROFIL DU PRODUIT ===
Nom : {profil['produit']}
Ce que ce produit fait exactement : {profil.get('indications', '')}
Ingredients principaux : {profil.get('composition', '')}
Ce que les clients disent (avis reels) : {pts_pos}
Verdict general : {verdict}
A ne jamais mentionner : {points_negatifs}

=== CONSIGNE DE REDACTION ===
Ecris un post {plateforme} naturel et convaincant.
Longueur : {longueur}

STRUCTURE OBLIGATOIRE :
1. ACCROCHE (1 phrase) : commence par le contexte de la fete,
   une question ou une observation liee a la sante pendant cette periode.
   NE PAS commencer par le nom du produit.
   NE PAS commencer par "En ce jour" ou "A l'occasion de"

2. TRANSITION (1-2 phrases) : lien naturel entre la fete et le besoin sante.

3. PRODUIT (2-3 phrases) : presente le produit comme une solution,
   utilise les vrais avis clients et les vrais benefices.
   Sois precis, cite un ingredient cle ou un benefice concret.

4. CALL TO ACTION (1 phrase) : doux, pas agressif.

5. HASHTAGS : 4-5 hashtags francais + 1-2 arabe si naturel.

EXEMPLES DE BON STYLE :
✅ "Avec Eid, les tablees genereuses peuvent peser lourd...
Vital Fersang, enrichi en spiruline, aide votre corps a mieux recuperer.
Disponible en pharmacie."

✅ "Le jeune du Ramadan modifie notre rythme. La fatigue s'installe.
Vital Fersang au fer fumarate hautement assimilable accompagne
des milliers de Tunisiennes depuis des annees. Essayez-le ce Ramadan."

❌ EVITER : "En ce jour festif, nous sommes ravis de vous presenter notre produit..."
❌ EVITER : phrases vagues sans benefice concret
❌ EVITER : "Notre produit revolutionnaire..."
❌ EVITER : phrases trop longues et compliquees
❌ EVITER : mentionner {points_negatifs}

Horaire recommande : {horaire}

FORMAT DE REPONSE :
Ecris DIRECTEMENT le texte du post sans aucun titre,
sans [TEXTE DU POST], sans introduction.
Commence immediatement par l'accroche.
Le texte doit etre en francais naturel tunisien,
chaleureux et authentique.
Pas de gras autour du texte principal."""

    def _build_season_prompt(
        self,
        profil: pd.Series,
        nom_saison: str,
        plateforme: str,
        saison_info: dict[str, Any],
    ) -> str:
        longueur = {"Facebook": "120-150 mots", "Instagram": "70-90 mots + emojis + hashtags"}.get(
            plateforme, "120 mots"
        )
        pts_pos = str(profil.get("points_positifs", ""))[:300]
        verdict = str(profil.get("verdict", ""))[:150]

        return f"""Tu es le responsable marketing de Vital Laboratories Tunisie.

=== CONTEXTE DE LA PERIODE ===
Periode : {nom_saison}
Contexte sante : {saison_info['contexte_sante']}
Ton a adopter : {saison_info['ton']}

=== PROFIL DU PRODUIT ===
Nom : {profil['produit']}
Ce que ce produit fait exactement : {profil.get('indications', '')}
Ingredients principaux : {profil.get('composition', '')}
Ce que les clients disent : {pts_pos}
Verdict general : {verdict}
A ne jamais mentionner : {profil.get('points_negatifs', '')}

=== CONSIGNE ===
Ecris un post {plateforme} naturel et convaincant.
Longueur : {longueur}
STRUCTURE :
1. ACCROCHE : contexte de la periode, observation sante.
2. TRANSITION : lien entre la periode et le besoin.
3. PRODUIT : solution concrete avec ingredient cle.
4. CALL TO ACTION : doux.
5. HASHTAGS : 4-5 francais + 1-2 arabe.
Ecris DIRECTEMENT le texte, sans titre ni introduction.
Francais naturel tunisien, chaleureux."""

    def _call_mistral(self, prompt: str) -> str | None:
        if not self.mistral_api_key:
            return None
        try:
            try:
                from mistralai.client import Mistral
            except Exception:
                from mistralai import Mistral

            client = Mistral(api_key=self.mistral_api_key)
            response = client.chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.75,
            )
            content = response.choices[0].message.content
            if not content:
                return None
            return self._cleanup_response(content)
        except Exception:
            return None

    def _cleanup_response(self, content: str) -> str:
        cleaned = str(content).strip()
        cleaned = cleaned.replace("[TEXTE DU POST]", "").strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`").strip()
        return cleaned

    def _fallback_institutional_post(self, fete_nom: str) -> str:
        hashtags = self._hashtags_from_text(fete_nom, "Vital Laboratories Tunisie")
        return (
            f"En cette journee de {fete_nom}, Vital Laboratories Tunisie rend hommage aux valeurs de respect, "
            f"de memoire et d'unite qui rassemblent les Tunisiennes et les Tunisiens. "
            f"Nous partageons ce moment avec sincerite et solidarite. {hashtags}"
        )

    def _fallback_product_post(self, profil: pd.Series, fete_nom: str, contexte_sante: str) -> str:
        benefit = profil.get("indications", "") or profil.get("theme", "") or "les besoins du quotidien"
        ingredient = profil.get("composition", "") or "sa formule ciblee"
        proof = profil.get("points_positifs", "") or profil.get("verdict", "") or "une bonne perception client"
        hashtags = self._hashtags_from_text(fete_nom, f"{profil['produit']} {benefit}")
        return (
            f"Avec {fete_nom}, {contexte_sante.lower()} {profil['produit']} peut accompagner cette periode grace a {ingredient}. "
            f"Ce produit aide a soutenir {benefit}, avec des retours clients qui mettent en avant {proof}. "
            f"Disponible en pharmacie. {hashtags}"
        )

    def _fallback_season_post(self, profil: pd.Series, nom_saison: str, saison_info: dict[str, Any]) -> str:
        hashtags = self._hashtags_from_text(nom_saison, saison_info["pic_vente"])
        return (
            f"{nom_saison}: quand {saison_info['contexte_sante'].lower()} {profil['produit']} apporte une reponse concrete "
            f"grace a {profil.get('composition', '') or 'sa formule ciblee'}. "
            f"Ses benefices sur {profil.get('indications', '') or 'le bien-etre quotidien'} en font une option utile pour cette periode. "
            f"Disponible en pharmacie. {hashtags}"
        )

    def _hashtags_from_text(self, primary: str, secondary: str) -> str:
        tokens = []
        for raw in f"{primary} {secondary} Vital Tunisie".split():
            clean = "".join(ch for ch in raw if ch.isalnum())
            if len(clean) < 3:
                continue
            tag = f"#{clean.capitalize()}"
            if tag not in tokens:
                tokens.append(tag)
        return " ".join(tokens[:6])

    def _safe_value(self, frame: pd.DataFrame, column: str) -> str:
        if frame.empty or column not in frame.columns:
            return ""
        value = frame[column].iloc[0]
        if pd.isna(value):
            return ""
        return str(value)

    def _find_profil(self, produit_nom: str) -> pd.Series | None:
        exact = self.df_profils[self.df_profils["produit"] == produit_nom]
        if not exact.empty:
            return exact.iloc[0]

        normalized_target = self._normalize(produit_nom)
        normalized_products = self.df_profils["produit"].astype(str).apply(self._normalize)
        partial = self.df_profils[normalized_products == normalized_target]
        if not partial.empty:
            return partial.iloc[0]

        contains = self.df_profils[normalized_products.str.contains(normalized_target, regex=False, na=False)]
        if not contains.empty:
            return contains.iloc[0]
        return None

    def _normalize(self, value: str) -> str:
        return (
            str(value)
            .lower()
            .replace("é", "e")
            .replace("è", "e")
            .replace("ê", "e")
            .replace("à", "a")
            .replace("ù", "u")
            .replace("î", "i")
            .replace("ï", "i")
            .replace("ô", "o")
            .replace("â", "a")
            .replace("ç", "c")
            .replace("œ", "oe")
            .replace("?", "")
        )
