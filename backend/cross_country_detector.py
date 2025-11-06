"""
Cross-Country Detector
Identifies countries mentioned in Reddit posts using NLP/ML
Handles cases like:
- Post in r/worldnews about India's water crisis
- Post in r/USA discussing UK politics
- Multi-country mentions in single post
"""

import re
from typing import Dict, List, Set
from transformers import pipeline

class CrossCountryDetector:
    """
    Detects country mentions in text using:
    1. Named Entity Recognition (NER) - finds country entities
    2. Keyword matching - common country references
    3. Geographic context - identifies location mentions
    """

    def __init__(self):
        print("🤖 Loading Named Entity Recognition (NER) model for country detection...")
        
        # Initialize NER model for entity detection - using working model
        try:
            self.ner_pipeline = pipeline(
                "ner",
                model="dslim/bert-base-NER",  # Better, maintained model
                grouped_entities=True,
                device=-1  # CPU
            )
            self.ner_available = True
            self.zero_shot_available = False  # Will try to load zero-shot as backup
            print("✓ NER model loaded successfully")
            
            # Try to also load zero-shot for fallback scenarios
            try:
                self.zero_shot_pipeline = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=-1
                )
                self.zero_shot_available = True
                print("✓ Zero-shot classifier also loaded as fallback")
            except Exception:
                print("  (Zero-shot fallback not available)")
                self.zero_shot_pipeline = None
                
        except Exception as e:
            print(f"⚠ NER model failed to load: {e}")
            print("  Trying alternative zero-shot approach...")
            try:
                # Fallback: Use zero-shot classification for country detection
                self.zero_shot_pipeline = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=-1
                )
                self.ner_pipeline = None
                self.ner_available = False
                self.zero_shot_available = True
                print("✓ Zero-shot classifier loaded for country detection")
            except Exception as e2:
                print(f"⚠ Zero-shot also failed: {e2}")
                print("  Using keyword-based detection only")
                self.ner_pipeline = None
                self.zero_shot_pipeline = None
                self.ner_available = False
                self.zero_shot_available = False

        # Import all countries from country_coordinates
        from country_coordinates import COUNTRY_COORDS
        
        # Generate country aliases programmatically from COUNTRY_COORDS
        # Each country gets: lowercase name, capitalized name, and demonym (if known)
        self.country_aliases = {}
        
        # Add all countries from COUNTRY_COORDS (auto-generated)
        for country_name in COUNTRY_COORDS.keys():
            country_lower = country_name.lower()
            # Each country gets its lowercase version as the key
            self.country_aliases[country_lower] = [country_lower, country_name.lower()]
        
        # Add manual aliases for countries with special names/demonyms
        manual_aliases = {
            # Americas
            'usa': ['usa', 'us', 'united states', 'america', 'american', 'u.s.', 'u.s.a.', 'united states of america'],
            'united states': ['usa', 'us', 'united states', 'america', 'american', 'u.s.', 'u.s.a.'],
            'uk': ['uk', 'united kingdom', 'britain', 'british', 'england', 'scotland', 'wales', 'great britain'],
            'united kingdom': ['uk', 'united kingdom', 'britain', 'british', 'england', 'scotland', 'wales'],
            'canada': ['canada', 'canadian'],
            'mexico': ['mexico', 'mexican'],
            'brazil': ['brazil', 'brasil', 'brazilian'],
            'argentina': ['argentina', 'argentine', 'argentinian'],
            
            # Europe
            'france': ['france', 'french'],
            'germany': ['germany', 'german', 'deutschland'],
            'spain': ['spain', 'spanish', 'españa'],
            'italy': ['italy', 'italian', 'italia'],
            'russia': ['russia', 'russian', 'rossiya'],
            'poland': ['poland', 'polish', 'polska'],
            'ukraine': ['ukraine', 'ukrainian', 'ukraina'],
            'netherlands': ['netherlands', 'dutch', 'holland'],
            'sweden': ['sweden', 'swedish'],
            'norway': ['norway', 'norwegian', 'norge'],
            'denmark': ['denmark', 'danish'],
            'finland': ['finland', 'finnish'],
            'greece': ['greece', 'greek', 'hellas'],
            'portugal': ['portugal', 'portuguese'],
            'belgium': ['belgium', 'belgian'],
            'austria': ['austria', 'austrian'],
            'switzerland': ['switzerland', 'swiss'],
            'ireland': ['ireland', 'irish'],
            'czech republic': ['czech', 'czechia', 'czech republic'],
            'czechia': ['czech', 'czechia', 'czech republic'],
            'hungary': ['hungary', 'hungarian'],
            'romania': ['romania', 'romanian'],
            'bulgaria': ['bulgaria', 'bulgarian'],
            'serbia': ['serbia', 'serbian', 'srbija'],
            'croatia': ['croatia', 'croatian'],
            'slovenia': ['slovenia', 'slovenian'],
            'albania': ['albania', 'albanian'],
            'montenegro': ['montenegro', 'montenegrin'],
            'bosnia and herzegovina': ['bosnia', 'bosnia and herzegovina', 'bosnian'],
            'north macedonia': ['macedonia', 'north macedonia', 'macedonian'],
            'kosovo': ['kosovo', 'kosovar'],
            
            # Asia
            'india': ['india', 'indian', 'bharat'],
            'china': ['china', 'chinese', 'prc'],
            'japan': ['japan', 'japanese'],
            'south korea': ['south korea', 'korea', 'korean', 'republic of korea', 'rok'],
            'north korea': ['north korea', 'dprk', 'democratic people\'s republic of korea'],
            'pakistan': ['pakistan', 'pakistani'],
            'bangladesh': ['bangladesh', 'bangladeshi'],
            'thailand': ['thailand', 'thai'],
            'vietnam': ['vietnam', 'vietnamese'],
            'indonesia': ['indonesia', 'indonesian'],
            'philippines': ['philippines', 'philippine', 'pilipinas', 'filipino'],
            'malaysia': ['malaysia', 'malaysian'],
            'singapore': ['singapore', 'singaporean'],
            'sri lanka': ['sri lanka', 'ceylon', 'sri lankan'],
            'afghanistan': ['afghanistan', 'afghan'],
            'iran': ['iran', 'persia', 'persian', 'iranian'],
            'iraq': ['iraq', 'iraqi'],
            'syria': ['syria', 'syrian'],
            'saudi arabia': ['saudi arabia', 'saudi', 'saudis', 'saudi arabian'],
            'israel': ['israel', 'israeli'],
            'palestine': ['palestine', 'palestinian'],
            'jordan': ['jordan', 'jordanian'],
            'lebanon': ['lebanon', 'lebanese'],
            'turkey': ['turkey', 'turkish', 'turkiye', 'türkiye'],
            'uae': ['uae', 'united arab emirates', 'emirates', 'emirati'],
            'united arab emirates': ['uae', 'united arab emirates', 'emirates', 'emirati'],
            'kuwait': ['kuwait', 'kuwaiti'],
            'qatar': ['qatar', 'qatari'],
            'bahrain': ['bahrain', 'bahraini'],
            'yemen': ['yemen', 'yemeni'],
            'oman': ['oman', 'omani'],
            'kazakhstan': ['kazakhstan', 'kazakh'],
            'uzbekistan': ['uzbekistan', 'uzbek'],
            'turkmenistan': ['turkmenistan', 'turkmen'],
            'tajikistan': ['tajikistan', 'tajik'],
            'kyrgyzstan': ['kyrgyzstan', 'kyrgyz'],
            'mongolia': ['mongolia', 'mongolian'],
            'cambodia': ['cambodia', 'khmer', 'cambodian'],
            'laos': ['laos', 'lao', 'laotian'],
            'myanmar': ['myanmar', 'burma', 'burmese'],
            'nepal': ['nepal', 'nepalese', 'nepali'],
            'armenia': ['armenia', 'armenian'],
            'azerbaijan': ['azerbaijan', 'azerbaijani', 'azeri'],
            'georgia': ['georgia', 'georgian'],
            
            # Africa
            'egypt': ['egypt', 'egyptian'],
            'south africa': ['south africa', 'south african'],
            'nigeria': ['nigeria', 'nigerian'],
            'kenya': ['kenya', 'kenyan'],
            'uganda': ['uganda', 'ugandan'],
            'tanzania': ['tanzania', 'tanzanian'],
            'ethiopia': ['ethiopia', 'ethiopian'],
            'algeria': ['algeria', 'algerian'],
            'morocco': ['morocco', 'moroccan'],
            'tunisia': ['tunisia', 'tunisian'],
            'libya': ['libya', 'libyan'],
            'ghana': ['ghana', 'ghanaian'],
            'senegal': ['senegal', 'senegalese'],
            'cameroon': ['cameroon', 'cameroonian'],
            'congo': ['congo', 'congolese'],
            'democratic republic of the congo': ['drc', 'democratic republic of congo', 'congo kinshasa', 'dr congo'],
            'drc': ['drc', 'democratic republic of congo', 'congo kinshasa', 'dr congo'],
            'sudan': ['sudan', 'sudanese'],
            'south sudan': ['south sudan', 'south sudanese'],
            'somalia': ['somalia', 'somali', 'somalian'],
            'zimbabwe': ['zimbabwe', 'zimbabwean'],
            'angola': ['angola', 'angolan'],
            'mozambique': ['mozambique', 'mozambican'],
            'benin': ['benin', 'beninese'],
            'mali': ['mali', 'malian'],
            'niger': ['niger', 'nigerien'],
            'chad': ['chad', 'chadian'],
            
            # Oceania
            'australia': ['australia', 'australian', 'aussie'],
            'new zealand': ['new zealand', 'nz', 'kiwi', 'aotearoa'],
            'fiji': ['fiji', 'fijian'],
            'samoa': ['samoa', 'samoan'],
            'papua new guinea': ['papua new guinea', 'png', 'papua'],
        }
        
        # Merge manual aliases with auto-generated ones
        for country, aliases in manual_aliases.items():
            if country in self.country_aliases:
                # Merge with existing
                self.country_aliases[country] = list(set(self.country_aliases[country] + aliases))
            else:
                self.country_aliases[country] = aliases

        # Build reverse lookup (keyword -> country)
        self.keyword_to_country = {}
        for country, keywords in self.country_aliases.items():
            for keyword in keywords:
                self.keyword_to_country[keyword.lower()] = country

        # Capital cities (for additional context)
        self.capital_cities = {
            'washington': 'usa',
            'london': 'uk',
            'paris': 'france',
            'berlin': 'germany',
            'moscow': 'russia',
            'beijing': 'china',
            'tokyo': 'japan',
            'delhi': 'india',
            'cairo': 'egypt',
            'sydney': 'australia',
            'toronto': 'canada',
            'mexico city': 'mexico',
            'buenos aires': 'argentina',
            'são paulo': 'brazil',
            'sao paulo': 'brazil',
            'manila': 'philippines',
            'bangkok': 'thailand',
            'istanbul': 'turkey',
            'dubai': 'uae',
            'singapore': 'singapore',
            'hong kong': 'hong kong',
            'bangkok': 'thailand',
        }

    def detect_countries(self, text: str, mention_context: bool = True) -> Dict:
        """
        Detect countries mentioned in text
        
        Returns: {
            'countries': [list of countries],
            'primary_country': str (most prominently mentioned),
            'confidence': float,
            'mentions': {
                'usa': {'count': 5, 'contexts': ['water crisis', 'policy']},
                ...
            },
            'method': str
        }
        """
        if not text or len(text.strip()) < 5:
            return self._empty_result()

        detected_countries = set()
        country_mentions = {}
        methods_used = []

        # Method 1: NER-based detection
        if self.ner_available:
            ner_countries = self._detect_with_ner(text)
            detected_countries.update(ner_countries)
            if ner_countries:
                methods_used.append('NER')

        # Method 2: Zero-shot classification (fallback if NER fails or finds nothing)
        if not detected_countries and self.zero_shot_available:
            zero_shot_countries = self._detect_with_zero_shot(text)
            detected_countries.update(zero_shot_countries)
            if zero_shot_countries:
                methods_used.append('zero-shot')

        # Method 3: Keyword matching
        keyword_countries = self._detect_with_keywords(text)
        detected_countries.update(keyword_countries)
        if keyword_countries:
            methods_used.append('keyword')

        # Method 3: Capital city detection
        capital_countries = self._detect_by_capitals(text)
        detected_countries.update(capital_countries)
        if capital_countries:
            methods_used.append('capitals')

        # Count mentions per country
        for country in detected_countries:
            count = self._count_country_mentions(text, country)
            country_mentions[country] = {
                'count': count,
                'frequency': count / len(text.split())
            }

        # Sort by frequency
        sorted_mentions = sorted(
            country_mentions.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )

        # Primary country (most mentioned)
        primary_country = sorted_mentions[0][0] if sorted_mentions else None

        # Confidence based on agreement between methods
        confidence = self._calculate_confidence(
            len(detected_countries),
            len(methods_used),
            country_mentions
        )

        return {
            'countries': list(detected_countries),
            'primary_country': primary_country,
            'confidence': round(confidence, 2),
            'mentions': dict(sorted_mentions),
            'method': '+'.join(methods_used) if methods_used else 'none',
            'total_methods': len(methods_used),
            'mention_count': len(detected_countries)
        }

    def _detect_with_ner(self, text: str) -> Set[str]:
        """Use NER to find location entities"""
        if not self.ner_available:
            return set()

        try:
            # Truncate to 512 tokens (BERT max)
            text_truncated = text[:512]
            entities = self.ner_pipeline(text_truncated)
            
            countries = set()
            for entity in entities:
                if entity['entity_group'] == 'LOC':  # Location entity
                    location = entity['word'].lower()
                    
                    # Match with known countries
                    if location in self.keyword_to_country:
                        countries.add(self.keyword_to_country[location])

            return countries

        except Exception as e:
            return set()

    def _detect_with_zero_shot(self, text: str) -> Set[str]:
        """Use zero-shot classification to detect country mentions
        
        This method is used as a fallback when NER fails or finds nothing.
        It uses semantic understanding to identify if text is discussing specific countries.
        """
        if not self.zero_shot_available:
            return set()

        try:
            # Truncate to avoid memory issues
            text_truncated = text[:1024]
            
            countries = set()
            
            # Create hypothesis for each country
            # Test top 20 most common countries to avoid excessive API calls
            common_countries = [
                'usa', 'uk', 'canada', 'australia', 'india', 'china', 'germany',
                'france', 'japan', 'brazil', 'russia', 'mexico', 'spain', 'italy',
                'south korea', 'turkey', 'israel', 'pakistan', 'egypt', 'nigeria'
            ]
            
            for country in common_countries:
                hypothesis = f"This text is about {country}."
                result = self.zero_shot_pipeline(text_truncated, candidate_labels=[hypothesis])
                
                # If confidence > 0.5, consider it a mention
                if result['scores'][0] > 0.5:
                    countries.add(country)
            
            return countries

        except Exception as e:
            return set()

    def _detect_with_keywords(self, text: str) -> Set[str]:
        """Match country keywords in text"""
        text_lower = text.lower()
        countries = set()

        for keyword, country in self.keyword_to_country.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                countries.add(country)

        return countries

    def _detect_by_capitals(self, text: str) -> Set[str]:
        """Detect countries by their capital cities"""
        text_lower = text.lower()
        countries = set()

        for capital, country in self.capital_cities.items():
            pattern = r'\b' + re.escape(capital) + r'\b'
            if re.search(pattern, text_lower):
                countries.add(country)

        return countries

    def _count_country_mentions(self, text: str, country: str) -> int:
        """Count how many times a country is mentioned in text"""
        text_lower = text.lower()
        count = 0

        # Count all keywords for this country
        if country in self.country_aliases:
            for keyword in self.country_aliases[country]:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                count += len(re.findall(pattern, text_lower))

        # Also count capital if available
        for capital, c in self.capital_cities.items():
            if c == country:
                pattern = r'\b' + re.escape(capital) + r'\b'
                count += len(re.findall(pattern, text_lower))

        return count

    def _calculate_confidence(self, country_count: int, method_count: int, mentions: Dict) -> float:
        """
        Calculate confidence in country detection
        Based on:
        - Number of countries (single country = higher confidence)
        - Number of detection methods (more = higher confidence)
        - Frequency of mentions
        """
        if country_count == 0:
            return 0.0

        # Normalize by country count (more countries = lower confidence per country)
        country_score = 1.0 / (country_count + 1)

        # Method score (more methods = higher confidence)
        method_score = min(method_count / 3.0, 1.0)  # Max 3 methods

        # Frequency score (higher frequency = higher confidence)
        if mentions:
            avg_frequency = sum(m['frequency'] for m in mentions.values()) / len(mentions)
            frequency_score = min(avg_frequency * 10, 1.0)  # Scale to 0-1
        else:
            frequency_score = 0.0

        # Combined confidence
        confidence = (country_score * 0.3) + (method_score * 0.4) + (frequency_score * 0.3)

        return min(confidence, 1.0)

    def _empty_result(self) -> Dict:
        """Return empty result for no countries detected"""
        return {
            'countries': [],
            'primary_country': None,
            'confidence': 0.0,
            'mentions': {},
            'method': 'none',
            'total_methods': 0,
            'mention_count': 0
        }

    def get_cross_country_analysis(self, post_country: str, detected_countries: List[str]) -> Dict:
        """
        Analyze if a post is about another country
        
        Returns: {
            'is_cross_country': bool,
            'primary_subject': str (which country is post about),
            'source_country': str (where post was published),
            'relevance': float (0-1)
        }
        """
        if post_country not in detected_countries:
            return {
                'is_cross_country': False,
                'primary_subject': post_country,
                'source_country': post_country,
                'relevance': 1.0
            }

        # If detected countries include different countries, it's cross-country
        primary = detected_countries[0]
        is_cross = primary.lower() != post_country.lower()

        # Calculate relevance (how much about the other country vs source)
        relevance = 1.0 if is_cross else 0.5

        return {
            'is_cross_country': is_cross,
            'primary_subject': primary,
            'source_country': post_country,
            'relevance': relevance
        }


# Test
if __name__ == '__main__':
    detector = CrossCountryDetector()

    test_posts = [
        {
            'text': 'Water crisis in India affecting millions of people',
            'country': 'worldnews'
        },
        {
            'text': 'The UK election results shocked Europe',
            'country': 'usa'
        },
        {
            'text': 'China and Japan tensions escalate in the region',
            'country': 'singapore'
        },
        {
            'text': 'Beautiful weather today in New York',
            'country': 'usa'
        },
    ]

    print("Cross-Country Detection Tests:\n")
    for post in test_posts:
        result = detector.detect_countries(post['text'])
        cross_analysis = detector.get_cross_country_analysis(post['country'], result['countries'])
        
        print(f"Post Country: {post['country']}")
        print(f"Text: {post['text']}")
        print(f"Detected Countries: {result['countries']}")
        print(f"Primary: {result['primary_country']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Is Cross-Country: {cross_analysis['is_cross_country']}")
        print(f"Primary Subject: {cross_analysis['primary_subject']}\n")
