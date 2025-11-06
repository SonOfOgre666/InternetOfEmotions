# How Country Emotions Are Generated - Complete Explanation

## Overview
For each country (like Spain), the system analyzes **multiple Reddit posts** and aggregates them into **ONE dominant emotion** using 4 different ML algorithms. The final emotion is determined by **consensus** across these algorithms.

---

## 📊 The Pipeline: Reddit → Database → Aggregation → Display

### **Step 1: Data Collection (app.py)**
```python
# Fetch posts for Spain from regional subreddits
posts = reddit_api.search_regional_subreddits("spain", limit=100)
# Example: 10 posts found about Spain
```

### **Step 2: Individual Post Analysis (emotion_analyzer.py)**
Each post is analyzed independently by RoBERTa ML model:
```python
Post 1: "Spain's immigration policy causes concern" 
   → emotion: "anger", confidence: 0.45

Post 2: "Spanish economy shows signs of recovery"
   → emotion: "joy", confidence: 0.65

Post 3: "Valencia faces water shortages"
   → emotion: "fear", confidence: 0.50
   
... (10 posts total)
```

### **Step 3: Filter Collective Posts Only (post_database.py)**
```python
# Only analyze COLLECTIVE issues (affects many people)
# Filter out personal stories (e.g., "I visited Spain, had fun")
collective_posts = db.get_posts_by_country("spain", collective_only=True)
```

### **Step 4: Emotion Aggregation (country_emotion_aggregator.py)**
This is where **4 different algorithms** vote on the dominant emotion:

---

## 🤖 The 4 Aggregation Algorithms

### **Algorithm 1: Majority Vote** (Simple Democracy)
- **Logic**: Most common emotion wins
- **Best for**: Clear consensus scenarios
- **Example**:
  ```
  anger: 3 posts
  fear: 3 posts
  disgust: 2 posts
  neutral: 2 posts
  
  Result: anger (30% of posts) - alphabetically first when tied
  ```

### **Algorithm 2: Weighted Vote** (Confidence-Based)
- **Logic**: Weight each emotion by average confidence of posts
- **Best for**: Mixed confidence levels
- **Formula**: `avg_confidence × frequency_weight`
- **Example**:
  ```
  anger:   (0.45 + 0.38 + 0.42) / 3 = 0.417 avg × 0.30 freq = 0.125
  fear:    (0.50 + 0.48 + 0.52) / 3 = 0.500 avg × 0.30 freq = 0.150 ✓
  disgust: (0.35 + 0.40) / 2       = 0.375 avg × 0.20 freq = 0.075
  neutral: (0.30 + 0.32) / 2       = 0.310 avg × 0.20 freq = 0.062
  
  Result: fear (highest weighted score)
  ```

### **Algorithm 3: Intensity Vote** (Emotion Strength)
- **Logic**: Stronger emotions (anger, fear) get priority over weak emotions (neutral)
- **Best for**: Identifying strong collective emotions
- **Intensity Weights**:
  ```python
  anger:    0.95  # Strongest
  fear:     0.90
  disgust:  0.85
  joy:      0.80
  sadness:  0.70
  surprise: 0.60
  neutral:  0.30  # Weakest
  ```
- **Formula**: `intensity × confidence × frequency`
- **Example**:
  ```
  anger:   0.95 × 0.417 × 3 posts = 1.188
  fear:    0.90 × 0.500 × 3 posts = 1.350 ✓
  disgust: 0.85 × 0.375 × 2 posts = 0.638
  neutral: 0.30 × 0.310 × 2 posts = 0.186
  
  Result: fear (highest intensity score)
  ```

### **Algorithm 4: Median Intensity Vote** (Robust to Outliers)
- **Logic**: Uses median instead of sum to avoid extreme values
- **Best for**: Robustness when some posts have unusual confidence
- **Formula**: `median(intensity × confidence) per emotion`
- **Example**:
  ```
  anger:   median([0.43, 0.36, 0.40]) = 0.40
  fear:    median([0.45, 0.43, 0.47]) = 0.45 ✓
  disgust: median([0.30, 0.34])       = 0.32
  neutral: median([0.09, 0.10])       = 0.095
  
  Result: fear (highest median score)
  ```

---

## 🎯 Final Decision: Ensemble Consensus

After all 4 algorithms vote, the system uses **majority consensus**:

```python
Algorithm Results:
  1. Majority Vote:          anger
  2. Weighted Vote:          fear
  3. Intensity Vote:         fear
  4. Median Intensity Vote:  fear

Consensus: fear wins (3/4 algorithms)
```

**BUT** - in your Spain example, the output shows **anger won**. This means:
- Either anger had higher confidence values in the actual data
- Or anger won in 3/4 algorithms due to the intensity weighting

---

## 📈 Spain Example (From Your Output)

```
Input Data:
  Total Posts: 10
  anger: 3 posts
  disgust: 2 posts
  fear: 3 posts
  neutral: 2 posts

Algorithm Votes:
  Intensity Vote:        anger ✓
  Median Intensity Vote: anger ✓
  Majority Vote:         fear
  Weighted Vote:         anger ✓

Final Result: anger (3/4 algorithms agreed)
Confidence: 41%
```

