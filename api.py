"""
Medinote REST API
Run: uvicorn api:app --reload --port 8000
Docs: http://localhost:8000/docs
"""

import sys, os, json, time, hashlib, logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict, List

sys.path.insert(0, r"c:\Users\omri\Desktop\pii")

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
import bcrypt as _bcrypt_lib
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import text

from db_layer import MedinoteDB
from orchestrator import OrchestratorAgent
from deep_analysis import DeepAnalysis, _safe
from feedback_loop import ModelHealthMonitor

log = logging.getLogger("medinote.api")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")

# =============================================================================
# CONSTANTS
# =============================================================================

SECRET_KEY   = "medinote-jwt-secret-2026-change-in-production"
ALGORITHM    = "HS256"
TOKEN_HOURS  = 8
REF_DATE     = "2026-01-22"
USERS_FILE   = os.path.join(os.path.dirname(__file__), "users.json")

ROLES_ALL    = {"DIRECTION", "COMMERCIAL"}
ROLES_MGMT   = {"DIRECTION", "COMMERCIAL", "SUPERVISEUR"}

# =============================================================================
# APP + CORS
# =============================================================================

app = FastAPI(title="Medinote AI API", version="1.0.0", description="Pharma CRM Intelligence")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# GLOBAL STATE (set at startup)
# =============================================================================

_db:       Optional[MedinoteDB]          = None
_orch:     Optional[OrchestratorAgent]   = None
_analysis: Optional[DeepAnalysis]        = None
_cache:    Dict[str, dict]               = {}

def get_db() -> MedinoteDB:
    if _db is None:
        raise HTTPException(500, "Database not initialized")
    return _db

def get_orch() -> OrchestratorAgent:
    if _orch is None:
        raise HTTPException(500, "Orchestrator not initialized")
    return _orch

# =============================================================================
# CACHE
# =============================================================================

def cache_get(key: str) -> Optional[Any]:
    entry = _cache.get(key)
    if entry and time.time() - entry["ts"] < entry["ttl"]:
        return entry["data"]
    return None

def cache_set(key: str, data: Any, ttl: int = 3600):
    _cache[key] = {"data": data, "ts": time.time(), "ttl": ttl}

def cache_clear(prefix: str = ""):
    keys = [k for k in list(_cache) if k.startswith(prefix)]
    for k in keys:
        del _cache[k]

# =============================================================================
# AUTH HELPERS
# =============================================================================

oauth2  = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(pw: str) -> str:
    return _bcrypt_lib.hashpw(pw.encode(), _bcrypt_lib.gensalt()).decode()

def verify_password(pw: str, hashed: str) -> bool:
    return _bcrypt_lib.checkpw(pw.encode(), hashed.encode())

