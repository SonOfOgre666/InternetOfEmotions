"""
Shared configuration for all microservices
"""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Service URLs
DATA_FETCHER_URL = os.getenv('DATA_FETCHER_URL', 'http://data-fetcher:5001')
EMOTION_ANALYZER_URL = os.getenv('EMOTION_ANALYZER_URL', 'http://emotion-analyzer:5002')
COLLECTIVE_ANALYZER_URL = os.getenv('COLLECTIVE_ANALYZER_URL', 'http://collective-analyzer:5003')
AGGREGATOR_URL = os.getenv('AGGREGATOR_URL', 'http://aggregator:5004')
API_GATEWAY_URL = os.getenv('API_GATEWAY_URL', 'http://api-gateway:5000')

# Database - Use absolute path so all microservices share the same database
DB_PATH = os.getenv('DB_PATH', os.path.join(os.path.dirname(__file__), 'posts.db'))

# Reddit API
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'EmotionsDashboard/1.0')

# Application settings
MIN_POSTS_PER_COUNTRY = int(os.getenv('MIN_POSTS_PER_COUNTRY', '1'))
MAX_POSTS_PER_COUNTRY = int(os.getenv('MAX_POSTS_PER_COUNTRY', '100'))
MAX_POST_AGE_DAYS = int(os.getenv('MAX_POST_AGE_DAYS', '28'))
REDDIT_FETCH_LIMIT = int(os.getenv('REDDIT_FETCH_LIMIT', '200'))  # Increased for faster collection
# Data fetch concurrency
DATA_FETCH_WORKERS = int(os.getenv('DATA_FETCH_WORKERS', '10'))  # More workers for parallel processing

# Regional mapping
REGIONS = {
    "europe": [
        "albania","andorra","austria","belarus","belgium","bosnia and herzegovina","bulgaria",
        "croatia","czech republic","denmark","estonia","finland","france","germany","greece",
        "hungary","iceland","ireland","italy","kosovo","latvia","liechtenstein","lithuania",
        "luxembourg","malta","moldova","monaco","montenegro","netherlands","north macedonia",
        "norway","poland","portugal","romania","russia","san marino","serbia","slovakia",
        "slovenia","spain","sweden","switzerland","ukraine","united kingdom","vatican city"
    ],
    "asia": [
        "afghanistan","armenia","azerbaijan","bangladesh","bhutan","brunei","cambodia","china",
        "georgia","india","indonesia","japan","kazakhstan","kyrgyzstan","laos","malaysia",
        "maldives","mongolia","myanmar","nepal","north korea","pakistan","philippines",
        "singapore","south korea","sri lanka","tajikistan","thailand","timor-leste","turkmenistan",
        "uzbekistan","vietnam","taiwan"
    ],
    "africa": [
        "algeria","angola","benin","botswana","burkina faso","burundi","cabo verde","cameroon",
        "central african republic","chad","comoros","congo (brazzaville)","congo (kinshasa)",
        "côte d'ivoire","djibouti","equatorial guinea","eritrea","eswatini","ethiopia","gabon",
        "gambia","ghana","guinea","guinea-bissau","kenya","lesotho","liberia","libya","madagascar",
        "malawi","mali","mauritania","mauritius","morocco","mozambique","namibia","niger","nigeria",
        "rwanda","sao tome and principe","senegal","seychelles","sierra leone","somalia",
        "south africa","south sudan","sudan","tanzania","togo","tunisia","uganda","zambia","zimbabwe"
    ],
    "americas": [
        "antigua and barbuda","argentina","bahamas","barbados","belize","bolivia","brazil","canada",
        "chile","colombia","costa rica","cuba","dominica","dominican republic","ecuador","el salvador",
        "grenada","guatemala","guyana","haiti","honduras","jamaica","mexico","nicaragua","panama",
        "paraguay","peru","saint kitts and nevis","saint lucia","saint vincent and the grenadines",
        "suriname","trinidad and tobago","united states","uruguay","venezuela"
    ],
    "oceania": [
        "australia","federated states of micronesia","fiji","kiribati","marshall islands","nauru",
        "new zealand","palau","papua new guinea","samoa","solomon islands","tonga","tuvalu","vanuatu"
    ],
    "middleeast": [
        "bahrain","cyprus","iran","iraq","israel","jordan","kuwait","lebanon","oman",
        "palestine","qatar","saudi arabia","syria","turkey","united arab emirates","yemen"
    ]
}

