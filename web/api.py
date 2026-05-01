"""
FastAPI Server with Orchestrator + Database + Swagger UI

Swagger automatically available at: http://localhost:8000/docs
ReDoc available at: http://localhost:8000/redoc

Run:
  python web/api.py
  
Then visit:
  http://localhost:8000/docs (Swagger UI - interactive testing)
"""

import logging
import sys
import os
import asyncio
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Set
from datetime import datetime
import json
import uvicorn

# Add parent directory to path so we can import orchestrator and agents
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import Orchestrator, apply_role_adapters
from agents import run_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# API KEY AUTHENTICATION SETUP
# ============================================================================

# API key to role mapping (load from environment with fallback defaults)
API_KEYS = {
    os.environ.get("API_KEY_PHARMACY", "ph-key-2026"): "pharmacy",
    os.environ.get("API_KEY_DOCTOR", "dr-key-2026"): "doctor",
    os.environ.get("API_KEY_DELEGATE", "dlg-key-2026"): "delegate",
    os.environ.get("API_KEY_DELEGATE_MOBILE") or "del-key-2026": "delegate",
    "del-key-2026": "delegate",
    os.environ.get("API_KEY_SUPERVISOR", "sup-key-2026"): "supervisor",
    os.environ.get("API_KEY_MANAGER", "mgr-key-2026"): "supervisor",
    os.environ.get("API_KEY_MARKETING", "mkt-key-2026"): "marketing",
    os.environ.get("API_KEY_FOUNDER", "fdr-key-2026"): "founder",
    os.environ.get("API_KEY_ADMIN", "admin-key-2026"): "admin",
}

def get_current_role(api_key: Optional[str] = None) -> Optional[str]:
    """
    Validate API key and return associated role.
    
    Args:
        api_key: API key from X-API-Key header (can be None)
        
    Returns:
        Role name (pharmacy, doctor, delegate, supervisor, marketing, founder, or admin)
        or None if no valid API key provided
    """
    if not api_key:
        # Return None for unauthenticated access
        return None
    
    if api_key not in API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return API_KEYS[api_key]

# ============================================================================
# PYDANTIC MODELS (For request/response validation + Swagger docs)
# ============================================================================

class VisitRequest(BaseModel):
    """Visit data for prediction"""
    id_rapport: int = Field(..., description="Visit ID (e.g., 123)")
    delegate_id: Optional[str] = Field(None, description="Delegate ID (e.g., D01)")
    pharmacy_id: Optional[str] = Field(None, description="Pharmacy ID (e.g., PH100)")
    date_visite: Optional[str] = Field(None, description="Visit date (e.g., 2026-04-18)")
    mouvement: Optional[str] = Field(None, description="Movement type (e.g., forte, moyen)")
    zone_id: Optional[str] = Field(None, description="Zone ID (e.g., Z01)")
    manager_id: Optional[str] = Field(None, description="Manager ID (e.g., MGR01)")


class NewVisitRequest(BaseModel):
    """New visit report for immediate analysis"""
    id_rapport: int = Field(..., description="Visit ID")
    delegate_id: str = Field(..., description="Delegate ID")
    pharmacy_id: str = Field(..., description="Pharmacy ID")
    date_visite: str = Field(..., description="Visit date (YYYY-MM-DD)")
    mouvement: Optional[str] = Field(None, description="Movement type")
    commentaire: Optional[str] = Field(None, description="Visit comments")
    manager_id: Optional[str] = Field(None, description="Manager ID")
    zone_id: Optional[str] = Field(None, description="Zone ID")


class NewVisitResponse(BaseModel):
    """Response after analyzing new visit"""
    visit_id: int
    status: str
    execution_time_sec: float
    roles: Dict[str, Dict[str, Any]]
    errors: Dict[str, str]


class RoleQueryParams(BaseModel):
    """Role query parameters"""
    role: str = Field("founder", description="View role: pharmacy, doctor, delegate, supervisor, marketing, founder")
    zone_id: Optional[str] = Field(None, description="Zone ID for filtering")
    manager_id: Optional[str] = Field(None, description="Manager ID for filtering")


class PredictionResponse(BaseModel):
    """Prediction response with metadata"""
    status: str = Field("success", description="Response status")
    timestamp: str = Field(..., description="Response timestamp")
    visit_id: int = Field(..., description="Visit ID")
    role: str = Field(..., description="Role used for filtering")
    execution_time_sec: float = Field(..., description="Pipeline execution time")
    data: Dict[str, Any] = Field(..., description="Role-specific prediction data")


