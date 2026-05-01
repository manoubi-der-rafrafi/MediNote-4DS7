"""
Medinote -- Delegate ID Bridge Builder
Discovers the link between numeric delegate IDs and name strings,
builds t_delegate_mapping, and documents what CAN and CANNOT be joined.

FINDINGS (from inspection):
  - t_ttc_ht_qte_qte_g.dlg has 3 formats:
      OLD:    "2020-N"      -> maps to t_delegates.id = N
      BU:     "2023BU1DC1"  -> Business Unit / Delegate Code
      NAME:   "2024HANEN"   -> year + first name (most recent delegates)
  - t_delegates (50 rows) = dummy seed data; names don't match real delegates
  - t_prime_rea_obj_r.prime uses IDs 61-500+ range with no bridge table
  - t_id_del_prime_note_de.id_del uses 100-400+ range, also unbridged
  - CONCLUSION: numeric objectives IDs cannot be joined to current sales dlg values
"""

import sys, re, json
sys.path.insert(0, r"C:\Users\omri\Desktop\pii")
import logging; logging.basicConfig(level=logging.WARNING)
from sqlalchemy import text
from db_layer import MedinoteDB

REF_DATE = "2026-01-22"

db = MedinoteDB()

def q(sql, params=None):
    return db.query(text(sql), params or {})

def ex(sql, params=None):
    db.execute(text(sql), params or {})

def sep(t):
    print(f"\n{'='*60}\n  {t}\n{'='*60}")


# =============================================================================
# TASK 1 -- INSPECT SOURCE TABLES
# =============================================================================

sep("TASK 1 -- SOURCE TABLE INSPECTION")

# All distinct dlg values in sales
all_dlg = q("""
    SELECT DISTINCT TRIM(dlg) AS dlg
    FROM   t_ttc_ht_qte_qte_g
    WHERE  dlg IS NOT NULL AND TRIM(dlg) != ''
""")
dlg_list = sorted(all_dlg["dlg"].tolist())
print(f"\n  Total distinct dlg values: {len(dlg_list)}")

old_fmt  = [d for d in dlg_list if re.match(r'^\d{4}-\d+$', d)]
bu_fmt   = [d for d in dlg_list if re.match(r'^\d{4}BU\d', d)]
name_fmt = [d for d in dlg_list if re.match(r'^\d{4}[A-Za-z]', d) and not re.match(r'^\d{4}BU\d', d)]
space_fmt = [d for d in dlg_list if re.match(r'^\d{4} +\w', d)]
other     = [d for d in dlg_list if d not in old_fmt + bu_fmt + name_fmt + space_fmt]

print(f"\n  Format breakdown:")
print(f"    OLD   (2020-N):      {len(old_fmt):3d} values  e.g. {old_fmt[:3]}")
print(f"    BU    (2023BU1DC1):  {len(bu_fmt):3d} values  e.g. {bu_fmt[:3]}")
print(f"    NAME  (2024HANEN):   {len(name_fmt):3d} values  e.g. {name_fmt[:5]}")
print(f"    SPACE (2024 INES):   {len(space_fmt):3d} values  e.g. {space_fmt[:5]}")
print(f"    OTHER:               {len(other):3d} values  e.g. {other[:3]}")

# t_delegates
dels = q("SELECT id, id_delegate, nom, region FROM t_delegates ORDER BY id")
print(f"\n  t_delegates: {len(dels)} rows (dummy seed data)")
print(dels.to_string(index=False))

# t_prime_rea_obj_r
prime = q("SELECT * FROM t_prime_rea_obj_r ORDER BY de DESC LIMIT 15")
print(f"\n  t_prime_rea_obj_r (latest 15 rows):")
print(prime.to_string(index=False))
prime_ids = sorted(q("SELECT DISTINCT prime FROM t_prime_rea_obj_r")["prime"].dropna().astype(int).tolist())
print(f"  Distinct 'prime' IDs ({len(prime_ids)} values): {prime_ids[:20]} ...")

# t_id_del_prime_note_de (active evaluations)
del_eval = q("""
    SELECT DISTINCT id_del FROM t_id_del_prime_note_de
    WHERE de >= '2024-01-01'
    ORDER BY id_del
""")
eval_ids = del_eval["id_del"].dropna().astype(int).tolist()
print(f"\n  t_id_del_prime_note_de 2024+ id_del values ({len(eval_ids)}): {eval_ids[:20]}")


# =============================================================================
# TASK 2 -- BUILD t_delegate_mapping
# =============================================================================

sep("TASK 2 -- BUILD MAPPING TABLE")

ex("DROP TABLE IF EXISTS t_delegate_mapping")
ex("""
    CREATE TABLE t_delegate_mapping (
        delegate_name         VARCHAR(100)  NOT NULL,
        delegate_id           INT           DEFAULT NULL,
        delegate_display_name VARCHAR(200)  DEFAULT NULL,
        zone                  VARCHAR(100)  DEFAULT NULL,
        governorate           VARCHAR(100)  DEFAULT NULL,
        dlg_format            VARCHAR(20)   DEFAULT NULL,
        PRIMARY KEY (delegate_name)
    )
""")
print("  t_delegate_mapping created / cleared")

