"""
Utility functions for the RAG tools AND map_tools.
"""
import math
import requests
from urllib.parse import quote
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

import logging
import re

from google.adk.tools.tool_context import ToolContext
from vertexai import rag

from ..config import (
    LOCATION,
    PROJECT_ID,
)

logger = logging.getLogger(__name__)


def get_corpus_resource_name(corpus_name: str) -> str:
    """
    Convert a corpus name to its full resource name if needed.
    Handles various input formats and ensures the returned name follows Vertex AI's requirements.

    Args:
        corpus_name (str): The corpus name or display name

    Returns:
        str: The full resource name of the corpus
    """
    logger.info(f"Getting resource name for corpus: {corpus_name}")

    # If it's already a full resource name with the projects/locations/ragCorpora format
    if re.match(r"^projects/[^/]+/locations/[^/]+/ragCorpora/[^/]+$", corpus_name):
        return corpus_name

    # Check if this is a display name of an existing corpus
    try:
        # List all corpora and check if there's a match with the display name
        corpora = rag.list_corpora()
        for corpus in corpora:
            if hasattr(corpus, "display_name") and corpus.display_name == corpus_name:
                return corpus.name
    except Exception as e:
        logger.warning(f"Error when checking for corpus display name: {str(e)}")
        # If we can't check, continue with the default behavior
        pass

    # If it contains partial path elements, extract just the corpus ID
    if "/" in corpus_name:
        # Extract the last part of the path as the corpus ID
        corpus_id = corpus_name.split("/")[-1]
    else:
        corpus_id = corpus_name

    # Remove any special characters that might cause issues
    corpus_id = re.sub(r"[^a-zA-Z0-9_-]", "_", corpus_id)

    # Construct the standardized resource name
    return f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/{corpus_id}"


def check_corpus_exists(corpus_name: str, tool_context: ToolContext) -> bool:
    """
    Check if a corpus with the given name exists.

    Args:
        corpus_name (str): The name of the corpus to check
        tool_context (ToolContext): The tool context for state management

    Returns:
        bool: True if the corpus exists, False otherwise
    """
    # Check state first if tool_context is provided
    if tool_context.state.get(f"corpus_exists_{corpus_name}"):
        return True

    try:
        # Get full resource name
        corpus_resource_name = get_corpus_resource_name(corpus_name)

        # List all corpora and check if this one exists
        corpora = rag.list_corpora()
        for corpus in corpora:
            if (
                corpus.name == corpus_resource_name
                or corpus.display_name == corpus_name
            ):
                # Update state
                tool_context.state[f"corpus_exists_{corpus_name}"] = True
                # Also set this as the current corpus if no current corpus is set
                if not tool_context.state.get("current_corpus"):
                    tool_context.state["current_corpus"] = corpus_name
                return True

        return False
    except Exception as e:
        logger.error(f"Error checking if corpus exists: {str(e)}")
        # If we can't check, assume it doesn't exist
        return False


def set_current_corpus(corpus_name: str, tool_context: ToolContext) -> bool:
    """
    Set the current corpus in the tool context state.

    Args:
        corpus_name (str): The name of the corpus to set as current
        tool_context (ToolContext): The tool context for state management

    Returns:
        bool: True if the corpus exists and was set as current, False otherwise
    """
    # Check if corpus exists first
    if check_corpus_exists(corpus_name, tool_context):
        tool_context.state["current_corpus"] = corpus_name
        return True
    return False



def pin_to_city_state(pin: str) -> tuple[str, str]:
    """→ ("Lucknow", "Uttar Pradesh")  or  None if the pin is invalid"""
    url  = f"https://api.postalpincode.in/pincode/{pin}"
    data = requests.get(url, timeout=4).json()
    if data[0]["Status"] != "Success":
        return None
    po = data[0]["PostOffice"][0]
    return po["District"], po["State"]


def dealers_in(city: str, state: str) -> list[dict]:
    """Query HRJ dealer API → list of dicts (may be empty)."""
    url = f"https://www.hrjohnsonindia.com/GetDealerList/{quote(state)}/{quote(city)}"
    resp = requests.get(url, timeout=4, headers={"X-Requested-With": "XMLHttpRequest"})
    resp.raise_for_status()
    return resp.json()            # already JSON list


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    φ1, φ2 = map(math.radians, (lat1, lat2))
    dφ     = math.radians(lat2 - lat1)
    dλ     = math.radians(lon2 - lon1)
    a = math.sin(dφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(dλ / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))