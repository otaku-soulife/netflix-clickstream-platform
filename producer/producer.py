"""
Synthetic Netflix-style clickstream producer -> Azure Event Hubs.

Faithful Python port of the original Mockingbird/PowerShell generator, with two
deliberate changes:
  1. FIXED CUSTOMER BASE - a bounded pool of customers is created once at start
     (NUM_CUSTOMERS). Each has a stable user_id, profiles, plan, location,
     language, and devices. Events reuse these instead of inventing a new user
     every time (the old script used a fresh GUID per event = infinite users).
  2. REPEATING TITLES - events are drawn from a fixed 75-title catalog, so the
     same movies/series recur (matches the original catalog behavior).

Config via environment variables (injected from Key Vault in the cloud):
  EVENTHUB_CONNECTION_STRING   required - producer SAS connection string
  EVENTHUB_NAME                optional - default "netflix-clickstream"
  EVENTS_PER_SECOND            optional - target rate (default 10)
  BATCH_SIZE                   optional - events per send (default 10)
  NUM_CUSTOMERS                optional - size of the fixed customer pool (default 500)
  RANDOM_SEED                  optional - set for reproducible customers/data
"""

import json
import os
import random
import signal
import time
import uuid
from datetime import datetime, timezone

from azure.eventhub import EventData, EventHubProducerClient

# ----------------------------- Config -----------------------------
CONN_STR = os.environ["EVENTHUB_CONNECTION_STRING"]
EVENTHUB_NAME = os.environ.get("EVENTHUB_NAME", "netflix-clickstream")
EPS = float(os.environ.get("EVENTS_PER_SECOND", "10"))
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "10"))
NUM_CUSTOMERS = int(os.environ.get("NUM_CUSTOMERS", "500"))
_SEED = os.environ.get("RANDOM_SEED")
if _SEED:
    random.seed(int(_SEED))

