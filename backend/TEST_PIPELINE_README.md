# Pipeline Testing Guide

## Overview
The `test_pipeline.py` script allows you to test each function in the emotion analysis pipeline with detailed input/output logging.

## Features
- ✅ **Separate Test Database**: Uses `test_posts.db` instead of production `posts.db`
- ✅ **Limited Test Regions**: Only 18 countries (2-4 per region) for faster testing
- ✅ **Your Reddit API**: Uses your credentials from `.env` file
- ✅ **Detailed I/O**: Shows exactly what goes into and comes out of each function
- ✅ **Color-coded Output**: Easy to read terminal output with sections

## Test Regions (18 countries total)
```python
europe: albania, andorra
asia: afghanistan, armenia
africa: algeria, angola, benin
americas: antigua and barbuda, argentina, bahamas, barbados
oceania: australia, federated states of micronesia
middleeast: bahrain, cyprus, iran, iraq
```

## Prerequisites
1. **Virtual environment activated**:
   ```bash
   source .venv/bin/activate
   ```

2. **Reddit API credentials in `.env` file**:
   ```
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   REDDIT_USER_AGENT=EmotionsDashboard/1.0
   ```

3. **All dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Tests

### Basic Usage
```bash
cd /home/SonOfOgre/Desktop/Emotion
source .venv/bin/activate
python backend/test_pipeline.py
```

### What Gets Tested

**Test 1: Country Coordinates**
- Tests `get_coordinates()` function
- Shows latitude/longitude for each country

**Test 2: Reddit API - Fetch Posts**
- Tests regional subreddit search
- Shows posts fetched from Reddit
- Uses test country: "albania"

**Test 3: Emotion Analyzer (RoBERTa)**
- Tests `EmotionAnalyzer.analyze()`
- Shows emotion classification results
- Model: j-hartmann/emotion-english-distilroberta-base

**Test 4: Collective Analyzer (BART)**
- Tests `CollectiveAnalyzer.analyze_post()`
- Shows collective vs personal classification
- Model: facebook/bart-large-mnli

**Test 5: Cross-Country Detector (BERT-NER)**
- Tests `CrossCountryDetector.detect_countries()`
- Shows country entity recognition
- Model: dslim/bert-base-NER

**Test 6: Multimodal Analyzer (CLIP + BLIP)**
- Tests `MultimodalAnalyzer.analyze_reddit_media()`
- Shows image/video analysis if present

**Test 7: Post Database**
- Tests database operations:
  - `add_raw_post()` - Store unanalyzed post
  - `get_unanalyzed_posts()` - Get posts needing analysis
  - `add_post()` - Store analyzed post
  - `get_country_aggregated_emotion()` - Get emotion aggregation
- Uses `test_posts.db` (separate from production)

**Test 8: Full Pipeline (End-to-End)**
- Tests complete flow: Reddit → ML → Database
- Uses test country: "argentina"

**Test 9: API Endpoints**
- Lists all available Flask API routes
- Shows how to test them manually

## Output Format

Each test shows:
```
================================================================================
                           TEST X: COMPONENT NAME
================================================================================
💡 ANALYSIS: What this component does

[Step 1] Initialize Component
--------------------------------------------------------------------------------
📥 INPUT - Description:
{input data shown here}

📤 OUTPUT - Description:
{output data shown here}

💡 ANALYSIS: What the output means
```

## Test Database

### Location
```
/home/SonOfOgre/Desktop/Emotion/backend/test_posts.db
```

### Inspect Database
```bash
# Open database
sqlite3 backend/test_posts.db

# View tables
.tables

# View raw posts
SELECT country, COUNT(*) FROM raw_posts GROUP BY country;

# View analyzed posts
SELECT country, emotion, COUNT(*) FROM posts GROUP BY country, emotion;

# Exit
.quit
```

### Clean Up After Testing
```bash
# Delete test database
rm backend/test_posts.db

# Or let the script prompt you on next run
```

## Example Output

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                   EMOTION PIPELINE - DEEP DIVE TESTING                       ║
║                  Test Each Function with Detailed I/O                        ║
║                                                                              ║
║  🧪 TEST MODE: Limited regions, separate DB, your Reddit credentials        ║
╚══════════════════════════════════════════════════════════════════════════════╝

================================================================================
TESTING CONFIGURATION
================================================================================
Database: /home/SonOfOgre/Desktop/Emotion/backend/test_posts.db
Total test countries: 18
Regions: ['europe', 'asia', 'africa', 'americas', 'oceania', 'middleeast']
Using Reddit credentials from: .env file
================================================================================

================================================================================
                      TEST 1: SUBREDDIT PARSER
================================================================================

[Step 1] Get coordinates for test countries
--------------------------------------------------------------------------------
📥 INPUT - Country:
albania

📤 OUTPUT - Coordinates:
[41.1533, 20.1683]

📤 OUTPUT - Sample countries:
['usa', 'uk', 'canada', 'brazil', 'china', ...]
```

## Troubleshooting

### Reddit API Errors
```
❌ Reddit API connection failed
```
**Solution**: Check your `.env` file has valid credentials

### No Posts Found
```
⚠ Found 0 posts for albania
```
**Solution**: Normal - some countries may not have recent posts. Try another country.

### ML Models Loading Slowly
```
🤖 Loading pre-trained model...
```
**Solution**: First run downloads models (~2GB). Subsequent runs are faster.

### Import Errors
```
ModuleNotFoundError: No module named 'transformers'
```
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

## Tips

1. **Run individual tests**: Comment out tests you don't need in `main()`
2. **Adjust fetch limits**: Change `limit=5` to `limit=2` for faster testing
3. **Test different countries**: Modify `test_country` variable in functions
4. **Keep test database**: Don't delete it to see accumulated test data
5. **Compare with production**: Run tests then check production `posts.db`

## Next Steps

After understanding the pipeline:
1. Modify ML models in `emotion_analyzer.py`, `collective_analyzer.py`, etc.
2. Add new analysis functions
3. Test changes with this script
4. Deploy to production app.py

## Questions?

Review the test output to understand:
- What data Reddit provides
- How ML models transform the data
- What gets stored in the database
- How the API serves the data

Each section shows the actual data flowing through your system!