# ── A: OLD format "2020-N" → t_delegates ─────────────────────
old_rows = 0
del_by_id = {int(r["id"]): r for _, r in dels.iterrows()}

for dlg in old_fmt:
    m = re.match(r'^(\d{4})-(\d+)$', dlg)
    if not m:
        continue
    num = int(m.group(2))
    del_row = del_by_id.get(num)
    if del_row is not None:
        ex("""
            INSERT INTO t_delegate_mapping
                (delegate_name, delegate_id, delegate_display_name, zone, governorate, dlg_format)
            VALUES (:name, :id, :display, :zone, :gouv, 'old')
            ON DUPLICATE KEY UPDATE
                delegate_id=VALUES(delegate_id),
                delegate_display_name=VALUES(delegate_display_name),
                zone=VALUES(zone), governorate=VALUES(governorate)
        """, dict(
            name=dlg,
            id=int(del_row["id_delegate"]),
            display=str(del_row["nom"]),
            zone=str(del_row["region"]) if del_row["region"] else None,
            gouv=str(del_row["region"]) if del_row["region"] else None,
        ))
    else:
        ex("""
            INSERT INTO t_delegate_mapping (delegate_name, dlg_format)
            VALUES (:name, 'old')
            ON DUPLICATE KEY UPDATE dlg_format=VALUES(dlg_format)
        """, dict(name=dlg))
    old_rows += 1

print(f"  OLD format rows inserted: {old_rows}")

# ── B: BU format "2023BU1DC1" ────────────────────────────────
bu_rows = 0
for dlg in bu_fmt:
    m = re.match(r'^(\d{4})(BU\d+)(DC\d+)$', dlg.strip())
    display = f"BU={m.group(2)} DC={m.group(3)}" if m else dlg
    ex("""
        INSERT INTO t_delegate_mapping (delegate_name, delegate_display_name, dlg_format)
        VALUES (:name, :display, 'bu')
        ON DUPLICATE KEY UPDATE delegate_display_name=VALUES(delegate_display_name)
    """, dict(name=dlg.strip(), display=display))
    bu_rows += 1
print(f"  BU  format rows inserted: {bu_rows}")

# ── C: NAME format "2024HANEN" ────────────────────────────────
name_rows = 0
for dlg in name_fmt:
    raw_dlg = dlg.strip()
    m = re.match(r'^(\d{4})\s*(.+)$', raw_dlg)
    year       = m.group(1) if m else "????"
    name_part  = m.group(2).strip().title() if m else raw_dlg
    display    = f"{name_part} ({year})"
    ex("""
        INSERT INTO t_delegate_mapping (delegate_name, delegate_display_name, dlg_format)
        VALUES (:name, :display, 'name')
        ON DUPLICATE KEY UPDATE delegate_display_name=VALUES(delegate_display_name)
    """, dict(name=raw_dlg, display=display))
    name_rows += 1
print(f"  NAME format rows inserted: {name_rows}")

# ── D: SPACE format "2024 INES" ───────────────────────────────
space_rows = 0
for dlg in space_fmt:
    raw_dlg = dlg.strip()
    m = re.match(r'^(\d{4})\s+(.+)$', raw_dlg)
    year      = m.group(1) if m else "????"
    name_part = m.group(2).strip().title() if m else raw_dlg
    display   = f"{name_part} ({year})"
    ex("""
        INSERT INTO t_delegate_mapping (delegate_name, delegate_display_name, dlg_format)
        VALUES (:name, :display, 'name')
        ON DUPLICATE KEY UPDATE delegate_display_name=VALUES(delegate_display_name)
    """, dict(name=raw_dlg, display=display))
    space_rows += 1
print(f"  SPACE format rows inserted: {space_rows}")

total_rows = q("SELECT COUNT(*) AS n FROM t_delegate_mapping").iloc[0]["n"]
print(f"\n  Total in t_delegate_mapping: {total_rows}")

# Print the name-format rows (most relevant for current sales data)
mapping_name = q("""
    SELECT delegate_name, delegate_id, delegate_display_name, zone, dlg_format
    FROM   t_delegate_mapping
    WHERE  dlg_format = 'name'
    ORDER  BY delegate_name
""")
print(f"\n  NAME-format delegates in mapping:")
print(mapping_name.to_string(index=False))

# JSON export
full_mapping = q("SELECT * FROM t_delegate_mapping ORDER BY dlg_format, delegate_name")
mapping_json = full_mapping.to_dict("records")
print(f"\n  Mapping JSON (name-format only):")
name_only = [r for r in mapping_json if r.get("dlg_format") == "name"]
print(json.dumps(name_only[:15], ensure_ascii=False, indent=2, default=str))