---

## 🔍 Confidence Calculation

The final confidence score (41% for Spain) is calculated as:

```python
def _calculate_confidence(emotion, distribution, confidences):
    # Agreement: % of posts with dominant emotion
    agreement = emotion_count / total_posts  # 3/10 = 0.30
    
    # Average confidence of all posts
    avg_confidence = mean(confidences)  # ~0.41
    
    # Combined confidence (weighted)
    confidence = (agreement × 0.6) + (avg_confidence × 0.4)
    # = (0.30 × 0.6) + (0.41 × 0.4) = 0.18 + 0.164 = 0.344 ≈ 34%
    
    return confidence
```

**Note**: Your Spain shows 41% confidence, which suggests:
- Higher average confidence in anger posts
- Or more anger posts than my simulation

---

## 📊 How It Appears in the Frontend

The frontend receives this JSON from `/api/country/Spain`:

```json
{
  "country": "spain",
  "country_emotion": {
    "dominant_emotion": "anger",
    "confidence": 0.41,
    "method": "ensemble_aggregation",
    "total_posts": 10,
    "distribution": {
      "anger": 3,
      "disgust": 2,
      "fear": 3,
      "neutral": 2
    },
    "algorithm_votes": {
      "majority": ["fear", 0.30],
      "weighted": ["anger", 0.150],
      "intensity": ["anger", 0.402],
      "intensity_median": ["anger", 0.357]
    },
    "details": {
      "total_emotions_analyzed": 10,
      "average_confidence": 0.41,
      "algorithm_consensus": {
        "Intensity Vote": "anger",
        "Median Intensity Vote": "anger",
        "Majority Vote": "fear",
        "Weighted Vote": "anger"
      }
    }
  },
  "top_events": [
    {
      "title": "General Discussion",
      "count": 10,
      "summary": "Spain will gain 600,000 immigrants this year..."
    }
  ]
}
```

The frontend then displays:
```
😠 ANGER
📍 Spain
Confidence: 41%
Analysis Method: ensemble_aggregation
Total Posts Analyzed: 10

Emotion Distribution:
😠 anger: 3
🤢 disgust: 2
😰 fear: 3
😐 neutral: 2

Algorithm Consensus:
Intensity Vote: anger
Median Intensity Vote: anger
Majority Vote: fear
Weighted Vote: anger
```

---

## 🎓 Why This Approach?

### **Problem**: Individual posts can be noisy
- One viral post doesn't represent a country
- Some posts have low confidence
- Mix of personal vs collective issues

### **Solution**: Ensemble of 4 algorithms
- **Majority Vote**: Democratic (most common wins)
- **Weighted Vote**: Trust high-confidence posts more
- **Intensity Vote**: Prioritize strong emotions over neutral
- **Median Vote**: Robust to outliers

### **Result**: Reliable country-level emotion
- Combines multiple perspectives
- Filters out noise
- Focuses on collective issues only
- Confidence score shows reliability

---

## 🔧 Code Flow Summary

```
1. app.py (Flask Backend)
   ↓
2. /api/country/<spain>
   ↓
3. db.get_country_aggregated_emotion("spain")
   ↓
4. db.get_posts_by_country("spain", collective_only=True)
   ↓ (10 posts returned)
5. aggregator.aggregate_country_emotions(posts)
   ↓
6. Run 4 algorithms:
   - majority_vote()
   - weighted_vote()
   - intensity_weighted_vote()
   - intensity_median_vote()
   ↓
7. consensus_emotion() → anger (3/4 votes)
   ↓
8. calculate_confidence() → 41%
   ↓
9. Return JSON to frontend
   ↓
10. Frontend displays: "😠 ANGER - 41% confidence"
```

---

## 🧪 Testing It Yourself

You can test the aggregation logic directly:

```bash
cd /home/SonOfOgre/Desktop/Emotion/backend
source ../.venv/bin/activate
python country_emotion_aggregator.py
```

Or programmatically:
```python
from country_emotion_aggregator import CountryEmotionAggregator

spain_posts = [
    {'emotion': 'anger', 'confidence': 0.45},
    {'emotion': 'anger', 'confidence': 0.38},
    {'emotion': 'anger', 'confidence': 0.42},
    # ... more posts
]

aggregator = CountryEmotionAggregator()
result = aggregator.aggregate_country_emotions(spain_posts)

print(f"Dominant: {result['dominant_emotion']}")
print(f"Confidence: {result['confidence']}")
print(f"Algorithm Votes: {result['algorithm_votes']}")
```

---

## 🎯 Key Takeaways

1. **Multiple posts** → **ONE dominant emotion** per country
2. **4 algorithms** vote → **consensus** determines winner
3. **Intensity matters**: Anger (0.95) > Neutral (0.30)
4. **Collective only**: Personal stories filtered out
5. **Confidence score**: Shows reliability of the result
6. **Transparent**: Frontend shows all algorithm votes

This ensures the map displays **reliable, country-level emotions** rather than random individual posts! 🌍
