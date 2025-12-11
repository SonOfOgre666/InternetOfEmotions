"""
Shared Configuration for Internet of Emotions Microservices

This module provides common configuration constants used across all services.
Import this in your service to ensure consistency.
"""

import os

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://ioe_user:password@localhost:5432/internet_of_emotions')

# ============================================================================
# MESSAGE QUEUE CONFIGURATION
# ============================================================================
RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://ioe_user:password@localhost:5672/')
RABBITMQ_EXCHANGE = 'posts_exchange'
RABBITMQ_EXCHANGE_TYPE = 'topic'

# Message routing keys
ROUTING_KEYS = {
    'POST_FETCHED': 'post.fetched',
    'URL_EXTRACTED': 'url.extracted',
    'POST_ANALYZED': 'post.analyzed',
    'COUNTRY_UPDATED': 'country.updated',
}

# ============================================================================
# CACHE CONFIGURATION
# ============================================================================
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
DEFAULT_CACHE_TTL = int(os.getenv('DEFAULT_CACHE_TTL', 300))  # 5 minutes

# ============================================================================
# SEARCH CONFIGURATION
# ============================================================================
ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')

# ============================================================================
# BUSINESS LOGIC CONSTANTS
# ============================================================================
MAX_POST_AGE_DAYS = int(os.getenv('MAX_POST_AGE_DAYS', 28))  # 4 weeks
MIN_POSTS_PER_COUNTRY = int(os.getenv('MIN_POSTS_PER_COUNTRY', 1))
MAX_POSTS_PER_COUNTRY = int(os.getenv('MAX_POSTS_PER_COUNTRY', 100))

# ============================================================================
# REDDIT API CONFIGURATION
# ============================================================================
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'InternetOfEmotions/2.0')
REDDIT_FETCH_LIMIT = int(os.getenv('REDDIT_FETCH_LIMIT', 25))

# ============================================================================
# SERVICE PORTS
# ============================================================================
SERVICE_PORTS = {
    'api_gateway': 8000,
    'post_fetcher': 5001,
    'url_extractor': 5002,
    'ml_analyzer': 5003,
    'db_cleanup': 5004,
    'country_aggregation': 5005,
    'cache_service': 5006,
    'search_service': 5007,
    'stats_service': 5008,
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'

# ============================================================================
# COUNTRIES BY REGION
# ============================================================================
REGIONS = {
    "europe": ["albania", "andorra", "austria", "belarus", "belgium", "bosnia and herzegovina",
               "bulgaria", "croatia", "czech republic", "denmark", "estonia", "finland", "france",
               "germany", "greece", "hungary", "iceland", "ireland", "italy", "kosovo", "latvia",
               "liechtenstein", "lithuania", "luxembourg", "malta", "moldova", "monaco", "montenegro",
               "netherlands", "north macedonia", "norway", "poland", "portugal", "romania", "russia",
               "san marino", "serbia", "slovakia", "slovenia", "spain", "sweden", "switzerland",
               "ukraine", "united kingdom", "vatican city"],
    "asia": ["afghanistan", "armenia", "azerbaijan", "bangladesh", "bhutan", "brunei", "cambodia",
             "china", "georgia", "india", "indonesia", "japan", "kazakhstan", "kyrgyzstan", "laos",
             "malaysia", "maldives", "mongolia", "myanmar", "nepal", "north korea", "pakistan",
             "philippines", "singapore", "south korea", "sri lanka", "tajikistan", "thailand",
             "timor-leste", "turkmenistan", "uzbekistan", "vietnam", "taiwan"],
    "africa": ["algeria", "angola", "benin", "botswana", "burkina faso", "burundi", "cabo verde",
               "cameroon", "central african republic", "chad", "comoros", "congo (brazzaville)",
               "congo (kinshasa)", "côte d'ivoire", "djibouti", "equatorial guinea", "eritrea",
               "eswatini", "ethiopia", "gabon", "gambia", "ghana", "guinea", "guinea-bissau", "kenya",
               "lesotho", "liberia", "libya", "madagascar", "malawi", "mali", "mauritania", "mauritius",
               "morocco", "mozambique", "namibia", "niger", "nigeria", "rwanda", "sao tome and principe",
               "senegal", "seychelles", "sierra leone", "somalia", "south africa", "south sudan",
               "sudan", "tanzania", "togo", "tunisia", "uganda", "zambia", "zimbabwe"],
    "americas": ["antigua and barbuda", "argentina", "bahamas", "barbados", "belize", "bolivia",
                 "brazil", "canada", "chile", "colombia", "costa rica", "cuba", "dominica",
                 "dominican republic", "ecuador", "el salvador", "grenada", "guatemala", "guyana",
                 "haiti", "honduras", "jamaica", "mexico", "nicaragua", "panama", "paraguay", "peru",
                 "saint kitts and nevis", "saint lucia", "saint vincent and the grenadines", "suriname",
                 "trinidad and tobago", "united states", "uruguay", "venezuela"],
    "oceania": ["australia", "federated states of micronesia", "fiji", "kiribati", "marshall islands",
                "nauru", "new zealand", "palau", "papua new guinea", "samoa", "solomon islands",
                "tonga", "tuvalu", "vanuatu"],
    "middleeast": ["bahrain", "cyprus", "iran", "iraq", "israel", "jordan", "kuwait", "lebanon",
                   "oman", "palestine", "qatar", "saudi arabia", "syria", "turkey",
                   "united arab emirates", "yemen"]
}

# Build reverse mapping
COUNTRY_TO_REGION = {}
ALL_COUNTRIES = []
for region, countries in REGIONS.items():
    for country in countries:
        COUNTRY_TO_REGION[country.lower()] = region
        ALL_COUNTRIES.append(country)

# ============================================================================
# REGIONAL SUBREDDITS
# ============================================================================
REGION_SUBREDDITS = {
    "europe": ["europe", "InternationalNews", "world", "worldnews", "news"],
    "asia": ["asia", "InternationalNews", "world", "worldnews", "news"],
    "africa": ["africa", "InternationalNews", "world", "worldnews", "news"],
    "americas": ["latinamerica", "InternationalNews", "world", "worldnews", "news"],
    "oceania": ["australia", "newzealand", "InternationalNews", "world", "worldnews"],
    "middleeast": ["middleeast", "InternationalNews", "world", "worldnews", "news"]
}