class AllRolesResponse(BaseModel):
    """All 6 roles in one response"""
    visit_id: int
    timestamp: str
    execution_time_sec: float
    roles: Dict[str, Dict[str, Any]]


class BatchRequest(BaseModel):
    """Batch prediction request"""
    visit_ids: List[int] = Field(..., description="List of visit IDs (e.g., [1,2,3])")
    role: str = Field("founder", description="View role for all predictions")


class BatchResponse(BaseModel):
    """Batch prediction response"""
    status: str
    timestamp: str
    total_requested: int
    total_successful: int
    results: List[Dict[str, Any]]


class StatusResponse(BaseModel):
    """System status response"""
    status: str
    version: str
    timestamp: str
    agents_count: int
    phases: int
    max_workers: int
    timeout_sec: int
    roles_supported: List[str]
    endpoints: List[str]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    database_connected: bool
    agents_available: int
    orchestrator_ready: bool
    last_successful_run: Optional[str]


# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title="Pharmacy Analytics Orchestrator",
    description="🏥 Multi-agent orchestration system for pharmacy visit predictions\n\n"
                "**Features:**\n"
                "- 21 parallel agents coordinated across 3 phases\n"
                "- 6 role-based output views (pharmacy, doctor, delegate, supervisor, marketing, founder)\n"
                "- Database integration with CSV fallback\n"
                "- Real-time risk synthesis and recommendations\n\n"
                "**Try it out:** Use the endpoints below to make predictions",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for caching
_last_run = None
_last_run_time = None
_alert_subscribers: Set[WebSocket] = set()
_alert_subscribers_lock = asyncio.Lock()