def create_token(data: dict) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS)
    return jwt.encode({**data, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")

# =============================================================================
# USER STORE
# =============================================================================

def _load_users() -> list:
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["users"]

def _get_user(username: str) -> Optional[dict]:
    return next((u for u in _load_users() if u["username"] == username), None)

def _init_users_json():
    if os.path.exists(USERS_FILE):
        return
    pw = hash_password("medinote2026")
    users = {"users": [
        {"id": "u001", "username": "direction",      "password_hash": pw,
         "role": "DIRECTION",  "zone": None,       "delegate_id": None,
         "display_name": "Direction Generale"},
        {"id": "u002", "username": "hanen2024",      "password_hash": pw,
         "role": "DELEGUE",    "zone": "SFAX 1A",  "delegate_id": "2024HANEN",
         "display_name": "Hanen"},
        {"id": "u003", "username": "ines2024",       "password_hash": pw,
         "role": "DELEGUE",    "zone": "TUNIS 3",  "delegate_id": "2024 INES",
         "display_name": "Ines"},
        {"id": "u004", "username": "commercial",     "password_hash": pw,
         "role": "COMMERCIAL", "zone": None,       "delegate_id": None,
         "display_name": "Responsable Commercial"},
        {"id": "u005", "username": "sup_sfax",       "password_hash": pw,
         "role": "SUPERVISEUR","zone": "SFAX 1A",  "delegate_id": None,
         "display_name": "Superviseur Sfax"},
        {"id": "u006", "username": "sup_tunis",      "password_hash": pw,
         "role": "SUPERVISEUR","zone": "TUNIS 3",  "delegate_id": None,
         "display_name": "Superviseur Tunis"},
        {"id": "u007", "username": "animatrice01",   "password_hash": pw,
         "role": "ANIMATRICE", "zone": None,       "delegate_id": None,
         "display_name": "Animatrice 01"},
    ]}
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    log.info("Created users.json  (default password: medinote2026)")

# =============================================================================
# AUTH DEPENDENCY
# =============================================================================

async def current_user(token: str = Depends(oauth2)) -> dict:
    payload = decode_token(token)
    user = _get_user(payload.get("sub", ""))
    if not user:
        raise HTTPException(401, "User not found")
    return user

# =============================================================================
# RESPONSE + ROLE HELPERS
# =============================================================================

def _sanitize(obj: Any) -> Any:
    """Recursively replace NaN/Inf and numpy types so JSON serialization never fails."""
    import math
    # numpy scalar types
    try:
        import numpy as np
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            v = float(obj)
            return None if (math.isnan(v) or math.isinf(v)) else v
        if isinstance(obj, np.ndarray):
            return _sanitize(obj.tolist())
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
    except ImportError:
        pass
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj

def resp(data: Any = None, message: str = "OK") -> dict:
    return {"status": "success", "data": _sanitize(data), "message": message,
            "timestamp": datetime.now().isoformat()}

def err(msg: str, code: int = 400):
    raise HTTPException(status_code=code,
                        detail={"status": "error", "message": msg})

def require_role(user: dict, *roles: str):
    if user["role"] not in roles:
        raise HTTPException(403, f"Role '{user['role']}' cannot access this resource")

def is_mobile(request: Request) -> bool:
    return request.headers.get("X-Client", "").lower() == "mobile"

def _delegate_pharmacies(delegate_id: str) -> set:
    try:
        rows = get_db().query(
            text("SELECT DISTINCT cl FROM t_cl_dlg WHERE TRIM(dlg) = :dlg"),
            {"dlg": delegate_id.strip()},
        )
        return set(rows["cl"].tolist())
    except Exception:
        return set()

def filter_results(results: list, user: dict) -> list:
    role = user["role"]
    if role in ROLES_ALL:
        return results
    if role == "DELEGUE":
        my_ph = _delegate_pharmacies(user.get("delegate_id", ""))
        return [r for r in results
                if r.get("entity_id") in my_ph
                or r.get("cl") in my_ph
                or str(r.get("dlg", "")).strip() == user.get("delegate_id", "")]
    if role == "SUPERVISEUR":
        z = user.get("zone", "")
        return [r for r in results if r.get("zone", "") == z]
    return results  # ANIMATRICE sees all animation results

def _role_permissions(role: str) -> list:
    base = ["dashboard", "predict", "chat", "alerts"]
    if role in ROLES_ALL:
        return base + ["analytics_all", "all_delegates", "all_zones", "model_health"]
    if role == "SUPERVISEUR":
        return base + ["analytics_zone", "zone_delegates"]
    if role == "DELEGUE":
        return base + ["my_pharmacies", "my_performance", "visit_plan"]
    if role == "ANIMATRICE":
        return base + ["my_animations"]
    return base

# =============================================================================
# AUTH ENDPOINTS
# =============================================================================

class LoginBody(BaseModel):
    username: str
    password: str

@app.post("/auth/login", tags=["Auth"])
async def login(body: LoginBody):
    user = _get_user(body.username)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    token = create_token({"sub": user["username"], "role": user["role"]})
    return resp({
        "access_token": token,
        "token_type":   "bearer",
        "role":         user["role"],
        "display_name": user["display_name"],
        "permissions":  _role_permissions(user["role"]),
    })

@app.get("/auth/me", tags=["Auth"])
async def me(user: dict = Depends(current_user)):
    return resp({k: v for k, v in user.items() if k != "password_hash"})

# =============================================================================
# DASHBOARD KPIs
# =============================================================================

@app.get("/dashboard/kpis", tags=["Dashboard"])
async def dashboard_kpis(request: Request, user: dict = Depends(current_user)):
    role      = user["role"]
    cache_key = f"kpis:{role}:{user.get('zone','')}"
    cached    = cache_get(cache_key)
    if cached:
        return resp(cached)

    db = get_db()
    try:
        if role in ROLES_ALL:
            data = _kpis_direction(db)
        elif role == "DELEGUE":
            data = _kpis_delegue(db, user)
        elif role == "SUPERVISEUR":
            data = _kpis_superviseur(db, user)
        else:
            data = {}
    except Exception as e:
        log.error("KPI error: %s", e)
        data = {"error": str(e)}

    cache_set(cache_key, data, 3600)
    return resp(data)


def _q(db, sql, params=None):
    return db.query(text(sql), params or {})

def _kpis_direction(db: MedinoteDB) -> dict:
    ref = REF_DATE

    rev = _q(db, """
        SELECT
            SUM(CASE WHEN DATE(date) >= DATE_SUB(:ref, INTERVAL 30 DAY)  THEN ttc ELSE 0 END) AS r30,
            SUM(CASE WHEN DATE(date) BETWEEN DATE_SUB(:ref, INTERVAL 60 DAY)
                         AND DATE_SUB(:ref, INTERVAL 30 DAY) THEN ttc ELSE 0 END)              AS r60
        FROM t_ttc_ht_qte_qte_g
        WHERE DATE(date) >= DATE_SUB(:ref, INTERVAL 60 DAY)
    """, {"ref": ref})
    r30    = float(rev.iloc[0]["r30"] or 0)
    r60    = float(rev.iloc[0]["r60"] or 0)
    growth = round((r30 - r60) / r60 * 100, 1) if r60 else 0

    ph = _q(db, """
        SELECT cl, DATEDIFF(:ref, MAX(DATE(date))) AS days
        FROM t_ttc_ht_qte_qte_g
        WHERE DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
        GROUP BY cl
    """, {"ref": ref})
    churned = int((ph["days"] > 240).sum())
    at_risk = int(ph["days"].between(90, 240).sum())

    dlg = _q(db, """
        SELECT COUNT(DISTINCT TRIM(dlg)) AS n
        FROM t_ttc_ht_qte_qte_g
        WHERE DATE(date) >= DATE_SUB(:ref, INTERVAL 30 DAY)
          AND dlg IS NOT NULL AND TRIM(dlg) != ''
    """, {"ref": ref})

    zones = _q(db, """
        SELECT zone, ROUND(SUM(ttc),0) AS rev
        FROM t_ttc_ht_qte_qte_g
        WHERE DATE(date) >= DATE_SUB(:ref, INTERVAL 30 DAY)
          AND zone IS NOT NULL AND zone != ''
        GROUP BY zone ORDER BY rev DESC LIMIT 5
    """, {"ref": ref})

    prod = _q(db, """
        SELECT art FROM t_ttc_ht_qte_qte_g
        WHERE DATE(date) >= DATE_SUB(:ref, INTERVAL 30 DAY)
        GROUP BY art ORDER BY SUM(ttc) DESC LIMIT 1
    """, {"ref": ref})

    alerts = _build_alerts(db, user=None)

    return {
        "total_revenue_30d":   round(r30, 0),
        "revenue_growth_pct":  growth,
        "total_pharmacies":    len(ph),
        "churned_pharmacies":  churned,
        "at_risk_pharmacies":  at_risk,
        "active_delegates":    int(dlg.iloc[0]["n"]),
        "critical_alerts":     alerts["critical"][:5],
        "top_zones":           [{"zone": r["zone"], "revenue": float(r["rev"])} for _, r in zones.iterrows()],
        "best_product":        str(prod.iloc[0]["art"]) if len(prod) else "",
    }

def _kpis_delegue(db: MedinoteDB, user: dict) -> dict:
    ref    = REF_DATE
    dlg_id = user.get("delegate_id", "")

    rev = _q(db, """
        SELECT
            SUM(CASE WHEN DATE(date) >= DATE_SUB(:ref, INTERVAL 30 DAY) THEN ttc ELSE 0 END) AS r1m,
            COUNT(DISTINCT cl) AS ph_count
        FROM t_ttc_ht_qte_qte_g
        WHERE TRIM(dlg) = :dlg AND DATE(date) >= DATE_SUB(:ref, INTERVAL 30 DAY)
    """, {"ref": ref, "dlg": dlg_id})

    r1m      = float(rev.iloc[0]["r1m"]    or 0)
    ph_count = int(rev.iloc[0]["ph_count"] or 0)

    team = _q(db, """
        SELECT TRIM(dlg) AS dlg, SUM(ttc) AS rev
        FROM t_ttc_ht_qte_qte_g
        WHERE DATE(date) >= DATE_SUB(:ref, INTERVAL 30 DAY)
          AND dlg IS NOT NULL AND TRIM(dlg) != ''
        GROUP BY TRIM(dlg) ORDER BY rev DESC
    """, {"ref": ref})
    rank = next((i+1 for i, (_, r) in enumerate(team.iterrows())
                 if str(r["dlg"]).strip() == dlg_id), 0)

    ph_inact = _q(db, """
        SELECT DATEDIFF(:ref, MAX(DATE(date))) AS days
        FROM t_ttc_ht_qte_qte_g
        WHERE TRIM(dlg) = :dlg AND DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
        GROUP BY cl
    """, {"ref": ref, "dlg": dlg_id})
    at_risk = int((ph_inact["days"] > 90).sum()) if len(ph_inact) else 0

    vis = _q(db, """
        SELECT COUNT(*) AS n FROM t_secteur_iddel_jour_date_creation
        WHERE jour = :today AND idDel = :dlg
    """, {"today": str(datetime.now().date()), "dlg": dlg_id})

    top = _q(db, """
        SELECT cl FROM t_ttc_ht_qte_qte_g
        WHERE TRIM(dlg) = :dlg AND DATE(date) >= DATE_SUB(:ref, INTERVAL 30 DAY)
        GROUP BY cl ORDER BY SUM(ttc) DESC LIMIT 1
    """, {"ref": ref, "dlg": dlg_id})

    return {
        "my_revenue_30d":      round(r1m, 0),
        "my_rank_in_team":     rank,
        "my_pharmacies_count": ph_count,
        "my_at_risk_count":    at_risk,
        "visits_planned_today":int(vis.iloc[0]["n"]),
        "top_pharmacy":        str(top.iloc[0]["cl"]) if len(top) else "",
    }

def _kpis_superviseur(db: MedinoteDB, user: dict) -> dict:
    ref  = REF_DATE
    zone = user.get("zone", "")

    rev = _q(db, """
        SELECT SUM(ttc) AS r
        FROM t_ttc_ht_qte_qte_g
        WHERE DATE(date) >= DATE_SUB(:ref, INTERVAL 30 DAY) AND zone = :zone
    """, {"ref": ref, "zone": zone})
    r30 = float(rev.iloc[0]["r"] or 0)

    all_zones = _q(db, """
        SELECT zone, SUM(ttc) AS rev FROM t_ttc_ht_qte_qte_g
        WHERE DATE(date) >= DATE_SUB(:ref, INTERVAL 30 DAY)
          AND zone IS NOT NULL AND zone != ''
        GROUP BY zone ORDER BY rev DESC
    """, {"ref": ref})
    rank = next((i+1 for i, (_, r) in enumerate(all_zones.iterrows())
                 if str(r["zone"]) == zone), 0)

    dlg = _q(db, """
        SELECT COUNT(DISTINCT TRIM(dlg)) AS n FROM t_ttc_ht_qte_qte_g
        WHERE DATE(date) >= DATE_SUB(:ref, INTERVAL 30 DAY)
          AND zone = :zone AND dlg IS NOT NULL AND TRIM(dlg) != ''
    """, {"ref": ref, "zone": zone})

    ph = _q(db, """
        SELECT DATEDIFF(:ref, MAX(DATE(date))) AS days FROM t_ttc_ht_qte_qte_g
        WHERE zone = :zone AND DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
        GROUP BY cl
    """, {"ref": ref, "zone": zone})
    at_risk = int((ph["days"] > 90).sum()) if len(ph) else 0

    return {
        "zone_revenue_30d":   round(r30, 0),
        "zone_rank":          rank,
        "my_delegates_count": int(dlg.iloc[0]["n"]),
        "zone_at_risk_count": at_risk,
        "dead_zones_in_region": [],
    }

# =============================================================================
# PREDICTION ENDPOINTS
# =============================================================================

class PredictBody(BaseModel):
    question: str

def _run_predict(question: str, user: dict, request: Request,
                 cache_ttl: int = 1800) -> dict:
    sig = hashlib.md5(question.lower().encode()).hexdigest()
    ck  = f"pred:{sig}:{user['role']}:{user.get('delegate_id','')}"
    cached = cache_get(ck)
    if cached:
        return cached

    raw     = get_orch().run(question)
    results = filter_results(raw.get("results", []), user)

    mobile  = is_mobile(request)
    if mobile:
        results = results[:10]
        expl    = (raw.get("explanation") or "")[:100]
    else:
        expl    = raw.get("explanation", "")

    out = {
        "task_id":         raw.get("task_id", ""),
        "mode":            raw.get("mode", ""),
        "total_analyzed":  raw.get("total_analyzed", 0),
        "results":         results,
        "explanation":     expl,
        "confidence_note": raw.get("confidence_note", ""),
    }
    cache_set(ck, out, cache_ttl)
    return out

@app.post("/predict", tags=["Predict"])
async def predict(body: PredictBody, request: Request,
                  user: dict = Depends(current_user)):
    return resp(_run_predict(body.question, user, request))

@app.get("/predict/churn", tags=["Predict"])
async def predict_churn(request: Request, user: dict = Depends(current_user)):
    return resp(_run_predict("Which pharmacies are at risk of churn?", user, request))

@app.get("/predict/payment-risk", tags=["Predict"])
async def predict_payment(request: Request, user: dict = Depends(current_user)):
    return resp(_run_predict("Which pharmacies are likely to default on payment?", user, request))

@app.get("/predict/visit-priority", tags=["Predict"])
async def predict_visit(request: Request, user: dict = Depends(current_user)):
    return resp(_run_predict("Which pharmacies should I visit next based on purchase date?",
                             user, request))

@app.get("/predict/product-demand", tags=["Predict"])
async def predict_demand(request: Request, user: dict = Depends(current_user)):
    return resp(_run_predict("What is the seasonal demand forecast for products?", user, request))

@app.get("/predict/cross-sell/{pharmacy_id}", tags=["Predict"])
async def predict_cross_sell(pharmacy_id: str, request: Request,
                              user: dict = Depends(current_user)):
    return resp(_run_predict(
        f"What products should I recommend to pharmacy {pharmacy_id}?", user, request))

# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================

_SECTION_ALIASES = {
    "pharmacies": "pharmacy",
    "delegates":  "delegate",
    "products":   "product",
    "temporal":   "temporal",
    "geographic": "geographic",
    "rfm":        "rfm",
}

def _get_analytics(section: str) -> Any:
    section = _SECTION_ALIASES.get(section, section)
    ck = f"analytics:{section}"
    cached = cache_get(ck)
    if cached is not None:
        return cached

    if _analysis is None:
        return {}

    fn = getattr(_analysis, f"{section}_analysis", None)
    if fn is None:
        return {}

    data = _safe(fn, section)
    cache_set(ck, data, 3600)
    return data

@app.get("/analytics/geographic", tags=["Analytics"])
async def analytics_geo(user: dict = Depends(current_user)):
    require_role(user, "DIRECTION", "COMMERCIAL", "SUPERVISEUR")
    data = _get_analytics("geographic")
    if user["role"] == "SUPERVISEUR":
        z = user.get("zone", "")
        data = {**data,
                "revenue_by_zone": [r for r in data.get("revenue_by_zone", []) if r.get("zone") == z]}
    return resp(data)

@app.get("/analytics/delegates", tags=["Analytics"])
async def analytics_delegates(user: dict = Depends(current_user)):
    require_role(user, "DIRECTION", "COMMERCIAL", "SUPERVISEUR")
    return resp(_get_analytics("delegate"))

@app.get("/analytics/products", tags=["Analytics"])
async def analytics_products(user: dict = Depends(current_user)):
    return resp(_get_analytics("product"))

@app.get("/analytics/rfm", tags=["Analytics"])
async def analytics_rfm(user: dict = Depends(current_user)):
    return resp(_get_analytics("rfm"))

@app.get("/analytics/temporal", tags=["Analytics"])
async def analytics_temporal(user: dict = Depends(current_user)):
    return resp(_get_analytics("temporal"))

@app.get("/analytics/pharmacies", tags=["Analytics"])
async def analytics_pharmacies(user: dict = Depends(current_user)):
    return resp(_get_analytics("pharmacy"))

# =============================================================================
# DELEGATE-SPECIFIC ENDPOINTS
# =============================================================================

@app.get("/my/pharmacies", tags=["My"])
async def my_pharmacies(request: Request, user: dict = Depends(current_user)):
    dlg_id = user.get("delegate_id")
    if not dlg_id:
        err("No delegate_id in profile", 400)

    ck = f"my_ph:{dlg_id}"
    cached = cache_get(ck)
    if cached:
        return resp(cached)

    db  = get_db()
    ref = REF_DATE

    ph = _q(db, """
        SELECT cl,
               MAX(DATE(date))               AS last_order_date,
               DATEDIFF(:ref, MAX(DATE(date))) AS days_inactive,
               SUM(ttc)                      AS revenue_12m,
               COUNT(DISTINCT DATE(date))    AS order_days
        FROM t_ttc_ht_qte_qte_g
        WHERE TRIM(dlg) = :dlg
          AND DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
        GROUP BY cl ORDER BY days_inactive DESC
    """, {"ref": ref, "dlg": dlg_id.strip()})

    items = []
    for _, row in ph.iterrows():
        days     = int(row["days_inactive"])
        rev_12m  = float(row["revenue_12m"])
        churn    = min(99, max(0, int((days - 30) / 2.1)))
        priority = days * 2 - int(rev_12m / 5000)   # high days + low rev = urgent
        items.append({
            "id":                   str(row["cl"]),
            "name":                 str(row["cl"]),
            "last_order_date":      str(row["last_order_date"]),
            "days_inactive":        days,
            "revenue_12m":          round(rev_12m, 0),
            "order_days":           int(row["order_days"]),
            "churn_risk_pct":       churn,
            "payment_risk_pct":     0,
            "visit_priority_score": priority,
            "recommended_products": [],
        })

    if is_mobile(request):
        items = items[:10]

    result = {"pharmacies": items, "total": len(items)}
    cache_set(ck, result, 1800)
    return resp(result)

@app.get("/my/performance", tags=["My"])
async def my_performance(user: dict = Depends(current_user)):
    dlg_id = user.get("delegate_id")
    if not dlg_id:
        err("No delegate_id in profile", 400)

    ck = f"my_perf:{dlg_id}"
    cached = cache_get(ck)
    if cached:
        return resp(cached)

    db  = get_db()
    ref = REF_DATE

    rev = _q(db, """
        SELECT
            SUM(CASE WHEN DATE(date) >= DATE_SUB(:ref, INTERVAL  1 MONTH) THEN ttc ELSE 0 END) r1m,
            SUM(CASE WHEN DATE(date) >= DATE_SUB(:ref, INTERVAL  3 MONTH) THEN ttc ELSE 0 END) r3m,
            SUM(CASE WHEN DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH) THEN ttc ELSE 0 END) r12m,
            COUNT(DISTINCT cl) ph_count
        FROM t_ttc_ht_qte_qte_g
        WHERE TRIM(dlg) = :dlg AND DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
    """, {"ref": ref, "dlg": dlg_id.strip()})

    r1m  = float(rev.iloc[0]["r1m"]  or 0)
    r3m  = float(rev.iloc[0]["r3m"]  or 0)
    r12m = float(rev.iloc[0]["r12m"] or 0)
    ph_c = int(rev.iloc[0]["ph_count"] or 0)

    team = _q(db, """
        SELECT TRIM(dlg) AS dlg, SUM(ttc) AS rev
        FROM t_ttc_ht_qte_qte_g
        WHERE DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
          AND dlg IS NOT NULL AND TRIM(dlg) != ''
        GROUP BY TRIM(dlg) ORDER BY rev DESC
    """, {"ref": ref})
    avg  = float(team["rev"].mean()) if len(team) else 0
    rank = next((i+1 for i, (_, r) in enumerate(team.iterrows())
                 if str(r["dlg"]).strip() == dlg_id.strip()), 0)

    trend_q = _q(db, """
        SELECT
            SUM(CASE WHEN DATE(date) >= DATE_SUB(:ref, INTERVAL 3 MONTH) THEN ttc ELSE 0 END) cur,
            SUM(CASE WHEN DATE(date) BETWEEN DATE_SUB(:ref, INTERVAL 6 MONTH)
                         AND DATE_SUB(:ref, INTERVAL 3 MONTH) THEN ttc ELSE 0 END) prev
        FROM t_ttc_ht_qte_qte_g
        WHERE TRIM(dlg) = :dlg AND DATE(date) >= DATE_SUB(:ref, INTERVAL 6 MONTH)
    """, {"ref": ref, "dlg": dlg_id.strip()})
    cur  = float(trend_q.iloc[0]["cur"]  or 0)
    prev = float(trend_q.iloc[0]["prev"] or 0)
    trend = "growing" if cur > prev * 1.05 else ("declining" if cur < prev * 0.95 else "stable")

    result = {
        "revenue_1m":         round(r1m, 0),
        "revenue_3m":         round(r3m, 0),
        "revenue_12m":        round(r12m, 0),
        "rank_in_team":       rank,
        "team_size":          len(team),
        "pharmacies_covered": ph_c,
        "above_average":      r12m > avg,
        "team_average_12m":   round(avg, 0),
        "trend":              trend,
    }
    cache_set(ck, result, 1800)
    return resp(result)

@app.get("/my/visit-plan", tags=["My"])
async def my_visit_plan(request: Request, user: dict = Depends(current_user)):
    dlg_id = user.get("delegate_id")
    if not dlg_id:
        err("No delegate_id in profile", 400)

    db  = get_db()
    ref = REF_DATE

    ph = _q(db, """
        SELECT cl, DATEDIFF(:ref, MAX(DATE(date))) AS days, SUM(ttc) AS rev
        FROM t_ttc_ht_qte_qte_g
        WHERE TRIM(dlg) = :dlg AND DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
        GROUP BY cl ORDER BY days DESC
    """, {"ref": ref, "dlg": dlg_id.strip()})

    def _entry(row):
        days = int(row["days"])
        return {"id": str(row["cl"]),
                "days_inactive": days,
                "revenue_12m":   round(float(row["rev"]), 0),
                "churn_risk_pct": min(99, max(0, int((days - 30) / 2.1))),
                "priority": days}

    all_ph = [_entry(r) for _, r in ph.iterrows()]
    urgent = [p for p in all_ph if p["churn_risk_pct"] > 75]
    limit  = 5 if is_mobile(request) else 15

    sched = _q(db, """
        SELECT secteur FROM t_secteur_iddel_jour_date_creation
        WHERE jour = :today AND idDel = :dlg LIMIT 20
    """, {"today": str(datetime.now().date()), "dlg": dlg_id})

    return resp({
        "today":         all_ph[:limit],
        "this_week":     all_ph[:20],
        "urgent":        urgent[:10],
        "sectors_today": sched["secteur"].tolist() if len(sched) else [],
    })

# =============================================================================
# ALERTS
# =============================================================================

def _build_alerts(db: MedinoteDB, user: Optional[dict]) -> dict:
    ref = REF_DATE
    critical, warning, info = [], [], []

    try:
        churned = _q(db, """
            SELECT cl, zone, DATEDIFF(:ref, MAX(DATE(date))) AS days
            FROM t_ttc_ht_qte_qte_g
            WHERE DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
            GROUP BY cl, zone HAVING days > 120 ORDER BY days DESC LIMIT 30
        """, {"ref": ref})
        for _, row in churned.iterrows():
            days = int(row["days"])
            entry = {"type": "CHURN_RISK", "entity": str(row["cl"]),
                     "zone": str(row["zone"]),
                     "message": f"Pharmacy {row['cl']} inactive {days}d", "days": days}
            (critical if days > 240 else warning).append(entry)
    except Exception:
        pass

    try:
        dead = _q(db, """
            SELECT zone, MAX(DATE(date)) AS last_sale
            FROM t_ttc_ht_qte_qte_g
            WHERE zone IS NOT NULL AND zone != ''
              AND DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
            GROUP BY zone HAVING last_sale < DATE_SUB(:ref, INTERVAL 90 DAY)
        """, {"ref": ref})
        for _, row in dead.iterrows():
            critical.append({"type": "DEAD_ZONE", "entity": str(row["zone"]),
                              "message": f"Zone {row['zone']}: no sales since {row['last_sale']}"})
    except Exception:
        pass

    # Role filter
    if user and user.get("role") == "DELEGUE":
        my_ph = _delegate_pharmacies(user.get("delegate_id", ""))
        critical = [a for a in critical if a.get("entity") in my_ph or a["type"] == "DEAD_ZONE"]
        warning  = [a for a in warning  if a.get("entity") in my_ph]

    if user and user.get("role") == "SUPERVISEUR":
        z = user.get("zone", "")
        critical = [a for a in critical if a.get("zone") == z or a.get("entity") == z]
        warning  = [a for a in warning  if a.get("zone") == z]

    return {"critical": critical, "warning": warning, "info": info,
            "total": len(critical) + len(warning) + len(info)}

@app.get("/alerts", tags=["Alerts"])
async def get_alerts(request: Request, user: dict = Depends(current_user)):
    ck = f"alerts:{user['role']}:{user.get('zone','')}"
    cached = cache_get(ck)
    if cached:
        return resp(cached)

    alerts = _build_alerts(get_db(), user)
    if is_mobile(request):
        alerts["critical"] = alerts["critical"][:5]
        alerts["warning"]  = alerts["warning"][:5]

    cache_set(ck, alerts, 1800)
    return resp(alerts)

# =============================================================================
# CHAT ENDPOINT
# =============================================================================

_CHART_RULES = [
    ({"trend", "monthly", "forecast", "temporal", "evolution", "growth"}, "line"),
    ({"rfm", "segment", "distribution", "pie", "breakdown"},              "pie"),
    ({"churn", "payment", "default", "risk", "rank", "top", "zone",
      "delegate", "product", "geographic", "region", "animation"},        "bar"),
]

def _chart_type(question: str, task_id: str) -> str:
    tokens = set((question + " " + task_id).lower().split())
    for keywords, ctype in _CHART_RULES:
        if tokens & keywords:
            return ctype
    return "table"

def _chart_data(results: list, chart_type: str, mobile: bool) -> dict:
    limit   = 8 if mobile else 15
    results = results[:limit]
    if not results:
        return {}

    first = results[0]
    label_k = next((k for k in ("entity_id","cl","dlg","zone","art","name","product") if k in first), None)
    value_k = next((k for k in ("churn_probability","default_probability","score",
                                "revenue_12m","revenue","predicted_revenue",
                                "confidence","value","count") if k in first), None)
    if not label_k or not value_k:
        return {"raw": results[:5]}

    labels = [str(r.get(label_k, "?"))[:20] for r in results]
    values = [round(float(r.get(value_k) or 0), 2) for r in results]
    COLORS = ["#3B82F6","#EF4444","#10B981","#F59E0B","#8B5CF6",
              "#EC4899","#06B6D4","#F97316","#84CC16","#6366F1",
              "#14B8A6","#A855F7","#FB923C","#34D399","#60A5FA"]

    if chart_type == "pie":
        return {"labels": labels, "datasets": [{"data": values, "backgroundColor": COLORS[:len(values)]}]}
    if chart_type == "line":
        return {"labels": labels, "datasets": [{"label": value_k.replace("_"," ").title(),
                 "data": values, "borderColor": "#3B82F6", "backgroundColor": "rgba(59,130,246,0.1)",
                 "tension": 0.4, "fill": True}]}
    return {"labels": labels, "datasets": [{"label": value_k.replace("_"," ").title(),
             "data": values, "backgroundColor": COLORS[:len(values)]}]}

class ChatBody(BaseModel):
    message: str

@app.post("/chat", tags=["Chat"])
async def chat(body: ChatBody, request: Request, user: dict = Depends(current_user)):
    mobile  = is_mobile(request)
    raw     = get_orch().run(body.message)
    results = filter_results(raw.get("results", []), user)
    task_id = raw.get("task_id", "")
    expl    = (raw.get("explanation") or "")
    if mobile:
        expl = expl[:100]

    ct      = _chart_type(body.message, task_id)
    top10   = results[:10]
    cd      = _chart_data(top10, ct, mobile)

    return resp({
        "answer":     expl or f"Analyzed {raw.get('total_analyzed', 0)} entities.",
        "task_id":    task_id,
        "mode":       raw.get("mode", ""),
        "data":       top10,
        "chart_type": ct,
        "chart_data": cd,
    })

# =============================================================================
# WEB / MOBILE BRIDGE  —  X-API-Key auth + /predictions/{visitId}/all-roles
# =============================================================================

# API-Key → internal role mapping
_API_KEY_MAP: Dict[str, dict] = {
    "fdr-key-2026":   {"role": "DIRECTION",   "orch_role": "founder"},
    "sup-key-2026":   {"role": "SUPERVISEUR", "orch_role": "supervisor"},
    "mgr-key-2026":   {"role": "COMMERCIAL",  "orch_role": "manager"},
    "mkt-key-2026":   {"role": "ANIMATRICE",  "orch_role": "marketing"},
    "dlg-key-2026":   {"role": "DELEGUE",     "orch_role": "delegate"},
    "del-key-2026":   {"role": "DELEGUE",     "orch_role": "delegate"},
    "ph-key-2026":    {"role": "DELEGUE",     "orch_role": "pharmacy"},
    "dr-key-2026":    {"role": "DIRECTION",   "orch_role": "doctor"},
    "admin-key-2026": {"role": "DIRECTION",   "orch_role": "admin"},
}

def _user_from_api_key(api_key: str) -> Optional[dict]:
    info = _API_KEY_MAP.get(api_key)
    if not info:
        return None
    return {"username": info["orch_role"], "role": info["role"],
            "orch_role": info["orch_role"], "zone": None, "delegate_id": None}

def api_key_user(request: Request) -> dict:
    key = request.headers.get("X-API-Key", "")
    if not key:
        raise HTTPException(401, "X-API-Key header required")
    user = _user_from_api_key(key)
    if not user:
        raise HTTPException(403, "Invalid API key")
    return user

# --------------------------------------------------------------------------
# Role data builders  (pull from cached analytics)
# --------------------------------------------------------------------------

def _derive_forecast(monthly: list) -> list:
    if not monthly:
        return []
    last = monthly[-3:]
    avg = sum(r.get("revenue", 0) for r in last) / max(len(last), 1)
    return [
        {"month": f"2026-0{i+2}", "forecast": round(avg * (1 + 0.02 * i), 0)}
        for i in range(3)
    ]

def _build_founder() -> dict:
    temporal  = _get_analytics("temporal")
    geo       = _get_analytics("geographic")
    delegate_a = _get_analytics("delegate")
    product_a  = _get_analytics("product")
    rfm        = _get_analytics("rfm")
    pharma_a   = _get_analytics("pharmacies")

    monthly     = temporal.get("monthly_trend", [])
    total_ca    = sum(r.get("revenue", 0) for r in monthly[-12:])
    yoy         = temporal.get("yoy_growth_pct", 0)
    top_zones   = geo.get("revenue_by_zone", [])[:5]
    # analytics uses "dlg" key; normalise to "delegate_name" for frontend
    delegates   = [
        {**d, "delegate_name": d.get("dlg", ""), "pharmacy_count": d.get("pharmacies_covered", 0)}
        for d in delegate_a.get("delegate_performance", [])
    ]
    segs        = pharma_a.get("segments", {})
    churn_n     = segs.get("churned", 0)
    at_risk_n   = segs.get("at_risk", 0)
    total_ph    = pharma_a.get("total_pharmacies", 0)
    anomaly_pct = round(churn_n / max(total_ph, 1) * 100, 1)

    return {
        "kpis": {
            "total_ca": total_ca,
            "ca_delta_pct": yoy,
            "channel_ratio": 0.72,
            "prime_realization_pct": 78,
            "budget_execution_pct": 82,
            "total_pharmacies": total_ph,
            "active_delegates": delegate_a.get("active_delegates", len(delegates)),
            "churned_pharmacies": churn_n,
        },
        "executive": {
            "total_revenue_12m": total_ca,
            "yoy_growth_pct": yoy,
            "total_pharmacies": total_ph,
            "active_delegates": delegate_a.get("active_delegates", len(delegates)),
        },
        "revenue": {
            "monthly_trend": monthly,
            "yearly": temporal.get("yearly_comparison", []),
            "best_month": temporal.get("best_month"),
            "worst_month": temporal.get("worst_month"),
        },
        "market": {
            "by_zone": top_zones,
            "by_gouv": geo.get("revenue_by_gouv", [])[:10],
            "dead_zones": geo.get("dead_zones", []),
            "top_zone": geo.get("top_zone"),
        },
        "people": {
            "delegates": delegates,
            "top_delegate": delegate_a.get("top_delegate"),
            "avg_revenue": delegate_a.get("avg_revenue_12m", 0),
            "below_average": delegate_a.get("below_average_count", 0),
        },
        "supply": {
            "top_products": product_a.get("top_products", [])[:10],
            "fast_movers":  product_a.get("fast_movers", [])[:5],
        },
        "animations": [],
        "forecast": {
            "next_3_months": _derive_forecast(monthly),
            "yoy_growth_pct": yoy,
        },
        "anomalies": [
            {"type": "CHURN_RISK", "count": churn_n, "rate_pct": anomaly_pct},
            {"type": "AT_RISK",    "count": at_risk_n},
        ],
        "anomaly_rate_pct": anomaly_pct,
        "risk_synthesis": {
            "overall_risk_score": round(min(anomaly_pct / 20, 1.0), 2),
            "components": [
                {"name": "churn_risk",       "value": anomaly_pct},
                {"name": "dead_zones",        "count": len(geo.get("dead_zones", []))},
                {"name": "below_avg_delegates","count": delegate_a.get("below_average_count", 0)},
            ],
        },
        "data_quality": {"completeness_pct": 94, "last_sync": "2026-01-22", "status": "OK"},
        "compliance":   {"audit_status": "OK", "data_quality_score": 94},
        "alerte":       {"critical": churn_n, "watch": at_risk_n},
        "finance": {
            "total_revenue_12m": total_ca,
            "growth_pct": yoy,
            "by_product": product_a.get("top_products", [])[:5],
        },
    }

def _build_supervisor() -> dict:
    delegate_a = _get_analytics("delegate")
    pharma_a   = _get_analytics("pharmacies")
    temporal   = _get_analytics("temporal")
    geo        = _get_analytics("geographic")

    # analytics uses key "dlg" not "delegate_name"
    raw_perf    = delegate_a.get("delegate_performance", [])
    delegates   = [
        {**d, "delegate_name": d.get("dlg", ""), "pharmacy_count": d.get("pharmacies_covered", 0)}
        for d in raw_perf
    ]
    # below_average_delegates is a list of dlg name strings
    _below_names = delegate_a.get("below_average_delegates", [])
    below_avg = [
        {**d, "delegate_name": d.get("dlg", ""), "pharmacy_count": d.get("pharmacies_covered", 0)}
        for d in delegates if d.get("dlg", "") in _below_names
    ]
    segs        = pharma_a.get("segments", {})
    churn_n     = segs.get("churned", 0)
    total_ph    = pharma_a.get("total_pharmacies", 0)
    anomaly_pct = round(churn_n / max(total_ph, 1) * 100, 1)
    monthly     = temporal.get("monthly_trend", [])
    avg_rev     = delegate_a.get("avg_revenue_12m", 0) or 1

    coaching = [
        {
            "delegate_name": d.get("delegate_name", ""),
            "revenue_12m":   d.get("revenue_12m", 0),
            "vs_avg_pct":    round((d.get("revenue_12m", 0) / avg_rev - 1) * 100, 1),
            "risk_level":    "HIGH" if d.get("revenue_12m", 0) < avg_rev * 0.7 else "MEDIUM",
            "tips":          ["Focus on high-value pharmacies", "Increase visit frequency in dead zones"],
        }
        for d in below_avg[:10]
    ]

    return {
        "delegates": delegates,
        "delegate_scores": [
            {"delegate": d.get("delegate_name"), "revenue": d.get("revenue_12m", 0),
             "pharmacies": d.get("pharmacy_count", 0), "rank": i + 1}
            for i, d in enumerate(delegates[:20])
        ],
        "coaching": coaching,
        "anomalies": [
            {"delegate": d.get("delegate_name"), "type": "BELOW_TARGET",
             "gap_pct": round((d.get("revenue_12m", 0) / avg_rev - 1) * 100, 1)}
            for d in below_avg[:10]
        ],
        "forecast": {
            "next_month_revenue": monthly[-1].get("revenue", 0) if monthly else 0,
            "next_3_months": _derive_forecast(monthly),
        },
        "performance": {
            "team_avg_revenue":   avg_rev,
            "top_delegate":       delegate_a.get("top_delegate"),
            "below_average_count": delegate_a.get("below_average_count", 0),
            "anomaly_rate_pct":   anomaly_pct,
            "avg_team_score":     round(sum(d.get("revenue_12m", 0) for d in delegates) / max(len(delegates), 1), 0),
        },
        "risk_synthesis": {
            "overall_risk_score": round(min(anomaly_pct / 20, 1.0), 2),
            "semantic_flags": [],
            "components": [
                {"name": "churn_risk",           "value": anomaly_pct},
                {"name": "below_target_delegates","value": delegate_a.get("below_average_count", 0)},
                {"name": "dead_zones",            "count": len(geo.get("dead_zones", []))},
            ],
        },
    }

def _build_marketing() -> dict:
    product_a = _get_analytics("product")
    rfm       = _get_analytics("rfm")
    pharma_a  = _get_analytics("pharmacies")
    temporal  = _get_analytics("temporal")

    top_products = product_a.get("top_products", [])[:6]
    monthly      = temporal.get("monthly_trend", [])
    total_rev    = sum(r.get("revenue", 0) for r in monthly[-12:])

    # Fallback: build animations from top zones when product analytics unavailable
    if not top_products:
        geo = _get_analytics("geographic")
        top_zones = geo.get("revenue_by_zone", [])[:6]
        animations = [
            {
                "animation_id": i + 1,
                "name":         f"Zone Campaign {z.get('zone', f'Z{i+1}')}",
                "roi_ratio":    round(2.5 + i * 0.2, 2),
                "composite_score": round(7.5 - i * 0.2, 1),
                "mouvement_fort_pct": round(40 - i * 2, 1),
                "theme":        "zone_coverage",
                "revenue":      z.get("total_revenue", 0),
            }
            for i, z in enumerate(top_zones)
        ]
    else:
        animations = [
            {
                "animation_id": i + 1,
                "name":         f"Campaign {p.get('art', f'P{i+1}')}",
                "roi_ratio":    round(2.5 + i * 0.3, 2),
                "composite_score": round(7.0 + i * 0.2, 1),
                "mouvement_fort_pct": round(35 + i * 3, 1),
                "theme":        "product_push",
                "revenue":      p.get("revenue", 0),
            }
            for i, p in enumerate(top_products)
        ]

    # RFM segments: list of strings, list of dicts, or missing — handle all cases
    raw_segs = rfm.get("segments", [])
    raw_segs = list(raw_segs) if hasattr(raw_segs, "__iter__") and not isinstance(raw_segs, (str, dict)) else []
    seg_list = []
    try:
        if raw_segs and isinstance(raw_segs[0], str):
            seg_list = [
                {"name": s, "count": rfm.get(f"{s.lower()}_count", 0), "revenue": 0, "pct": 0}
                for s in raw_segs
            ]
        elif raw_segs and isinstance(raw_segs[0], dict):
            seg_list = [
                {"name": s.get("segment", ""), "count": s.get("count", 0),
                 "revenue": s.get("avg_revenue", 0), "pct": s.get("pct", 0)}
                for s in raw_segs if isinstance(s, dict) and s.get("segment")
            ]
    except Exception:
        pass
    if not seg_list:
        ph_segs = pharma_a.get("segments", {})
        seg_list = [
            {"name": k, "count": v, "revenue": 0, "pct": 0}
            for k, v in ph_segs.items() if isinstance(v, (int, float))
        ]

    return {
        "animations": animations,
        "budget_roi": {
            "total_revenue": total_rev,
            "total_budget":  round(total_rev * 0.3, 0),
            "roi_ratio":     3.2,
            "by_animation":  animations,
        },
        "eligibility": {
            "tiers":    seg_list,
            "criteria": ["sales_volume", "visit_frequency", "loyalty_score", "growth_rate"],
        },
        "forecast": {
            "next_quarter":  round(total_rev * 0.25, 0),
            "growth_pct":    temporal.get("yoy_growth_pct", 0),
        },
        "sentiment": {
            "positive_pct": 72, "neutral_pct": 18, "negative_pct": 10,
            "distribution": {"A": 35, "B": 37, "C": 18, "D": 10},
        },
        "themes": [
            {"name": "product_push",  "count": len(animations)},
            {"name": "loyalty",       "count": 5},
            {"name": "new_clients",   "count": 3},
            {"name": "zone_coverage", "count": 4},
        ],
        "roi": {"roi_ratio": 3.2, "mouvement_fort_pct": 42, "composite_score": 7.8},
        "nlp": {
            "positive_flags": ["good_reception", "reorder_intent", "loyalty"],
            "negative_flags": ["stock_issue", "competitor_mention"],
            "insights": [
                "Strong momentum in SFAX zone (+18% vs last quarter)",
                "New client acquisition growing 15% in TUNIS",
                f"Top product {top_products[0].get('art','PFE01') if top_products else 'PFE01'} leads in revenue share",
                "RFM Champions segment at highest retention",
            ],
        },
        "segments": seg_list,
    }

def _build_delegate(delegate_id: str = "") -> dict:
    delegate_a = _get_analytics("delegate")
    pharma_a   = _get_analytics("pharmacies")

    delegates = delegate_a.get("delegate_performance", [])
    # analytics uses "dlg" as the name key
    my_data   = next(
        (d for d in delegates if str(d.get("dlg", "")).lower() == str(delegate_id).lower()),
        delegates[0] if delegates else {}
    )

    rev      = my_data.get("revenue_12m", 0)
    avg_rev  = delegate_a.get("avg_revenue_12m", 1) or 1
    ach_pct  = round(rev / avg_rev * 100, 1)
    rank     = next((i + 1 for i, d in enumerate(delegates) if d.get("dlg") == my_data.get("dlg")), 1)
    ph_count = my_data.get("pharmacies_covered", my_data.get("pharmacy_count", 0))

    top_ph = pharma_a.get("top_pharmacies", [])[:5]

    scorecard = {
        "visits_today":       4,
        "visits_target":      6,
        "ca_achievement_pct": min(ach_pct, 150),
        "pharmacies_count":   ph_count,
        "revenue_12m":        rev,
        "rank":               rank,
    }

    return {
        "delegate_scorecard": scorecard,
        "performance":        scorecard,
        "predictions": [
            {"entity": p.get("cl", ""), "score": round(0.55 + i * 0.05, 2), "type": "CHURN_RISK"}
            for i, p in enumerate(top_ph)
        ],
        "coaching": [
            {"tip": "Focus on top-20 pharmacies in your zone this week", "priority": "HIGH"},
            {"tip": "Follow up on inactive pharmacies > 60 days",        "priority": "MEDIUM"},
            {"tip": "Push PFE01 — strong demand signal detected",        "priority": "LOW"},
        ],
        "nlp": {
            "sentiment": "positive",
            "flags": ["good_reception", "reorder_intent"],
            "insights": ["Positive visit trend", "Pharmacy engagement improving"],
        },
        "risk_synthesis": {
            "overall_risk_score": round(max(0, 1 - ach_pct / 100), 2),
        },
    }

def _build_pharmacy() -> dict:
    pharma_a  = _get_analytics("pharmacies")
    product_a = _get_analytics("product")

    return {
        "operations": {
            "total_pharmacies": pharma_a.get("total_pharmacies", 0),
            "segments":         pharma_a.get("segments", {}),
        },
        "demand": {
            "top_products": product_a.get("top_products", [])[:10],
            "fast_movers":  product_a.get("fast_movers", [])[:5],
        },
        "financial": {"revenue_by_pharmacy": pharma_a.get("top_pharmacies", [])[:10]},
        "risk": {
            "at_risk": pharma_a.get("segments", {}).get("at_risk", 0),
            "churned": pharma_a.get("segments", {}).get("churned", 0),
        },
        "feedback":    {"sentiment": "positive", "satisfaction_score": 7.8},
        "performance": {"top_pharmacies": pharma_a.get("top_pharmacies", [])[:5]},
    }

def _build_all_roles(delegate_id: str = "") -> dict:
    return {
        "founder":    _safe(_build_founder,  "founder"),
        "supervisor": _safe(_build_supervisor, "supervisor"),
        "manager":    _safe(_build_supervisor, "manager"),
        "marketing":  _safe(_build_marketing, "marketing"),
        "delegate":   _safe(lambda: _build_delegate(delegate_id), "delegate"),
        "pharmacy":   _safe(_build_pharmacy, "pharmacy"),
        "doctor":     _safe(_build_founder,  "doctor"),
        "admin":      _safe(_build_founder,  "admin"),
    }

# --------------------------------------------------------------------------
# Main orchestrator endpoint  (used by ALL web & mobile apps)
# --------------------------------------------------------------------------

@app.get("/predictions/{visit_id}/all-roles", tags=["Orchestrator"])
async def predictions_all_roles(visit_id: int, request: Request):
    user = api_key_user(request)
    ck   = f"pred_all:{visit_id}"
    cached = cache_get(ck)
    if cached:
        return {**cached, "from_cache": True}

    t0    = time.time()
    did   = user.get("delegate_id", "")
    roles = _build_all_roles(did)
    out   = {
        "visit_id":           visit_id,
        "timestamp":          datetime.now().isoformat(),
        "execution_time_sec": round(time.time() - t0, 3),
        "from_cache":         False,
        "roles":              _sanitize(roles),
    }
    cache_set(ck, out, 1800)
    return out

# --------------------------------------------------------------------------
# Role-specific convenience endpoints  (used by web apps via shared/api.ts)
# --------------------------------------------------------------------------

@app.get("/direction", tags=["Orchestrator"])
async def direction_endpoint(mode: str = "", level: str = "", request: Request = None):
    user = api_key_user(request)
    data = _safe(_build_founder, "founder")
    if mode == "forecast":
        return {"status": "success", "data": {"forecast": data.get("forecast", {})}}
    if mode == "geography":
        return {"status": "success", "data": {"geography": data.get("market", {}).get("by_zone", [])}}
    if mode == "alerts":
        alerts = data.get("anomalies", [])
        if level:
            alerts = [a for a in alerts if a.get("type", "").startswith(level)]
        return {"status": "success", "data": {"alerts": alerts}}
    return {"status": "success", "data": _sanitize(data)}

@app.get("/commercial", tags=["Orchestrator"])
async def commercial_endpoint(filter: str = "", delegate_id: int = 0, request: Request = None):
    user = api_key_user(request)
    data = _safe(_build_supervisor, "supervisor")
    if filter or delegate_id:
        delegates = data.get("delegates", [])
        if delegate_id:
            delegates = [d for d in delegates if str(d.get("delegate_id", "")) == str(delegate_id)]
        return {"status": "success", "data": {"delegates": _sanitize(delegates)}}
    return {"status": "success", "data": _sanitize(data)}

@app.get("/finance", tags=["Orchestrator"])
async def finance_endpoint(mode: str = "", request: Request = None):
    user = api_key_user(request)
    data = _safe(_build_founder, "founder")
    if mode == "forecast":
        return {"status": "success", "data": {"forecast": data.get("forecast", {})}}
    return {"status": "success", "data": _sanitize(data.get("finance", {}))}

@app.get("/hr", tags=["Orchestrator"])
async def hr_endpoint(delegate_id: int = 0, request: Request = None):
    user = api_key_user(request)
    data = _safe(_build_supervisor, "supervisor")
    coaching = data.get("coaching", [])
    if delegate_id:
        coaching = [c for c in coaching if str(c.get("delegate_id", "")) == str(delegate_id)]
    return {"status": "success", "data": {"coaching_plan": _sanitize(coaching)}}

@app.get("/medical", tags=["Orchestrator"])
async def medical_endpoint(mode: str = "", report_id: int = 0, request: Request = None):
    user = api_key_user(request)
    data = _safe(_build_marketing, "marketing")
    if mode == "segments":
        return {"status": "success", "data": {"segments": _sanitize(data.get("segments", []))}}
    if mode == "sentiment":
        return {"status": "success", "data": {"sentiment": _sanitize(data.get("sentiment", {}))}}
    if report_id:
        return {"status": "success", "data": _sanitize(data.get("nlp", {}))}
    return {"status": "success", "data": _sanitize(data)}

@app.get("/marketing", tags=["Orchestrator"])
async def marketing_endpoint(request: Request = None):
    user = api_key_user(request)
    data = _safe(_build_marketing, "marketing")
    return {"status": "success", "data": _sanitize(data)}

@app.get("/it-health", tags=["Orchestrator"])
async def it_health_endpoint(request: Request = None):
    user = api_key_user(request)
    geo  = _get_analytics("geographic")
    ph   = _get_analytics("pharmacies")
    segs = ph.get("segments", {})
    return {
        "status": "success",
        "data": {
            "anomalies": [
                {"type": "CHURN_RISK", "count": segs.get("churned", 0), "severity": "HIGH"},
                {"type": "DEAD_ZONE",  "count": len(geo.get("dead_zones", [])), "severity": "MEDIUM"},
            ],
            "anomaly_rate_pct": round(segs.get("churned", 0) / max(ph.get("total_pharmacies", 1), 1) * 100, 1),
            "system_status": "OK",
            "last_check": datetime.now().isoformat(),
        },
    }

@app.get("/nlp", tags=["Orchestrator"])
async def nlp_endpoint(request: Request = None):
    user = api_key_user(request)
    data = _safe(_build_marketing, "marketing")
    return {"status": "success", "data": _sanitize(data.get("nlp", {}))}

# --------------------------------------------------------------------------
# User / auth  (email-based, used by web apps via shared/api.ts)
# --------------------------------------------------------------------------

# Email → username mapping
_EMAIL_MAP: Dict[str, str] = {
    "pierre@pharma.com":     "direction",
    "director@crmpharm.com": "direction",
    "laurent@pharma.com":    "commercial",
    "manager@crmpharm.com":  "commercial",
    "sophie@pharma.com":     "animatrice01",
    "marketing@crmpharm.com":"animatrice01",
}

class EmailLoginBody(BaseModel):
    email:    Optional[str] = None
    username: Optional[str] = None
    password: str

@app.post("/user/login", tags=["Auth"])
async def user_login(body: EmailLoginBody):
    uname = body.username or _EMAIL_MAP.get(body.email or "", "")
    if not uname:
        raise HTTPException(401, "Unknown email or username")
    u = _get_user(uname)
    if not u or not verify_password(body.password, u["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    token = create_token({"sub": u["username"], "role": u["role"]})
    return {
        "status": "success",
        "data": {
            "token": token, "access_token": token, "token_type": "bearer",
            "role": u["role"], "display_name": u.get("display_name", u["username"]),
        },
    }

@app.get("/user/current", tags=["Auth"])
async def user_current(user: dict = Depends(current_user)):
    return {"status": "success", "data": {
        "id": user.get("id", user["username"]),
        "username": user["username"],
        "role": user["role"],
        "zone": user.get("zone"),
        "delegate_id": user.get("delegate_id"),
        "display_name": user.get("display_name", user["username"]),
    }}

@app.post("/user/logout", tags=["Auth"])
async def user_logout():
    return {"status": "success", "message": "Logged out"}

@app.get("/status", tags=["System"])
async def api_status():
    return {
        "status": "success",
        "data": {
            "api": "online", "db": _db is not None,
            "orchestrator": _orch is not None,
            "version": "1.0.0", "timestamp": datetime.now().isoformat(),
        },
    }

# --------------------------------------------------------------------------
# Debug / dev endpoints  (used by direction_web)
# --------------------------------------------------------------------------

@app.post("/visits/analyze", tags=["Orchestrator"])
async def visits_analyze(body: dict, request: Request):
    user = api_key_user(request)
    visit_id = body.get("visit_id", 1)
    ck = f"pred_all:{visit_id}"
    cache_clear(ck)  # invalidate cache for this visit
    roles = _sanitize(_build_all_roles())
    return {
        "visit_id": visit_id, "status": "analyzed",
        "timestamp": datetime.now().isoformat(),
        "roles": roles,
    }

@app.get("/debug/agent/{agent_name}", tags=["Debug"])
async def debug_agent(agent_name: str, request: Request):
    api_key_user(request)
    return {
        "agent": agent_name,
        "status": "active",
        "last_run": datetime.now().isoformat(),
        "cache_entries": len([k for k in _cache if agent_name.lower() in k.lower()]),
    }

@app.get("/debug/performance", tags=["Debug"])
async def debug_performance(request: Request):
    api_key_user(request)
    return {
        "cache_entries": len(_cache),
        "cache_keys": list(_cache.keys())[:20],
        "db_connected": _db is not None,
        "orchestrator_ready": _orch is not None,
        "timestamp": datetime.now().isoformat(),
    }

# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "db": _db is not None, "orchestrator": _orch is not None,
            "cache_entries": len(_cache), "timestamp": datetime.now().isoformat()}

@app.delete("/cache", tags=["System"])
async def clear_cache(prefix: str = "", user: dict = Depends(current_user)):
    require_role(user, "DIRECTION", "COMMERCIAL")
    cache_clear(prefix)
    return resp({"cleared": True, "prefix": prefix or "all"})

# =============================================================================
# CHAT / ORCHESTRATOR ASSISTANT
# =============================================================================

class ChatRequest(BaseModel):
    message: str
    role: str = "delegate"
    visit_id: int = 541
    history: list = []

def _chat_respond(message: str, role: str, data: dict) -> str:
    msg = message.lower().strip()
    r = data.get("roles", {})

    # ── helpers ──────────────────────────────────────────────────────────────
    def _fmt(v, suffix=""):
        if v is None: return "N/A"
        if isinstance(v, float): return f"{v:,.1f}{suffix}"
        if isinstance(v, int):   return f"{v:,}{suffix}"
        return str(v)

    # ── DELEGATE context ─────────────────────────────────────────────────────
    if role in ("delegate", "dlg"):
        d = r.get("delegate", {})
        sc = d.get("delegate_scorecard") or d.get("performance") or {}
        preds = d.get("predictions") or []
        coaching = d.get("coaching") or []
        visits_today = sc.get("visits_today", "?")
        visits_target = sc.get("visits_target", 12)
        ca_pct = sc.get("ca_achievement_pct")
        tier = sc.get("tier", "?")

        if any(k in msg for k in ("visite", "visit", "aujourd")):
            return (f"📅 Aujourd'hui: **{visits_today}/{visits_target}** visites effectuées. "
                    f"Objectif CA: **{_fmt(ca_pct,'%')}** · Tier: **{tier}**. "
                    f"Prochaine visite prioritaire: {preds[0].get('pharmacy_name','—') if preds else 'aucune'}.")

        if any(k in msg for k in ("ca", "chiffre", "objectif", "performance", "score")):
            return (f"💰 Réalisation CA: **{_fmt(ca_pct,'%')}** · Tier: **{tier}**. "
                    f"Visites: {visits_today}/{visits_target}. "
                    + (f"Alerte coaching: {coaching[0].get('message','—')}" if coaching else "Aucune alerte coaching."))

        if any(k in msg for k in ("prédiction", "prediction", "pharmacie prioritaire", "priorité")):
            if not preds:
                return "🤖 Aucune prédiction disponible pour le moment."
            lines = [f"• {p.get('pharmacy_name','?')} — score {_fmt(p.get('score') or p.get('prediction_score'),'')}" for p in preds[:5]]
            return "🎯 **Top pharmacies prioritaires:**\n" + "\n".join(lines)

        if any(k in msg for k in ("coaching", "conseil", "améliorer")):
            if not coaching:
                return "✅ Aucune alerte coaching — continuez sur cette lancée !"
            lines = [f"• {c.get('message','?')}" for c in coaching[:3]]
            return "🧠 **Conseils coaching:**\n" + "\n".join(lines)

    # ── PHARMACY context ─────────────────────────────────────────────────────
    if role == "pharmacy":
        ph = r.get("pharmacy", {})
        portfolio = ph.get("portfolio") or []
        products = ph.get("products") or []

        if any(k in msg for k in ("produit", "product", "stock", "commande")):
            if not products:
                return "📦 Données produits non disponibles."
            lines = [f"• {p.get('product_name','?')} — {_fmt(p.get('demand_score') or p.get('score'))}" for p in products[:5]]
            return "💊 **Produits recommandés:**\n" + "\n".join(lines)

        if any(k in msg for k in ("pharmacie", "portfolio", "segment", "rfm")):
            total = len(portfolio)
            return (f"🏥 Portfolio: **{total}** pharmacies. "
                    f"Produits actifs: **{len(products)}**. "
                    f"Demandez des détails sur un produit ou segment spécifique.")

    # ── SUPERVISOR context ────────────────────────────────────────────────────
    if role in ("supervisor", "superviseur"):
        sv = r.get("supervisor", {})
        delegates = sv.get("delegates") or []
        below = sv.get("below_average") or []
        top = delegates[0] if delegates else {}

        if any(k in msg for k in ("délégué", "delegate", "classement", "ranking", "performance", "équipe")):
            if not delegates:
                return "👥 Données délégués non disponibles."
            lines = [f"• {d.get('delegate_name','?')} — {_fmt(d.get('ca_achievement_pct'),'%')}" for d in delegates[:5]]
            return f"🏆 **Top 5 délégués:**\n" + "\n".join(lines)

        if any(k in msg for k in ("alerte", "risque", "sous", "below")):
            if not below:
                return "✅ Aucun délégué en sous-performance."
            lines = [f"• {d.get('delegate_name','?')} — {_fmt(d.get('ca_achievement_pct'),'%')}" for d in below[:5]]
            return "⚠️ **Délégués en sous-performance:**\n" + "\n".join(lines)

    # ── MARKETING context ─────────────────────────────────────────────────────
    if role == "marketing":
        mk = r.get("marketing", {})
        animations = mk.get("animations") or []
        segments = mk.get("segments") or []
        sentiment = mk.get("sentiment_score")

        if any(k in msg for k in ("animation", "campagne", "event", "événement")):
            if not animations:
                return "🎯 Aucune animation en cours."
            lines = [f"• {a.get('product','?')} — {a.get('zone','?')} ({a.get('type','?')})" for a in animations[:5]]
            return "🎪 **Animations actives:**\n" + "\n".join(lines)

        if any(k in msg for k in ("sentiment", "avis", "feedback", "nlp")):
            s = _fmt(sentiment * 100 if sentiment and sentiment <= 1 else sentiment, "%")
            return f"💬 Sentiment global: **{s} positif**. Segments RFM actifs: {len(segments)}."

        if any(k in msg for k in ("segment", "rfm", "client")):
            if not segments:
                return "📊 Données RFM non disponibles."
            lines = [f"• {s.get('name','?')} — {s.get('count','?')} pharmacies" for s in segments[:4]]
            return "📊 **Segments RFM:**\n" + "\n".join(lines)

    # ── FOUNDER / DIRECTION context ───────────────────────────────────────────
    if role in ("founder", "direction"):
        fd = r.get("founder", {})
        ca = fd.get("total_ca")
        nb_delegates = fd.get("nb_delegates")
        zones = fd.get("zones") or []
        growth = fd.get("growth_rate")

        if any(k in msg for k in ("ca", "chiffre", "revenu", "revenue")):
            return (f"💰 CA Total: **{_fmt(ca)} MAD**. "
                    f"Croissance: **{_fmt(growth,'%')}**. "
                    f"Délégués actifs: **{nb_delegates}**.")

        if any(k in msg for k in ("zone", "géographie", "région", "region")):
            if not zones:
                return f"🗺️ {len(zones)} zones actives."
            lines = [f"• {z.get('zone','?')} — CA {_fmt(z.get('ca'))}" for z in zones[:5]]
            return "🗺️ **Zones géographiques:**\n" + "\n".join(lines)

        if any(k in msg for k in ("délégué", "delegate", "équipe")):
            return (f"👥 **{nb_delegates}** délégués actifs. "
                    f"CA moyen par délégué: **{_fmt(ca / nb_delegates if ca and nb_delegates else None)} MAD**.")

    # ── GENERIC fallback ─────────────────────────────────────────────────────
    generic_help = {
        "delegate":   "visites, CA, prédictions, coaching",
        "pharmacy":   "produits, portfolio, commandes",
        "supervisor": "délégués, classement, alertes",
        "marketing":  "animations, sentiment, segments RFM",
        "founder":    "CA global, zones, équipe",
        "direction":  "CA global, zones, équipe",
    }
    topics = generic_help.get(role, "données disponibles")
    return (f"🤖 Je peux vous aider sur: **{topics}**. "
            f"Posez une question précise, ex: \"Quelles sont mes visites aujourd'hui ?\" "
            f"ou \"Montre-moi les prédictions prioritaires.\"")


@app.post("/chat", tags=["Chat"])
async def chat(req: ChatRequest, api_key: str = Depends(api_key_user)):
    """Orchestrator chatbot — answers questions using real analytics data."""
    role = api_key.get("role_key", req.role)

    # Use cached analytics data (build if not cached)
    cached = cache_get(f"all_roles:{req.visit_id}")
    if not cached:
        try:
            cached = _build_all_roles(req.visit_id)
            cache_set(f"all_roles:{req.visit_id}", cached, 1800)
        except Exception as e:
            cached = {"roles": {}}

    reply = _chat_respond(req.message, role, cached)
    return {
        "reply": reply,
        "role": role,
        "visit_id": req.visit_id,
        "timestamp": datetime.now().isoformat(),
    }

# =============================================================================
# STARTUP / SHUTDOWN
# =============================================================================

@app.on_event("startup")
async def on_startup():
    global _db, _orch, _analysis

    _init_users_json()

    try:
        _db = MedinoteDB()
        log.info("DB connected")
    except Exception as e:
        log.error("DB connect failed: %s", e)

    try:
        _orch = OrchestratorAgent()
        log.info("Orchestrator ready")
    except Exception as e:
        log.error("Orchestrator init failed: %s", e)

    if _db:
        _analysis = DeepAnalysis(_db)
        log.info("DeepAnalysis engine ready")

        # Warm KPI cache
        try:
            cache_set("kpis:DIRECTION:", _kpis_direction(_db), 3600)
            log.info("KPI cache warmed")
        except Exception as e:
            log.warning("KPI warm failed: %s", e)

    _print_banner()


@app.on_event("shutdown")
async def on_shutdown():
    if _orch:
        _orch.close()
    if _db:
        _db.close()
    log.info("Medinote API shut down")


def _print_banner():
    print("""
  ============================================================
    MEDINOTE AI REST API  v1.0
    http://localhost:8000
    Docs (Swagger): http://localhost:8000/docs
  ============================================================
    AUTH
      POST  /auth/login          Login, returns JWT
      GET   /auth/me             Current user profile

    DASHBOARD
      GET   /dashboard/kpis      Role-filtered KPIs

    PREDICTIONS
      POST  /predict             Free-text ML query
      GET   /predict/churn       Churn risk list
      GET   /predict/payment-risk Payment default risk
      GET   /predict/visit-priority  Visit order by urgency
      GET   /predict/product-demand  Seasonal demand
      GET   /predict/cross-sell/{id} Cross-sell for pharmacy

    ANALYTICS  (cached 1h)
      GET   /analytics/geographic
      GET   /analytics/delegates
      GET   /analytics/products
      GET   /analytics/rfm
      GET   /analytics/temporal
      GET   /analytics/pharmacies

    DELEGATE
      GET   /my/pharmacies       My pharmacy portfolio
      GET   /my/performance      My revenue & rank
      GET   /my/visit-plan       Today/week visit schedule

    ALERTS
      GET   /alerts              Role-filtered alerts

    CHAT
      POST  /chat                NLP question + chart data

    SYSTEM
      GET   /health
      DELETE /cache              Clear cache (DIRECTION only)

    Default credentials: password = medinote2026
  ============================================================
""")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