# ------------------------- Reference data -------------------------
# Fixed catalog: the same titles recur across events.
CATALOG = [
    {"id": 1001, "title": "The Signal Between Us", "type": "movie", "genre": "Drama", "rating": "PG-13"},
    {"id": 1002, "title": "Crown of Ash", "type": "series", "genre": "Thriller", "rating": "TV-MA"},
    {"id": 1003, "title": "Deep Blue Frontier", "type": "documentary", "genre": "Documentary", "rating": "PG"},
    {"id": 1004, "title": "Midnight in Kyoto", "type": "movie", "genre": "Romance", "rating": "PG-13"},
    {"id": 1005, "title": "The Last Cartographer", "type": "series", "genre": "Sci-Fi", "rating": "TV-14"},
    {"id": 1006, "title": "Wildfire Season", "type": "documentary", "genre": "Documentary", "rating": "PG"},
    {"id": 1007, "title": "Glass Horizon", "type": "movie", "genre": "Sci-Fi", "rating": "PG-13"},
    {"id": 1008, "title": "The Undertow", "type": "series", "genre": "Thriller", "rating": "TV-MA"},
    {"id": 1009, "title": "Echoes of Everest", "type": "documentary", "genre": "Documentary", "rating": "G"},
    {"id": 1010, "title": "Paper Moons", "type": "movie", "genre": "Comedy", "rating": "PG"},
    {"id": 1011, "title": "Nine Lives of Marlowe", "type": "series", "genre": "Comedy", "rating": "TV-PG"},
    {"id": 1012, "title": "Static and Steel", "type": "movie", "genre": "Action", "rating": "R"},
    {"id": 1013, "title": "The Quiet Coast", "type": "movie", "genre": "Drama", "rating": "PG-13"},
    {"id": 1014, "title": "Vantage Point Zero", "type": "series", "genre": "Action", "rating": "TV-14"},
    {"id": 1015, "title": "Borrowed Time", "type": "movie", "genre": "Romance", "rating": "PG-13"},
    {"id": 1016, "title": "The Fractured Sky", "type": "series", "genre": "Sci-Fi", "rating": "TV-14"},
    {"id": 1017, "title": "Salt and Ceremony", "type": "movie", "genre": "Drama", "rating": "R"},
    {"id": 1018, "title": "Ashes of Meridian", "type": "series", "genre": "Fantasy", "rating": "TV-14"},
    {"id": 1019, "title": "The Hollow Choir", "type": "movie", "genre": "Horror", "rating": "R"},
    {"id": 1020, "title": "Concrete Bloom", "type": "documentary", "genre": "Documentary", "rating": "PG"},
    {"id": 1021, "title": "Rin's Firefly Diaries", "type": "series", "genre": "Anime", "rating": "TV-14"},
    {"id": 1022, "title": "Blade of the Hollow Moon", "type": "series", "genre": "Anime", "rating": "TV-MA"},
    {"id": 1023, "title": "Starlight Cram School", "type": "series", "genre": "Anime", "rating": "TV-PG"},
    {"id": 1024, "title": "The Iron Sparrow Squadron", "type": "series", "genre": "Anime", "rating": "TV-14"},
    {"id": 1025, "title": "Whisker & Wire", "type": "movie", "genre": "Anime", "rating": "TV-Y7"},
    {"id": 1026, "title": "Ten Thousand Cherry Blossoms", "type": "movie", "genre": "Anime", "rating": "PG"},
    {"id": 1027, "title": "Shrine of the Drifting Stars", "type": "series", "genre": "Anime", "rating": "TV-14"},
    {"id": 1028, "title": "Neon Ronin", "type": "series", "genre": "Anime", "rating": "TV-MA"},
    {"id": 1029, "title": "The Clockmaker's Apprentice", "type": "movie", "genre": "Anime", "rating": "TV-PG"},
    {"id": 1030, "title": "Paper Crane Academy", "type": "series", "genre": "Anime", "rating": "TV-Y7"},
    {"id": 1031, "title": "Ghosts of the Inland Sea", "type": "series", "genre": "Anime", "rating": "TV-14"},
    {"id": 1032, "title": "Voltage Sisters", "type": "series", "genre": "Anime", "rating": "TV-PG"},
    {"id": 1033, "title": "The Last Train to Amaterasu", "type": "movie", "genre": "Anime", "rating": "PG-13"},
    {"id": 1034, "title": "Crimson Koi Detective", "type": "series", "genre": "Anime", "rating": "TV-14"},
    {"id": 1035, "title": "Lantern Festival Rebellion", "type": "movie", "genre": "Anime", "rating": "TV-MA"},
    {"id": 1036, "title": "The Sixth Seal", "type": "movie", "genre": "Horror", "rating": "R"},
    {"id": 1037, "title": "Marigold Station", "type": "series", "genre": "Drama", "rating": "TV-14"},
    {"id": 1038, "title": "The Cartography of Grief", "type": "documentary", "genre": "Documentary", "rating": "PG-13"},
    {"id": 1039, "title": "Low Tide Confessions", "type": "movie", "genre": "Romance", "rating": "R"},
    {"id": 1040, "title": "The Architects of Nowhere", "type": "series", "genre": "Sci-Fi", "rating": "TV-14"},
    {"id": 1041, "title": "Rust Belt Renaissance", "type": "documentary", "genre": "Documentary", "rating": "PG"},
    {"id": 1042, "title": "The Understudy", "type": "movie", "genre": "Drama", "rating": "PG-13"},
    {"id": 1043, "title": "Feral Hour", "type": "series", "genre": "Thriller", "rating": "TV-MA"},
    {"id": 1044, "title": "The Orchard at Dusk", "type": "movie", "genre": "Romance", "rating": "PG-13"},
    {"id": 1045, "title": "Static Choir", "type": "series", "genre": "Sci-Fi", "rating": "TV-14"},
    {"id": 1046, "title": "The Locksmith's Daughter", "type": "movie", "genre": "Thriller", "rating": "R"},
    {"id": 1047, "title": "Winter Palace Heist", "type": "series", "genre": "Action", "rating": "TV-14"},
    {"id": 1048, "title": "The Last Lighthouse Keeper", "type": "movie", "genre": "Drama", "rating": "PG"},
    {"id": 1049, "title": "Backroad Prophets", "type": "documentary", "genre": "Documentary", "rating": "PG-13"},
    {"id": 1050, "title": "The Marrow of Winter", "type": "series", "genre": "Fantasy", "rating": "TV-14"},
    {"id": 1051, "title": "Kitsune Delivery Service", "type": "series", "genre": "Anime", "rating": "TV-Y7"},
    {"id": 1052, "title": "The Forge of Nine Suns", "type": "series", "genre": "Anime", "rating": "TV-14"},
    {"id": 1053, "title": "Paper Lantern Detectives", "type": "series", "genre": "Anime", "rating": "TV-PG"},
    {"id": 1054, "title": "Moonlit Rail Academy", "type": "movie", "genre": "Anime", "rating": "TV-Y7"},
    {"id": 1055, "title": "The Silver Threshold", "type": "series", "genre": "Anime", "rating": "TV-14"},
    {"id": 1056, "title": "Origami Warfare", "type": "movie", "genre": "Anime", "rating": "TV-MA"},
    {"id": 1057, "title": "Tsubaki's Last Summer", "type": "movie", "genre": "Anime", "rating": "PG"},
    {"id": 1058, "title": "The Hundred Year Festival", "type": "series", "genre": "Anime", "rating": "TV-PG"},
    {"id": 1059, "title": "Static Shrine Maidens", "type": "series", "genre": "Anime", "rating": "TV-14"},
    {"id": 1060, "title": "The Bellmaker of Edo Bay", "type": "movie", "genre": "Anime", "rating": "PG"},
    {"id": 1061, "title": "Comet Tail Diner", "type": "series", "genre": "Comedy", "rating": "TV-PG"},
    {"id": 1062, "title": "The Understory", "type": "documentary", "genre": "Documentary", "rating": "PG"},
    {"id": 1063, "title": "Departure Gate 12", "type": "movie", "genre": "Drama", "rating": "PG-13"},
    {"id": 1064, "title": "The Fault Line Waltz", "type": "series", "genre": "Romance", "rating": "TV-14"},
    {"id": 1065, "title": "Hollow Point", "type": "movie", "genre": "Action", "rating": "R"},
    {"id": 1066, "title": "The Sommelier's Secret", "type": "series", "genre": "Comedy", "rating": "TV-PG"},
    {"id": 1067, "title": "Static Horizon Line", "type": "documentary", "genre": "Documentary", "rating": "PG"},
    {"id": 1068, "title": "The Widow's Ledger", "type": "movie", "genre": "Thriller", "rating": "R"},
    {"id": 1069, "title": "Paper Wings, Iron Cage", "type": "series", "genre": "Fantasy", "rating": "TV-14"},
    {"id": 1070, "title": "The Last Reel", "type": "movie", "genre": "Drama", "rating": "PG-13"},
    {"id": 1071, "title": "Nocturne for Strangers", "type": "series", "genre": "Romance", "rating": "TV-14"},
    {"id": 1072, "title": "The Salt Mines of Cairn", "type": "movie", "genre": "Fantasy", "rating": "PG-13"},
    {"id": 1073, "title": "Grid Failure", "type": "series", "genre": "Sci-Fi", "rating": "TV-14"},
    {"id": 1074, "title": "The Cellar Door Sessions", "type": "documentary", "genre": "Documentary", "rating": "PG-13"},
    {"id": 1075, "title": "Everything After Midnight", "type": "movie", "genre": "Drama", "rating": "R"},
]

