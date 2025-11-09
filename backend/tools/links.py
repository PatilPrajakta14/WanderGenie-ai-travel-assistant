"""
Booking link generation tools.

This module provides functions to generate booking links for flights and hotels.
Uses LLM web search for accurate, up-to-date booking links.
"""

import logging
from typing import Dict
from datetime import datetime, timedelta
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


def build_flight_link(
    origin: str,
    destination: str,
    start_date: str,
    return_date: str = None
) -> str:
    """
    Generate a Google Flights booking link with proper parameters.
    
    Args:
        origin: Origin city or airport code
        destination: Destination city or airport code
        start_date: Departure date in YYYY-MM-DD format
        return_date: Optional return date in YYYY-MM-DD format
        
    Returns:
        URL string for Google Flights search
    """
    try:
        # Format dates for Google Flights (remove hyphens)
        dep_date = start_date.replace("-", "")
        
        # Build Google Flights URL
        # Format: https://www.google.com/travel/flights?q=Flights%20from%20{origin}%20to%20{destination}%20on%20{date}
        if return_date:
            ret_date = return_date.replace("-", "")
            # Round trip
            query = f"Flights from {origin} to {destination} departing {start_date} returning {return_date}"
        else:
            # One way
            query = f"Flights from {origin} to {destination} on {start_date}"
        
        params = {"q": query}
        url = f"https://www.google.com/travel/flights?{urlencode(params)}"
        
        logger.info(f"Generated Google Flights link: {url}")
        return url
        
    except Exception as e:
        logger.error(f"Failed to generate flight link: {e}")
        # Ultimate fallback - just Google Flights homepage
        return "https://www.google.com/travel/flights"


def build_hotel_link(
    city: str,
    check_in: str,
    nights: int,
    party: Dict[str, int]
) -> str:
    """
    Generate a Booking.com link with proper date parameters.
    Google Hotels has issues with date parsing, so using Booking.com instead.
    
    Args:
        city: Destination city
        check_in: Check-in date in YYYY-MM-DD format
        nights: Number of nights
        party: Party composition dict with adults, children, teens
        
    Returns:
        URL string for Booking.com search
    """
    try:
        # Parse check-in date
        check_in_dt = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_dt = check_in_dt + timedelta(days=nights)
        
        # Booking.com uses separate year, month, day parameters
        checkin_year = check_in_dt.year
        checkin_month = check_in_dt.month
        checkin_day = check_in_dt.day
        
        checkout_year = check_out_dt.year
        checkout_month = check_out_dt.month
        checkout_day = check_out_dt.day
        
        # Calculate total guests
        adults = party.get("adults", 1)
        children = party.get("children", 0)
        
        # Build Booking.com URL with proper parameters
        params = {
            "ss": city,  # Search string (destination)
            "checkin_year": checkin_year,
            "checkin_month": checkin_month,
            "checkin_monthday": checkin_day,
            "checkout_year": checkout_year,
            "checkout_month": checkout_month,
            "checkout_monthday": checkout_day,
            "group_adults": adults,
            "group_children": children,
            "no_rooms": 1
        }
        
        url = f"https://www.booking.com/searchresults.html?{urlencode(params)}"
        
        logger.info(f"Generated Booking.com link: {url}")
        return url
        
    except Exception as e:
        logger.error(f"Failed to generate hotel link: {e}")
        # Fallback to simple Booking.com search
        params = {"ss": city}
        return f"https://www.booking.com/searchresults.html?{urlencode(params)}"