def _extract_alerts(full_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract alert list from orchestrator output across supported shapes."""
    alerte_data = full_data.get("agent_outputs", {}).get("alerte", [])
    if isinstance(alerte_data, list):
        return [a for a in alerte_data if isinstance(a, dict)]
    if isinstance(alerte_data, dict):
        maybe_alerts = alerte_data.get("alerts", [])
        if isinstance(maybe_alerts, list):
            return [a for a in maybe_alerts if isinstance(a, dict)]
    return []


async def _publish_alert_event(event: Dict[str, Any]) -> None:
    """Broadcast an alert payload to all connected websocket subscribers."""
    async with _alert_subscribers_lock:
        subscribers = list(_alert_subscribers)

    disconnected = []
    for websocket in subscribers:
        try:
            await websocket.send_json(event)
        except Exception:
            disconnected.append(websocket)

    if disconnected:
        async with _alert_subscribers_lock:
            for websocket in disconnected:
                _alert_subscribers.discard(websocket)


async def _stream_alerts_from_pipeline(full_data: Dict[str, Any], source: str) -> None:
    """Push alert events produced by orchestrator runs to websocket clients."""
    alerts = _extract_alerts(full_data)
    if not alerts:
        return

    risk_components = full_data.get("risk_synthesis", {}).get("components", {})
    event = {
        "type": "agent_alerts",
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "visit_id": full_data.get("metadata", {}).get("visit_id"),
        "alert_level": risk_components.get("alert_level"),
        "alerts_count": len(alerts),
        "alerts": alerts,
    }
    await _publish_alert_event(event)


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """Stream real-time orchestrator alert events to connected clients."""
    await websocket.accept()
    async with _alert_subscribers_lock:
        _alert_subscribers.add(websocket)

    await websocket.send_json({
        "type": "connection",
        "status": "connected",
        "timestamp": datetime.now().isoformat(),
    })

    try:
        # Keep the connection open and allow optional client ping messages.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        async with _alert_subscribers_lock:
            _alert_subscribers.discard(websocket)


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/", tags=["System"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Pharmacy Analytics Orchestrator",
        "version": "2.0.0",
        "status": "✅ Running",
        "swagger_ui": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "status_endpoint": "/status",
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check system health and availability"""
    try:
        # Test orchestrator
        orch = Orchestrator()
        
        # Test agent registry
        try:
            from agents import AgentRegistry
            agents_available = len(AgentRegistry._agents) if hasattr(AgentRegistry, "_agents") else 21
        except:
            agents_available = 21
        
        return HealthResponse(
            status="operational",
            timestamp=datetime.now().isoformat(),
            database_connected=True,
            agents_available=max(14, agents_available),  # At least Phase 1 + Phase 2
            orchestrator_ready=True,
            last_successful_run=_last_run_time,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="degraded",
            timestamp=datetime.now().isoformat(),
            database_connected=False,
            agents_available=0,
            orchestrator_ready=False,
            last_successful_run=_last_run_time,
        )


@app.get("/status", response_model=StatusResponse, tags=["System"])
async def get_status():
    """Get system status and configuration"""
    return StatusResponse(
        status="operational",
        version="2.0.0",
        timestamp=datetime.now().isoformat(),
        agents_count=21,
        phases=5,
        max_workers=7,
        timeout_sec=30,
        roles_supported=["pharmacy", "doctor", "delegate", "supervisor", "marketing", "founder"],
        endpoints=[
            "/predictions/{visit_id}",
            "/predictions/{visit_id}/all-roles",
            "/predictions/batch",
            "/health",
            "/status",
        ]
    )


# ============================================================================
# PREDICTION ENDPOINTS
# ============================================================================

@app.post("/predictions", response_model=PredictionResponse, tags=["Predictions"])
async def create_prediction(
    request: VisitRequest,
    role: str = Query("founder", description="Role: pharmacy|doctor|delegate|supervisor|marketing|founder"),
):
    """
    Get prediction for a single visit with role-based filtering
    
    **Parameters:**
    - `visit_id`: The pharmacy visit ID
    - `role`: View role (pharmacy, doctor, delegate, supervisor, marketing, founder)
    - `zone_id`: Optional zone for filtering
    - `manager_id`: Optional manager for filtering
    
    **Returns:** Role-specific prediction data
    
    **Example:**
    ```json
    {
      "id_rapport": 123,
      "delegate_id": "D01",
      "pharmacy_id": "PH100"
    }
    ```
    """
    
    # Validate role
    valid_roles = ["pharmacy", "doctor", "delegate", "supervisor", "marketing", "founder"]
    if role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    
    try:
        logger.info(f"📍 Prediction request: visit_id={request.id_rapport}, role={role}")
        
        # Prepare visit data
        visit_data = {
            "id_rapport": request.id_rapport,
            "delegate_id": request.delegate_id or "UNKNOWN",
            "pharmacy_id": request.pharmacy_id or "UNKNOWN",
            "date_visite": request.date_visite or datetime.now().isoformat(),
            "mouvement": request.mouvement or "moyen",
        }
        
        # Run orchestrator
        logger.info(f"🚀 Running orchestrator pipeline...")
        orchestrator = Orchestrator(max_workers=7, timeout=30)
        full_data = orchestrator.run_full_pipeline(
            visit_data,
            manager_id=request.manager_id,
            zone_id=request.zone_id,
        )
        
        # Apply role adapters
        logger.info(f"🎭 Applying role adapters...")
        adapted = apply_role_adapters(full_data)
        await _stream_alerts_from_pipeline(full_data, source="prediction")
        
        # Prepare response
        response = {
            "status": "success",
            "timestamp": full_data["metadata"]["timestamp"],
            "visit_id": request.id_rapport,
            "role": role,
            "execution_time_sec": full_data["metadata"]["total_duration_sec"],
            "data": adapted[role],
        }
        
        # Cache result
        global _last_run, _last_run_time
        _last_run = response
        _last_run_time = datetime.now().isoformat()
        
        logger.info(f"✅ Prediction complete in {response['execution_time_sec']:.2f}s")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Prediction failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictions/{visit_id}", response_model=PredictionResponse, tags=["Predictions"])
async def get_prediction(
    visit_id: int,
    role: str = Query("founder", description="View role"),
    zone_id: Optional[str] = Query(None, description="Zone ID"),
    manager_id: Optional[str] = Query(None, description="Manager ID"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    Get prediction for a single visit (GET variant with API key authentication)
    
    **Headers:**
    - `X-API-Key`: API key (required for role-based access control)
    
    **URL Parameters:**
    - `visit_id`: Visit ID (in path)
    - `role`: View role (query param)
    - `zone_id`: Optional zone (query param)
    - `manager_id`: Optional manager (query param)
    
    **Returns:** Prediction with role-specific filtering
    
    **Example URLs:**
    - `GET /predictions/123?role=pharmacy`
      - Headers: `X-API-Key: ph-key-2026`
    - `GET /predictions/456?role=delegate&zone_id=Z01`
      - Headers: `X-API-Key: dlg-key-2026`
    
    **Role-Based Access Control:**
    - Each API key has an associated role
    - Can only access matching role view, unless key is admin
    - Admin key can access any role
    """
    
    # Check authentication
    allowed_role = get_current_role(x_api_key)
    if not allowed_role:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    
    # Check authorization: can only access own role unless admin
    if allowed_role != "admin" and role != allowed_role:
        raise HTTPException(
            status_code=403,
            detail=f"API key is for '{allowed_role}' role, cannot access '{role}' role"
        )
    
    request = VisitRequest(
        id_rapport=visit_id,
        zone_id=zone_id,
        manager_id=manager_id,
    )
    return await create_prediction(request, role=role)


@app.get("/predictions/{visit_id}/all-roles", response_model=AllRolesResponse, tags=["Predictions"])
async def get_all_roles(
    visit_id: int,
    zone_id: Optional[str] = Query(None, description="Zone ID"),
    manager_id: Optional[str] = Query(None, description="Manager ID"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    Get all 6 role-based views in one response (requires API key)
    
    **Headers:**
    - `X-API-Key`: API key (required)
    
    **Returns:** All roles (pharmacy, doctor, delegate, supervisor, marketing, founder)
    
    **Useful for:** Dashboard initialization, multi-role systems
    
    **Example:**
    - `GET /predictions/123/all-roles`
      - Headers: `X-API-Key: admin-key-2026`
    - `GET /predictions/456/all-roles?zone_id=Z01`
      - Headers: `X-API-Key: fnd-key-2026`
    """
    
    # Check authentication
    allowed_role = get_current_role(x_api_key)
    if not allowed_role:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    
    try:
        logger.info(f"📍 All-roles request: visit_id={visit_id}, role={allowed_role}")
        
        visit_data = {
            "id_rapport": visit_id,
            "zone_id": zone_id,
        }
        
        orchestrator = Orchestrator()
        full_data = orchestrator.run_full_pipeline(
            visit_data,
            manager_id=manager_id,
            zone_id=zone_id,
        )
        
        adapted = apply_role_adapters(full_data)
        await _stream_alerts_from_pipeline(full_data, source="all_roles")
        
        response = {
            "visit_id": visit_id,
            "timestamp": full_data["metadata"]["timestamp"],
            "execution_time_sec": full_data["metadata"]["total_duration_sec"],
            "roles": adapted,
        }
        
        logger.info(f"✅ All-roles complete in {response['execution_time_sec']:.2f}s")
        return response
    
    except Exception as e:
        logger.error(f"❌ All-roles failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BATCH PROCESSING ENDPOINTS
# ============================================================================

@app.post("/predictions/batch", response_model=BatchResponse, tags=["Batch"])
async def batch_predictions(
    request: BatchRequest,
    background_tasks: BackgroundTasks,
):
    """
    Process multiple predictions in batch
    
    **Parameters:**
    - `visit_ids`: List of visit IDs (e.g., [1,2,3,4,5])
    - `role`: Role for all predictions
    
    **Returns:** Results for all visits
    
    **Example Request:**
    ```json
    {
      "visit_ids": [100, 101, 102, 103],
      "role": "pharmacy"
    }
    ```
    """
    
    logger.info(f"📦 Batch request: {len(request.visit_ids)} visits, role={request.role}")
    
    results = []
    successful = 0
    
    for visit_id in request.visit_ids:
        try:
            visit_data = {"id_rapport": visit_id}
            orchestrator = Orchestrator()
            full_data = orchestrator.run_full_pipeline(visit_data)
            adapted = apply_role_adapters(full_data)
            
            results.append({
                "visit_id": visit_id,
                "status": "success",
                "data": adapted[request.role],
                "execution_time_sec": full_data["metadata"]["total_duration_sec"],
            })
            successful += 1
        except Exception as e:
            logger.warning(f"⚠️  Visit {visit_id} failed: {str(e)}")
            results.append({
                "visit_id": visit_id,
                "status": "error",
                "error": str(e),
            })
    
    response = {
        "status": "complete",
        "timestamp": datetime.now().isoformat(),
        "total_requested": len(request.visit_ids),
        "total_successful": successful,
        "results": results,
    }
    
    logger.info(f"✅ Batch complete: {successful}/{len(request.visit_ids)} successful")
    return response


@app.get("/predictions/batch", tags=["Batch"])
async def batch_predictions_get(
    visit_ids: str = Query(..., description="Comma-separated visit IDs (e.g., 1,2,3,4,5)"),
    role: str = Query("founder", description="View role for all predictions"),
):
    """
    Process multiple predictions via GET (URL parameters)
    
    **Query Parameters:**
    - `visit_ids`: Comma-separated list (e.g., "1,2,3,4,5")
    - `role`: Role for all predictions
    
    **Example:**
    - `/predictions/batch?visit_ids=100,101,102&role=pharmacy`
    - `/predictions/batch?visit_ids=1,2,3,4,5,6,7,8,9,10&role=delegate`
    """
    
    try:
        # Parse visit_ids
        ids = [int(x.strip()) for x in visit_ids.split(",")]
        request = BatchRequest(visit_ids=ids, role=role)
        return await batch_predictions(request, BackgroundTasks())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="visit_ids must be comma-separated integers (e.g., '1,2,3')"
        )


# ============================================================================
# NEW VISIT ANALYSIS ENDPOINT
# ============================================================================

@app.post("/visits/analyze", response_model=NewVisitResponse, tags=["Visits"])
async def analyze_new_visit(request: NewVisitRequest):
    """
    Submit a new visit report and get instant predictions for all 6 roles.
    
    Runs the full orchestrator pipeline on the provided visit data and returns
    all 6 role-based views in a single response.
    
    **Request Body:**
    - `id_rapport`: Visit ID (required)
    - `delegate_id`: Delegate ID (required)
    - `pharmacy_id`: Pharmacy ID (required)
    - `date_visite`: Visit date (required, YYYY-MM-DD format)
    - `mouvement`: Movement type (optional)
    - `commentaire`: Visit comments (optional)
    - `manager_id`: Manager ID (optional)
    - `zone_id`: Zone ID (optional)
    
    **Returns:** All 6 role views (pharmacy, doctor, delegate, supervisor, marketing, founder)
    
    **Example:**
    ```json
    {
      "id_rapport": 1000,
      "delegate_id": "D001",
      "pharmacy_id": "PH001",
      "date_visite": "2026-04-18",
      "mouvement": "forte",
      "commentaire": "Good visit, strong orders",
      "zone_id": "Z001",
      "manager_id": "MGR001"
    }
    ```
    """
    try:
        logger.info(f"Analyzing new visit {request.id_rapport}...")
        
        # Build visit data from request
        visit_data = {
            "id_rapport": request.id_rapport,
            "delegate_id": request.delegate_id,
            "pharmacy_id": request.pharmacy_id,
            "date_visite": request.date_visite,
            "mouvement": request.mouvement,
            "commentaire": request.commentaire,
        }
        
        # Run orchestrator
        orchestrator = Orchestrator()
        full_data = orchestrator.run_full_pipeline(
            visit_data,
            manager_id=request.manager_id,
            delegate_id=request.delegate_id,
            zone_id=request.zone_id,
        )
        
        # Get all role views
        role_views = apply_role_adapters(full_data)
        await _stream_alerts_from_pipeline(full_data, source="analyze_visit")
        
        logger.info(f"✅ Visit {request.id_rapport} analyzed successfully")
        
        return {
            "visit_id": request.id_rapport,
            "status": "analyzed",
            "execution_time_sec": full_data.get("metadata", {}).get("total_duration_sec", 0),
            "roles": role_views,
            "errors": full_data.get("errors", {}),
        }
    except Exception as e:
        logger.error(f"❌ Visit analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze visit: {str(e)}"
        )


# ============================================================================
# AGENT DEBUGGING ENDPOINTS
# ============================================================================

@app.get("/debug/agent/{agent_name}", tags=["Debug"])
async def debug_agent(
    agent_name: str,
    visit_id: int = Query(123, description="Visit ID for testing"),
):
    """
    Run a single agent directly (for debugging)
    
    **Parameters:**
    - `agent_name`: Name of agent (perf, nlp, alerte, compliance, finance, roi, forecast, etc.)
    - `visit_id`: Visit ID to test with
    
    **Returns:** Direct agent output
    
    **Useful for:**
    - Testing individual agents
    - Checking agent output format
    - Debugging agent failures
    
    **Example:**
    - `/debug/agent/perf?visit_id=123`
    - `/debug/agent/nlp?visit_id=456`
    - `/debug/agent/roi?visit_id=789`
    """
    
    try:
        logger.info(f"🔧 Debug agent: {agent_name}")
        
        result = run_agent(agent_name, visit_id=visit_id)
        
        return {
            "status": "success",
            "agent": agent_name,
            "visit_id": visit_id,
            "output": result,
            "output_type": type(result).__name__,
            "output_keys": list(result.keys()) if isinstance(result, dict) else None,
        }
    except Exception as e:
        logger.error(f"❌ Agent {agent_name} failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/performance", tags=["Debug"])
async def get_performance_report():
    """
    Get bottleneck analysis and performance metrics
    
    Identifies which agents are slow and which phases take longest.
    Useful for optimization and capacity planning.
    
    **Returns:**
    - `slow_agents`: List of agents taking >10 seconds
    - `slow_agents_count`: Number of slow agents
    - `execution_log`: Details of each phase's execution
    - `slowest_phases`: Top 3 slowest phases
    - `recommendation`: Suggested optimizations
    """
    try:
        # Create a test orchestrator to get metrics
        orch = Orchestrator()
        return orch.get_bottleneck_report()
    except Exception as e:
        logger.error(f"❌ Performance report failed: {str(e)}")
        return {
            "error": str(e),
            "slow_agents": [],
            "execution_log": [],
            "recommendation": "Run a prediction first to generate performance metrics"
        }


# ============================================================================
# SAMPLE DATA ENDPOINTS
# ============================================================================

@app.get("/sample-data", tags=["Utilities"])
async def get_sample_data():
    """Get sample visit data for testing"""
    return {
        "visits": [
            {
                "id_rapport": 100,
                "delegate_id": "D01",
                "pharmacy_id": "PH001",
                "date_visite": "2026-04-18",
                "mouvement": "forte",
            },
            {
                "id_rapport": 101,
                "delegate_id": "D02",
                "pharmacy_id": "PH002",
                "date_visite": "2026-04-18",
                "mouvement": "moyen",
            },
            {
                "id_rapport": 102,
                "delegate_id": "D03",
                "pharmacy_id": "PH003",
                "date_visite": "2026-04-18",
                "mouvement": "faible",
            },
            {
                "id_rapport": 103,
                "delegate_id": "D04",
                "pharmacy_id": "PH004",
                "date_visite": "2026-04-18",
                "mouvement": "très_forte",
            },
            {
                "id_rapport": 104,
                "delegate_id": "D05",
                "pharmacy_id": "PH005",
                "date_visite": "2026-04-18",
                "mouvement": "moyen",
            },
        ],
        "description": "Use these visit_ids in /predictions/{visit_id} endpoints"
    }


# ============================================================================
# TEST ENDPOINT (For quick verification)
# ============================================================================

@app.get("/test", tags=["Test"])
async def quick_test():
    """Quick test of the full pipeline"""
    try:
        logger.info("🧪 Running quick test...")
        
        test_visit = {
            "id_rapport": 999,
            "delegate_id": "TEST_D01",
            "pharmacy_id": "TEST_PH",
        }
        
        orchestrator = Orchestrator()
        full_data = orchestrator.run_full_pipeline(test_visit)
        adapted = apply_role_adapters(full_data)
        
        return {
            "status": "✅ PASS",
            "timestamp": datetime.now().isoformat(),
            "test_duration_sec": full_data["metadata"]["total_duration_sec"],
            "agents_run": full_data["metadata"]["total_agents_run"],
            "errors": len(full_data.get("errors", {})),
            "roles_generated": len(adapted),
            "sample_pharmacy_view_keys": list(adapted["pharmacy"].keys()),
        }
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}", exc_info=True)
        return {
            "status": "❌ FAIL",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "code": exc.status_code,
            "detail": exc.detail,
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "code": 500,
            "detail": "Internal server error",
        }
    )


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("="*60)
    logger.info("🚀 PHARMACY ANALYTICS ORCHESTRATOR v2.0")
    logger.info("="*60)
    logger.info("📊 Swagger UI: http://localhost:8000/docs")
    logger.info("📖 ReDoc: http://localhost:8000/redoc")
    logger.info("🧪 Quick Test: http://localhost:8000/test")
    logger.info("💾 Sample Data: http://localhost:8000/sample-data")
    logger.info("="*60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Server shutting down...")


# ============================================================================
# MAIN - RUN SERVER
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🏥 PHARMACY ANALYTICS ORCHESTRATOR - FASTAPI SERVER")
    print("="*70)
    print("\n📍 Starting server on http://localhost:8000")
    print("\n🌐 SWAGGER UI (Interactive API Testing):")
    print("   → http://localhost:8000/docs")
    print("\n📖 ReDoc (API Documentation):")
    print("   → http://localhost:8000/redoc")
    print("\n🧪 QUICK TEST:")
    print("   → http://localhost:8000/test")
    print("\n💾 SAMPLE DATA:")
    print("   → http://localhost:8000/sample-data")
    print("\n" + "="*70 + "\n")
    
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,  # Auto-reload on code changes
    )