# =============================================================================
# TASK 3 -- VERIFY MAPPING
# =============================================================================

sep("TASK 3 -- VERIFY MAPPING")

verify = q("""
    SELECT
        s.dlg                                   AS delegate_name,
        m.delegate_id,
        m.delegate_display_name                 AS display_name,
        m.governorate,
        m.dlg_format,
        ROUND(SUM(s.ttc), 0)                    AS revenue_12m
    FROM   t_ttc_ht_qte_qte_g s
    LEFT   JOIN t_delegate_mapping m ON TRIM(s.dlg) = m.delegate_name
    WHERE  DATE(s.date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
    GROUP  BY s.dlg, m.delegate_id, m.delegate_display_name, m.governorate, m.dlg_format
    ORDER  BY revenue_12m DESC
    LIMIT  20
""", {"ref": REF_DATE})

print(verify.to_string(index=False))

matched   = verify["display_name"].notna().sum()
unmatched = verify["display_name"].isna().sum()
print(f"\n  Matched to display name: {matched}/{len(verify)}")
print(f"  Unmatched:               {unmatched}/{len(verify)}")

if unmatched > 0:
    print("  Unmatched dlg values (need manual mapping):")
    print("  ", verify[verify["display_name"].isna()]["delegate_name"].tolist())


# =============================================================================
# TASK 4 -- OBJECTIVES WITH REAL REVENUE
# =============================================================================

sep("TASK 4 -- OBJECTIVES VS ACTUAL REVENUE")

# First: show what prime IDs exist in t_prime_rea_obj_r for recent periods
recent_prime = q("""
    SELECT prime, obj, rea, de, a
    FROM   t_prime_rea_obj_r
    WHERE  a >= '2024-01-01'
    ORDER  BY de DESC
    LIMIT  20
""")

if len(recent_prime):
    print(f"\n  Recent objectives records ({len(recent_prime)} rows):")
    print(recent_prime.to_string(index=False))
else:
    # Fall back to most recent regardless of year
    recent_prime = q("""
        SELECT prime, obj, rea, de, a
        FROM   t_prime_rea_obj_r
        ORDER  BY a DESC
        LIMIT  20
    """)
    print(f"\n  Most recent objectives (no 2024+ data, showing latest available):")
    print(recent_prime.to_string(index=False))

# What we CAN join: t_prime_rea_obj_r.prime -> t_id_del_prime_note_de.prime -> id_del
# but t_id_del_prime_note_de.id_del values don't match t_delegates.id_delegate
print(f"\n  ID MISMATCH SUMMARY:")
print(f"    t_delegates.id_delegate range:        1 - {dels['id_delegate'].max()}")
print(f"    t_prime_rea_obj_r.prime range:        {prime_ids[0]} - {prime_ids[-1]}")
print(f"    t_id_del_prime_note_de 2024 id_del:   {eval_ids[:5]} ...")
print(f"")
print(f"  CONCLUSION: No valid bridge exists between:")
print(f"    - Sales dlg name strings ('2024HANEN', '2024OMAR', ...)")
print(f"    - Objectives numeric IDs (prime=61, 134, ...)")
print(f"")
print(f"  What IS available:")
print(f"    - 'name' format delegates: human-readable (e.g. 'Hanen 2024')")
print(f"    - Revenue per delegate from sales (fully working)")
print(f"    - t_id_del_caph_cagro_obj: has caph/cagro/obj by id_del")
print(f"      -> if the CRM app knows the mapping id_del <-> dlg name,")
print(f"         that link is in application code, not in the DB")

# ── Partial objectives via t_id_del_caph_cagro_obj (best available) ──────
ca_obj = q("""
    SELECT id_del, year, obj, caph, cagro
    FROM   t_id_del_caph_cagro_obj
    WHERE  year = 2024 AND obj > 0
    ORDER  BY obj DESC
    LIMIT  20
""")
print(f"\n  t_id_del_caph_cagro_obj 2024 records with obj > 0 ({len(ca_obj)} rows):")
print(ca_obj.to_string(index=False))

# ── Revenue per delegate (fully working -- no join needed) ────────────────
print(f"\n  Actual revenue per delegate (2024, from sales table):")
del_rev = q("""
    SELECT
        TRIM(dlg)                  AS delegate_name,
        ROUND(SUM(ttc), 0)         AS revenue_12m,
        COUNT(DISTINCT cl)         AS pharmacies,
        COUNT(DISTINCT DATE(date)) AS active_days
    FROM   t_ttc_ht_qte_qte_g
    WHERE  DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
      AND  dlg IS NOT NULL AND TRIM(dlg) != ''
    GROUP  BY TRIM(dlg)
    ORDER  BY revenue_12m DESC
    LIMIT  20
""", {"ref": REF_DATE})
print(del_rev.to_string(index=False))

db.close()
print("\n\nDone.")
