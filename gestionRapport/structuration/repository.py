from __future__ import annotations

from db.models import StructuredReport
from db.session import session_scope

from .schemas import PointFortStructured


def save_structured_report(
    raw_text: str,
    structured_report: PointFortStructured,
) -> StructuredReport:
    payload = structured_report.model_dump()

    with session_scope() as session:
        row = StructuredReport(
            raw_text=raw_text,
            text_corrige=payload["text_corrige"],
            mouvement=payload["mouvement"],
            potentiel=payload["potentiel"],
            conseil=payload["conseil"],
            emplacement_proximite=payload["emplacement_proximite"],
            emplacement_qualite=payload["emplacement_qualite"],
            personnel_attitude=payload["personnel_attitude"],
            mise_en_place=payload["mise_en_place"],
            invitations=payload["invitations"],
            stock_disponibilite=payload["stock_disponibilite"],
            type_pharmacie=payload["type_pharmacie"],
            eligibilite_animation=payload["eligibilite_animation"],
            aucun_point_fort=payload["aucun_point_fort"],
        )
        session.add(row)
        session.flush()
        session.refresh(row)
        return row


def delete_structured_report(report_id: int) -> StructuredReport | None:
    with session_scope() as session:
        row = session.get(StructuredReport, int(report_id))
        if row is None:
            return None

        session.delete(row)
        session.flush()
        return row