# Country-specific subreddits - REAL subreddits only
SUBREDDITS_BY_COUNTRY = {
    "albania":     ["albania"],
    "austria":     ["austria"],
    "belarus":     ["belarus"],
    "belgium":     ["belgium", "belgiumfs"],
    "bulgaria":    ["bulgaria"],
    "croatia":     ["croatia"],
    "czech republic":["czech"],
    "denmark":     ["denmark"],
    "estonia":     ["eesti"],
    "finland":     ["finland", "suomi"],
    "france":      ["france", "rance"],
    "germany":     ["germany", "de"],
    "greece":      ["greece"],
    "hungary":     ["hungary"],
    "iceland":     ["iceland"],
    "ireland":     ["ireland"],
    "italy":       ["italy"],
    "latvia":      ["latvia"],
    "lithuania":   ["lithuania"],
    "luxembourg":  ["luxembourg"],
    "malta":       ["malta"],
    "moldova":     ["moldova"],
    "netherlands": ["thenetherlands", "netherlands"],
    "norway":      ["norway"],
    "poland":      ["poland", "polska"],
    "portugal":    ["portugal"],
    "romania":     ["romania"],
    "russia":      ["russia"],
    "serbia":      ["serbia"],
    "slovakia":    ["slovakia"],
    "slovenia":    ["slovenia"],
    "spain":       ["spain", "es"],
    "sweden":      ["sweden"],
    "switzerland": ["switzerland"],
    "ukraine":     ["ukraine"],
    "united kingdom":["unitedkingdom", "ukpolitics"],
    "china":       ["china", "sino"],
    "india":       ["india", "indiaspeaks"],
    "indonesia":   ["indonesia"],
    "japan":       ["japan", "japanlife"],
    "south korea": ["korea", "hanguk"],
    "malaysia":    ["malaysia"],
    "pakistan":    ["pakistan"],
    "philippines": ["philippines"],
    "singapore":   ["singapore"],
    "thailand":    ["thailand"],
    "vietnam":     ["vietnam"],
    "taiwan":      ["taiwan"],
    "bangladesh":  ["bangladesh"],
    "sri lanka":   ["srilanka"],
    "myanmar":     ["myanmar", "burma"],
    "egypt":       ["egypt"],
    "south africa":["southafrica"],
    "nigeria":     ["nigeria"],
    "kenya":       ["kenya"],
    "ethiopia":    ["ethiopia"],
    "morocco":     ["morocco"],
    "argentina":   ["argentina"],
    "brazil":      ["brazil"],
    "canada":      ["canada", "onguardforthee"],
    "chile":       ["chile"],
    "colombia":    ["colombia"],
    "mexico":      ["mexico"],
    "peru":        ["peru"],
    "venezuela":   ["venezuela", "vzla"],
    "united states":["politics", "news"],
    "australia":   ["australia", "straya"],
    "new zealand": ["newzealand"],
    "iran":        ["iran"],
    "iraq":        ["iraq"],
    "israel":      ["israel"],
    "jordan":      ["jordan"],
    "lebanon":     ["lebanon"],
    "palestine":   ["palestine"],
    "saudi arabia":["saudiarabia"],
    "syria":       ["syria"],
    "turkey":      ["turkey"],
    "united arab emirates":["dubai", "abudhabi"]
}

REGION_SUBREDDITS = {
    "europe":     ["worldnews", "news", "europe", "geopolitics", "UpliftingNews", "UnderReportedNews", "internationalnews", "CredibleDefense", "AskTheWorld", "economics"],
    "asia":       ["worldnews", "news", "geopolitics", "asia", "UpliftingNews", "UnderReportedNews", "internationalnews", "CredibleDefense", "AskTheWorld", "economics"],
    "africa":     ["worldnews", "news", "geopolitics", "africa", "UpliftingNews", "UnderReportedNews", "internationalnews", "CredibleDefense", "AskTheWorld", "economics"],
    "americas":   ["worldnews", "news", "geopolitics", "latinamerica", "UpliftingNews", "UnderReportedNews", "internationalnews", "CredibleDefense", "AskTheWorld", "economics"],
    "oceania":    ["worldnews", "news", "geopolitics", "australia", "UpliftingNews", "UnderReportedNews", "internationalnews", "CredibleDefense", "AskTheWorld", "economics"],
    "middleeast": ["worldnews", "news", "geopolitics", "middleeast", "UpliftingNews", "UnderReportedNews", "internationalnews", "CredibleDefense", "AskTheWorld", "economics"],
}

COUNTRY_TO_REGION = {}
for region, countries in REGIONS.items():
    for country in countries:
        COUNTRY_TO_REGION[country.lower()] = region

ALL_COUNTRIES = []
for region, countries in REGIONS.items():
    ALL_COUNTRIES.extend(countries)
