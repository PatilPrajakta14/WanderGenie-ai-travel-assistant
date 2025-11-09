"""
API routes for trip creation and management
"""
import uuid
import asyncio
import logging
from typing import Dict
from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.schemas import CreateTripRequest, EditTripRequest, TripResponse
from backend.agents.graph import trip_graph, edit_graph
from backend.agents.state import TripState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["trips"])

# Temporary in-memory storage (DevOps will replace with actual database)
trips_store: Dict[str, dict] = {}


def generate_trip_id() -> str:
    """Generate unique trip ID"""
    return f"trip_{uuid.uuid4().hex[:8]}"


def run_trip_workflow(trip_id: str, user_input: str):
    """
    Run the LangGraph workflow to generate trip itinerary.
    
    This function is called in the background after the API returns.
    It invokes the agent workflow and stores the result.
    """
    try:
        logger.info(f"Starting trip workflow for {trip_id}")
        
        # Check if trip_graph was initialized
        if trip_graph is None:
            error_msg = "LangGraph workflow not initialized"
            logger.error(error_msg)
            trips_store[trip_id] = {
                "trip_id": trip_id,
                "status": "failed",
                "error": error_msg
            }
            return
        
        # Initialize state
        initial_state: TripState = {
            "user_input": user_input,
            "trip_id": trip_id,
            "intent": None,
            "poi_candidates": [],
            "days": [],
            "links": {},
            "map_geojson": {},
            "calendar_export": {},
            "edit_instruction": None,
            "edit_type": None,
            "needs_new_pois": None,
            "replacement_pois": [],
            "modified_days": [],
            "status": "processing",
            "current_agent": None,
            "errors": []
        }
        
        # Invoke the workflow with config for checkpointer
        logger.info(f"Invoking trip_graph for {trip_id}")
        config = {"configurable": {"thread_id": trip_id}}
        final_state = trip_graph.invoke(initial_state, config=config)
        
        # Convert state to API response format
        if final_state["status"] == "error":
            trips_store[trip_id] = {
                "trip_id": trip_id,
                "status": "failed",
                "errors": final_state["errors"]
            }
            logger.error(f"Trip workflow failed for {trip_id}: {final_state['errors']}")
            return
        
        # Extract data from state
        intent = final_state.get("intent", {})
        days_data = final_state.get("days", [])
        links = final_state.get("links", {})
        
        # Convert to API response format
        trip_response = {
            "trip_id": trip_id,
            "status": "completed",
            "city": intent.get("city", ""),
            "origin": intent.get("origin", ""),
            "start_date": intent.get("start_date", ""),
            "end_date": intent.get("start_date", ""),  # Will be calculated properly later
            "days": days_data,
            "booking_links": links
        }
        
        trips_store[trip_id] = trip_response
        logger.info(f"Trip workflow completed successfully for {trip_id}")
        
    except Exception as e:
        error_msg = f"Workflow execution failed: {str(e)}"
        logger.error(f"Error in trip workflow for {trip_id}: {error_msg}", exc_info=True)
        trips_store[trip_id] = {
            "trip_id": trip_id,
            "status": "failed",
            "error": error_msg
        }


@router.post("/trip")
async def create_trip(request: CreateTripRequest, background_tasks: BackgroundTasks):
    """
    Create a new trip from natural language prompt
    
    Returns immediately with trip_id and 'processing' status.
    The agent workflow runs in background.
    """
    trip_id = generate_trip_id()
    
    # Store initial state
    trips_store[trip_id] = {
        "trip_id": trip_id,
        "status": "processing",
        "prompt": request.prompt
    }
    
    # Trigger LangGraph workflow in background
    background_tasks.add_task(run_trip_workflow, trip_id, request.prompt)
    
    logger.info(f"Created trip {trip_id}, workflow queued")
    
    return {
        "trip_id": trip_id,
        "status": "processing"
    }


@router.get("/trip/{trip_id}")
async def get_trip(trip_id: str):
    """
    Get trip details by ID
    
    Returns complete trip itinerary if processing is done,
    or status='processing' if still working.
    """
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    trip_data = trips_store[trip_id]
    
    # If still processing, return minimal response
    if trip_data["status"] == "processing":
        return {
            "trip_id": trip_id,
            "status": "processing",
            "city": "",
            "origin": "",
            "start_date": "",
            "end_date": "",
            "days": [],
            "booking_links": {"flights": "", "hotels": ""}
        }
    
    # Return complete trip data
    return trip_data


@router.post("/trip/sync")
async def create_trip_sync(request: CreateTripRequest):
    """
    Create trip synchronously (for testing/debugging).
    This blocks until the trip is fully generated.
    """
    trip_id = generate_trip_id()
    
    try:
        logger.info(f"Starting synchronous trip creation for {trip_id}")
        
        # Initialize state
        initial_state: TripState = {
            "user_input": request.prompt,
            "trip_id": trip_id,
            "intent": None,
            "poi_candidates": [],
            "days": [],
            "links": {},
            "map_geojson": {},
            "calendar_export": {},
            "edit_instruction": None,
            "edit_type": None,
            "needs_new_pois": None,
            "replacement_pois": [],
            "modified_days": [],
            "status": "processing",
            "current_agent": None,
            "errors": []
        }
        
        # Run workflow synchronously
        config = {"configurable": {"thread_id": trip_id}}
        final_state = trip_graph.invoke(initial_state, config=config)
        
        if final_state["status"] == "error" or final_state.get("errors"):
            return {
                "trip_id": trip_id,
                "status": "failed",
                "errors": final_state.get("errors", ["Unknown error"])
            }
        
        # Extract data
        intent = final_state.get("intent", {})
        days_data = final_state.get("days", [])
        links = final_state.get("links", {})
        
        return {
            "trip_id": trip_id,
            "status": "completed",
            "city": intent.get("city", ""),
            "origin": intent.get("origin", ""),
            "start_date": intent.get("start_date", ""),
            "days": days_data,
            "booking_links": links
        }
        
    except Exception as e:
        logger.error(f"Sync trip creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/trip/{trip_id}", response_model=TripResponse)
async def edit_trip(trip_id: str, request: EditTripRequest):
    """
    Edit existing trip with natural language instruction
    
    Example: "Swap Day 2 afternoon for MoMA"
    """
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    trip_data = trips_store[trip_id]
    
    if trip_data["status"] == "processing":
        raise HTTPException(
            status_code=409, 
            detail="Trip is still being generated. Please wait."
        )
    
    # TODO: Run LangGraph workflow with edit instruction
    # For now, just return existing data
    
    return trip_data

