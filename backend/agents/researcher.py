"""
Researcher Agent for the LangGraph travel planning workflow.

This agent is responsible for discovering and enriching points of interest (POIs)
by integrating data from multiple sources: external APIs, VectorDB, and GraphDB.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from .state import TripState, POICandidate
from .llm_config import llm_provider
from backend.tools.poi import poi_search
from backend.memory.vectordb import vectordb_retrieve
from backend.memory.graphdb import graphdb_query
import json
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

RESEARCHER_SYSTEM_PROMPT = """You are a travel research assistant specialized in discovering points of interest.

You will receive:
1. Structured travel intent (city, dates, preferences)
2. POI data from multiple sources (API, VectorDB, GraphDB)

Your task is to:
1. Analyze the provided POI data from all sources
2. Select 20-30 most relevant POIs based on user interests
3. Ensure diversity (different neighborhoods, activity types)
4. Include booking information and practical tips
5. Deduplicate any POIs that appear in multiple sources

Output ONLY valid JSON array of POI candidates:
[
  {
    "name": "string",
    "lat": number,
    "lon": number,
    "tags": ["string"],
    "duration_min": number,
    "booking_required": boolean,
    "booking_url": "string or null",
    "notes": "string or null",
    "open_hours": "string or null"
  }
]

Prioritize:
- POIs matching user interests (from prefs.interests)
- Mix of popular attractions and hidden gems
- Geographic diversity (different neighborhoods)
- Practical considerations (booking requirements, operating hours)
- Appropriate for party composition (family-friendly if children, etc.)

Selection criteria:
- For "relaxed" pace: Focus on 2-3 major attractions per day, leisurely activities
- For "moderate" pace: Mix of 3-4 attractions per day, balanced schedule
- For "fast" pace: Pack in 4-5 attractions per day, efficient routing

IMPORTANT: 
- Return ONLY the JSON array, no additional text or explanation
- Ensure 20-30 POIs are selected (not more, not less)
- Remove duplicates based on name and location similarity
"""


def normalize_poi_name(name: str) -> str:
    """
    Normalize POI name for deduplication.
    
    Args:
        name: Original POI name
        
    Returns:
        Normalized name (lowercase, stripped, common words removed)
    """
    # Convert to lowercase and strip whitespace
    normalized = name.lower().strip()
    
    # Remove common suffixes/prefixes
    remove_words = ["the ", " museum", " park", " building", " center", " centre"]
    for word in remove_words:
        normalized = normalized.replace(word, "")
    
    return normalized.strip()


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    
    Args:
        lat1, lon1: First coordinate
        lat2, lon2: Second coordinate
        
    Returns:
        Distance in kilometers
    """
    from math import radians, sin, cos, sqrt, atan2
    
    # Earth radius in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = R * c
    return distance


