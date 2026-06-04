import logging
from fastapi import APIRouter, HTTPException
import requests
from datetime import datetime
import json
import time

from hevy2garmin.config import load_config

logger = logging.getLogger("hevy2garmin")

router = APIRouter()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:151.0) Gecko/20100101 Firefox/151.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en,en-US;q=0.9,de;q=0.8',
    'x-api-key': 'shelobs_hevy_web',
    'Hevy-Platform': 'web',
    'Origin': 'https://hevy.com',
    'Referer': 'https://hevy.com/'
}

def get_target_username() -> str:
    config = load_config()
    return config.get("hevyless_username", "")

def get_latest_workout_id(username: str) -> str:
    if not username:
        raise ValueError("Hevy username not configured")
        
    url = f"https://api.hevyapp.com/public_user_profile/{username}"
    headers = HEADERS.copy()
    headers['x-client-time'] = str(time.time())
    
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code != 200:
        logger.error(f"Failed to fetch profile for {username}: {resp.status_code}")
        return None
        
    data = resp.json()
    last_workout = data.get("last_workout", {})
    return last_workout.get("short_id")

def fetch_latest_workout() -> dict:
    username = get_target_username()
    if not username:
        return None
        
    logger.info(f"Fetching profile for {username}...")
    short_id = get_latest_workout_id(username)
    if not short_id:
        logger.error(f"Could not find latest workout for {username}.")
        return None
        
    logger.info(f"Found latest workout short_id: {short_id}")
    
    url2 = f"https://api.hevyapp.com/workout/{short_id}"
    headers2 = HEADERS.copy()
    headers2['x-client-time'] = str(time.time())
    
    resp2 = requests.get(url2, headers=headers2, timeout=10)
    if resp2.status_code != 200:
        logger.error(f"Failed to fetch workout details: {resp2.status_code}")
        return None
        
    workout_data = resp2.json()
    logger.info(f"Successfully fetched workout details for {short_id}.")
    
    return format_workout_data(workout_data)

def format_workout_data(workout: dict) -> dict:
    def ts_to_iso(ts):
        if not ts: return ""
        if isinstance(ts, (int, float)):
            return datetime.utcfromtimestamp(ts).isoformat() + "Z"
        return ts

    w = workout.copy()
    if "name" in w and "title" not in w:
        w["title"] = w["name"]
        
    w["start_time"] = ts_to_iso(w.get("start_time"))
    w["end_time"] = ts_to_iso(w.get("end_time"))
    w["create_at"] = ts_to_iso(w.get("create_at"))
    w["updated_at"] = ts_to_iso(w.get("updated_at"))

    if "exercises" in w:
        for ex in w["exercises"]:
            if "name" in ex and "title" not in ex:
                ex["title"] = ex["name"]
            if "sets" in ex:
                for s in ex["sets"]:
                    if "indicator" in s and "type" not in s:
                        s["type"] = s["indicator"]
                    s["completed_at"] = ts_to_iso(s.get("completed_at"))
    return w

@router.get("/v1/workouts/count")
def get_workout_count():
    username = get_target_username()
    if not username:
        return {"workout_count": 0}
        
    workout = fetch_latest_workout()
    return {"workout_count": 1 if workout else 0}

@router.get("/v1/workouts")
def get_workouts():
    username = get_target_username()
    if not username:
        return {"page_count": 1, "events": [], "workouts": []}
        
    workout = fetch_latest_workout()
    if workout:
        return {"page_count": 1, "events": [{"workout": workout}], "workouts": [workout]}
    return {"page_count": 1, "events": [], "workouts": []}