EVENT_TYPES = ["play_heartbeat", "click_thumbnail", "pause", "stop", "search_query", "error"]
EVENT_WEIGHTS = [65, 15, 8, 5, 5, 2]
SUBSCRIPTION_PLANS = ["Basic", "Standard", "Premium"]
SUBSCRIPTION_WEIGHTS = [30, 40, 30]
DEVICE_TYPES = ["SmartTV", "Mobile_iOS", "Mobile_Android", "Web_Browser", "Roku"]
DEVICE_WEIGHTS = [45, 25, 15, 10, 5]
APP_VERSIONS = ["8.1.0", "8.2.3", "9.0.1", "9.1.0"]
APP_VERSION_WEIGHTS = [10, 20, 30, 40]
CONNECTION_TYPES = ["wifi", "cellular", "ethernet"]
CONNECTION_WEIGHTS = [60, 25, 15]
VIDEO_QUALITIES = ["SD", "HD", "4K"]
QUALITY_WEIGHTS = [15, 55, 30]
COUNTRIES = ["US", "GB", "CA", "DE", "FR", "BR", "IN", "JP", "AU", "MX"]
CITIES = ["Austin", "London", "Toronto", "Berlin", "Paris", "Sao Paulo", "Mumbai", "Tokyo", "Sydney", "Mexico City"]
LANGUAGES = ["en", "es", "fr", "de", "pt", "ja"]
LANGUAGE_WEIGHTS = [50, 15, 10, 10, 10, 5]
REFERRER_SOURCES = ["homepage", "search", "recommendation", "continue_watching", "social"]
REFERRER_WEIGHTS = [30, 20, 25, 20, 5]
SEARCH_ENGINES = ["google.com", "bing.com", "duckduckgo.com", "yahoo.com"]
ERROR_CODES = ["", "ERR_BUFFER_TIMEOUT", "ERR_LICENSE_EXPIRED", "ERR_NETWORK"]
ERROR_WEIGHTS = [90, 4, 3, 3]
SEARCH_TERMS = ["action movies", "new releases", "best comedies", "documentaries 2026", "kids shows", "true crime", "sci-fi series"]
OS_BY_DEVICE = {
    "SmartTV": ["tvOS"],
    "Mobile_iOS": ["iOS"],
    "Mobile_Android": ["Android"],
    "Web_Browser": ["Windows", "macOS", "Linux"],
    "Roku": ["tvOS"],
}


