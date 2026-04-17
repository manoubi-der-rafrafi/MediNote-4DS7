from typing import Literal

from pydantic import BaseModel


class PointFortStructured(BaseModel):
    text_corrige: str
    mouvement: Literal[
        "aucun",
        "tres_faible",
        "faible",
        "moyen",
        "forte",
        "tres_forte",
        "non_precise",
    ]
    potentiel: Literal["aucun", "faible", "moyen", "forte", "non_precise"]
    conseil: Literal["aucun", "faible", "moyen", "forte", "non_precise"]
    emplacement_proximite: Literal[
        "cabinets",
        "cabines",
        "dispensaire",
        "hopital",
        "centre_ville",
        "usines",
        "salle_de_sport",
        "marche",
        "autre",
        "non_precise",
    ]
    emplacement_qualite: Literal["adequat", "inadequat", "non_precise"]
    personnel_attitude: Literal[
        "positive",
        "negative",
        "positive_et_negative",
        "non_precise",
    ]
    mise_en_place: Literal["absente", "faible", "moyenne", "forte", "non_precise"]
    invitations: Literal["non_distribuees", "distribuees", "non_precise"]
    stock_disponibilite: Literal["rupture", "faible", "important", "non_precise"]
    type_pharmacie: Literal[
        "pharmacie_de_conseil",
        "pharmacie_de_passage",
        "pharmacie_de_nuit",
        "pharmacie_de_convention",
        "quartier_populaire",
        "autre",
        "non_precise",
    ]
    eligibilite_animation: Literal[
        "favorable",
        "a_revoir",
        "defavorable",
        "ne_merite_pas_animation",
        "non_precise",
    ]
    aucun_point_fort: Literal["oui", "non"]