def deduplicate_pois(pois: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate POIs based on name similarity and geographic proximity.
    
    Two POIs are considered duplicates if:
    1. Their normalized names match, OR
    2. They are within 100 meters of each other
    
    Args:
        pois: List of POI dictionaries
        
    Returns:
        Deduplicated list of POIs
    """
    if not pois:
        return []
    
    unique_pois = []
    seen_names = set()
    seen_locations = []
    
    for poi in pois:
        # Check name duplication
        normalized_name = normalize_poi_name(poi.get("name", ""))
        
        if normalized_name in seen_names:
            logger.debug(f"Skipping duplicate POI by name: {poi.get('name')}")
            continue
        
        # Check location duplication (within 100m = 0.1km)
        lat = poi.get("lat")
        lon = poi.get("lon")
        
        if lat is None or lon is None:
            logger.warning(f"POI missing coordinates: {poi.get('name')}")
            continue
        
        is_duplicate_location = False
        for seen_lat, seen_lon in seen_locations:
            distance = calculate_distance(lat, lon, seen_lat, seen_lon)
            if distance < 0.1:  # 100 meters
                logger.debug(f"Skipping duplicate POI by location: {poi.get('name')} (within {distance*1000:.0f}m)")
                is_duplicate_location = True
                break
        
        if is_duplicate_location:
            continue
        
        # Add to unique list
        unique_pois.append(poi)
        seen_names.add(normalized_name)
        seen_locations.append((lat, lon))
    
    logger.info(f"Deduplicated {len(pois)} POIs to {len(unique_pois)} unique POIs")
    return unique_pois


def merge_poi_sources(
    api_pois: List[Dict[str, Any]],
    vector_pois: List[Dict[str, Any]],
    graph_pois: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge POIs from multiple sources and deduplicate.
    
    Args:
        api_pois: POIs from external API
        vector_pois: POIs from VectorDB
        graph_pois: POIs from GraphDB
        
    Returns:
        Merged and deduplicated list of POIs
    """
    # Combine all sources
    all_pois = []
    
    # Add source tags for tracking
    for poi in api_pois:
        poi["_source"] = "api"
        all_pois.append(poi)
    
    for poi in vector_pois:
        poi["_source"] = "vector"
        all_pois.append(poi)
    
    for poi in graph_pois:
        poi["_source"] = "graph"
        all_pois.append(poi)
    
    logger.info(f"Merging POIs: {len(api_pois)} from API, {len(vector_pois)} from VectorDB, {len(graph_pois)} from GraphDB")
    
    # Deduplicate
    unique_pois = deduplicate_pois(all_pois)
    
    return unique_pois


def validate_poi_candidates(poi_candidates: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Validate that POI candidates meet requirements.
    
    Args:
        poi_candidates: List of POI candidate dictionaries
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check count
    if len(poi_candidates) < 20:
        return False, f"Too few POI candidates: {len(poi_candidates)} (minimum 20 required)"
    
    if len(poi_candidates) > 30:
        return False, f"Too many POI candidates: {len(poi_candidates)} (maximum 30 allowed)"
    
    # Validate each POI structure
    required_fields = ["name", "lat", "lon", "tags", "duration_min", "booking_required"]
    
    for i, poi in enumerate(poi_candidates):
        for field in required_fields:
            if field not in poi:
                return False, f"POI {i} missing required field: {field}"
        
        # Validate data types
        if not isinstance(poi["name"], str) or not poi["name"]:
            return False, f"POI {i} has invalid name"
        
        if not isinstance(poi["lat"], (int, float)):
            return False, f"POI {i} has invalid latitude"
        
        if not isinstance(poi["lon"], (int, float)):
            return False, f"POI {i} has invalid longitude"
        
        if not isinstance(poi["tags"], list):
            return False, f"POI {i} has invalid tags (must be list)"
        
        if not isinstance(poi["duration_min"], int) or poi["duration_min"] <= 0:
            return False, f"POI {i} has invalid duration_min"
        
        if not isinstance(poi["booking_required"], bool):
            return False, f"POI {i} has invalid booking_required (must be boolean)"
    
    return True, ""


def researcher_node(state: TripState) -> TripState:
    """
    Researcher agent: Discover and enrich POIs.
    
    This node integrates data from multiple sources (API, VectorDB, GraphDB)
    to discover relevant points of interest based on user intent. It performs
    deduplication and selects 20-30 most relevant POIs.
    
    Args:
        state: Current TripState with intent populated
        
    Returns:
        Updated TripState with poi_candidates populated or errors added
    """
    logger.info("Researcher agent starting")
    
    try:
        # Validate that intent exists
        if not state.get("intent"):
            error_msg = "Cannot run researcher without intent from planner"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["status"] = "error"
            state["current_agent"] = "researcher"
            return state
        
        intent = state["intent"]
        city = intent["city"]
        interests = intent["prefs"]["interests"]
        
        logger.info(f"Researching POIs for {city} with interests: {interests}")
        
        # 1. Call POI API
        logger.info("Querying POI API...")
        api_pois = poi_search(city, interests)
        logger.info(f"Found {len(api_pois)} POIs from API")
        
        # 2. Query VectorDB for enrichment
        logger.info("Querying VectorDB...")
        query_text = f"{city} attractions {' '.join(interests)}"
        vector_pois = vectordb_retrieve(query_text, k=15)
        logger.info(f"Found {len(vector_pois)} POIs from VectorDB")
        
        # 3. Query GraphDB for neighborhood clustering
        logger.info("Querying GraphDB...")
        graph_pois = graphdb_query(city)
        logger.info(f"Found {len(graph_pois)} POIs from GraphDB")
        
        # 4. Merge and deduplicate POIs
        logger.info("Merging and deduplicating POIs...")
        merged_pois = merge_poi_sources(api_pois, vector_pois, graph_pois)
        logger.info(f"Merged to {len(merged_pois)} unique POIs")
        
        # 5. Prepare context for LLM selection
        all_pois_data = {
            "merged_pois": merged_pois,
            "total_count": len(merged_pois)
        }
        
        # Prepare messages for LLM
        messages = [
            SystemMessage(content=RESEARCHER_SYSTEM_PROMPT),
            HumanMessage(content=f"""
Intent: {json.dumps(intent, indent=2)}

Available POI Data ({len(merged_pois)} unique POIs after deduplication):
{json.dumps(merged_pois, indent=2)}

Select 20-30 most relevant POIs for this trip based on the user's interests and preferences.
Ensure geographic diversity and a mix of activity types.
""")
        ]
        
        # Invoke LLM with fallback support
        logger.info("Invoking LLM to select POI candidates")
        response = llm_provider.invoke_with_fallback(messages)
        
        # Parse JSON response
        response_content = response.content.strip()
        logger.debug(f"LLM response length: {len(response_content)} characters")
        
        # Handle potential markdown code blocks
        if response_content.startswith("```"):
            lines = response_content.split("\n")
            json_lines = []
            in_code_block = False
            for line in lines:
                if line.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or (not line.startswith("```")):
                    json_lines.append(line)
            response_content = "\n".join(json_lines).strip()
        
        poi_candidates = json.loads(response_content)
        
        # Validate POI candidates
        is_valid, error_msg = validate_poi_candidates(poi_candidates)
        if not is_valid:
            logger.error(f"POI validation failed: {error_msg}")
            state["errors"].append(f"Researcher validation error: {error_msg}")
            state["status"] = "error"
            state["current_agent"] = "researcher"
            return state
        
        # Update state with POI candidates
        state["poi_candidates"] = poi_candidates
        state["status"] = "research_complete"
        state["current_agent"] = "researcher"
        
        logger.info(f"Researcher selected {len(poi_candidates)} POI candidates")
        logger.debug(f"Sample POIs: {[poi['name'] for poi in poi_candidates[:5]]}")
        
        return state
        
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse LLM response as JSON: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Response content: {response.content if 'response' in locals() else 'N/A'}")
        state["errors"].append(f"Researcher JSON error: {error_msg}")
        state["status"] = "error"
        state["current_agent"] = "researcher"
        return state
        
    except Exception as e:
        error_msg = f"Researcher agent failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        state["errors"].append(error_msg)
        state["status"] = "error"
        state["current_agent"] = "researcher"
        return state