def wchoice(values, weights):
    return random.choices(values, weights=weights, k=1)[0]


def build_customers(n):
    """Create the fixed customer base once. Each customer keeps stable identity,
    plan, location, language, profiles, and a small set of devices."""
    customers = []
    for _ in range(n):
        idx = random.randrange(len(COUNTRIES))  # pairs country + city
        devices = []
        for _d in range(random.randint(1, 3)):
            dtype = wchoice(DEVICE_TYPES, DEVICE_WEIGHTS)
            devices.append(
                {
                    "device_id": str(uuid.uuid4()),
                    "device_type": dtype,
                    "operating_system": random.choice(OS_BY_DEVICE[dtype]),
                }
            )
        customers.append(
            {
                "user_id": str(uuid.uuid4()),
                "profile_ids": [str(uuid.uuid4()) for _ in range(random.randint(1, 5))],
                "subscription_plan": wchoice(SUBSCRIPTION_PLANS, SUBSCRIPTION_WEIGHTS),
                "country": COUNTRIES[idx],
                "city": CITIES[idx],
                "language": wchoice(LANGUAGES, LANGUAGE_WEIGHTS),
                "devices": devices,
            }
        )
    return customers


def make_event(customers):
    cust = random.choice(customers)
    video = random.choice(CATALOG)
    event_type = wchoice(EVENT_TYPES, EVENT_WEIGHTS)
    is_series = video["type"] == "series"
    device = random.choice(cust["devices"])
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "user_id": cust["user_id"],
        "session_id": str(uuid.uuid4()),
        "profile_id": random.choice(cust["profile_ids"]),
        "event_type": event_type,
        "video_id": video["id"],
        "video_title": video["title"],
        "video_type": video["type"],
        "genre": video["genre"],
        "content_rating": video["rating"],
        "season_number": random.randint(1, 4) if is_series else None,
        "episode_number": random.randint(1, 11) if is_series else None,
        "subscription_plan": cust["subscription_plan"],
        "device_type": device["device_type"],
        "device_id": device["device_id"],
        "operating_system": device["operating_system"],
        "app_version": wchoice(APP_VERSIONS, APP_VERSION_WEIGHTS),
        "connection_type": wchoice(CONNECTION_TYPES, CONNECTION_WEIGHTS),
        "video_quality": wchoice(VIDEO_QUALITIES, QUALITY_WEIGHTS),
        "bitrate_kbps": random.randint(500, 24999),
        "buffering_events": random.randint(0, 4),
        "buffering_duration_ms": random.randint(0, 7999),
        "watch_duration_seconds": random.randint(0, 299),
        "playback_position_seconds": random.randint(0, 7199),
        "is_autoplay": random.randint(0, 1),
        "country": cust["country"],
        "city": cust["city"],
        "language": cust["language"],
        "search_query": random.choice(SEARCH_TERMS) if event_type == "search_query" else None,
        "search_engine": random.choice(SEARCH_ENGINES),
        "referrer_source": wchoice(REFERRER_SOURCES, REFERRER_WEIGHTS),
        "error_code": wchoice(ERROR_CODES, ERROR_WEIGHTS) if event_type == "error" else None,
    }


running = True


def _stop(*_):
    global running
    running = False


signal.signal(signal.SIGTERM, _stop)
signal.signal(signal.SIGINT, _stop)


def build_producer():
    if "EntityPath=" in CONN_STR:
        return EventHubProducerClient.from_connection_string(CONN_STR)
    return EventHubProducerClient.from_connection_string(CONN_STR, eventhub_name=EVENTHUB_NAME)


def main():
    customers = build_customers(NUM_CUSTOMERS)
    print(f"Built {len(customers)} fixed customers; catalog has {len(CATALOG)} titles.", flush=True)
    producer = build_producer()
    interval = (BATCH_SIZE / EPS) if EPS > 0 else 1.0
    sent = 0
    print(f"Producing ~{EPS} events/sec to '{EVENTHUB_NAME}' ...", flush=True)
    with producer:
        while running:
            batch = producer.create_batch()
            for _ in range(BATCH_SIZE):
                batch.add(EventData(json.dumps(make_event(customers))))
            producer.send_batch(batch)
            sent += BATCH_SIZE
            print(f"{datetime.now(timezone.utc).strftime('%H:%M:%S')} sent {sent} events", flush=True)
            time.sleep(interval)
    print(f"Stopped. Total sent: {sent}", flush=True)


if __name__ == "__main__":
    main()
