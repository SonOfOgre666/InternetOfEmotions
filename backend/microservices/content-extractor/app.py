"""
Content Extractor Service
Extracts text content from blog/news article URLs
Translates non-English content to English
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import SharedDatabase
from config import DB_PATH

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize database
db = SharedDatabase(DB_PATH)


def detect_and_translate(text: str, field_name: str = "text") -> str:
    """
    Detect language and translate to English if needed.
    Returns translated text or original if already English.
    """
    if not text or len(text.strip()) < 10:
        return text
    
    try:
        # Detect language
        lang = detect(text)
        
        if lang == 'en':
            # Already English
            return text
        
        # Translate to English
        logger.info(f"🌐 Translating {field_name} from {lang} to English ({len(text)} chars)")
        translator = GoogleTranslator(source=lang, target='en')
        
        # Split into chunks if too long (Google Translate limit ~5000 chars)
        max_chunk = 4500
        if len(text) <= max_chunk:
            translated = translator.translate(text)
        else:
            # Split by sentences/paragraphs
            chunks = []
            current_chunk = ""
            for sentence in text.split('. '):
                if len(current_chunk) + len(sentence) < max_chunk:
                    current_chunk += sentence + '. '
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence + '. '
            if current_chunk:
                chunks.append(current_chunk)
            
            # Translate each chunk
            translated_chunks = [translator.translate(chunk) for chunk in chunks]
            translated = ' '.join(translated_chunks)
        
        logger.info(f"✓ Translated {field_name}: {lang} → en")
        return translated
        
    except LangDetectException:
        # Can't detect language, return original
        logger.warning(f"⚠️  Could not detect language for {field_name}")
        return text
    except Exception as e:
        logger.error(f"Translation error for {field_name}: {e}")
        return text  # Return original on error


def extract_article_content(url: str) -> dict:
    """
    Extract main content from article URL.
    Skips social media links (require login).
    Returns: {text, title, success}
    """
    # Skip social media (safety check)
    social_media = ['twitter.com', 'x.com', 'facebook.com', 'instagram.com', 'tiktok.com',
                   'linkedin.com', 'reddit.com', 'youtube.com', 'youtu.be']
    if any(sm in url.lower() for sm in social_media):
        logger.info(f"⏭️ Skipping social media URL: {url[:50]}")
        return {'success': False, 'error': 'Social media URL (requires login)'}
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'aside']):
            script.decompose()
        
        # Try to find article content
        article = None
        
        # Common article containers
        for selector in [
            'article',
            {'class': 'article'},
            {'class': 'post-content'},
            {'class': 'entry-content'},
            {'class': 'content'},
            {'id': 'article-body'},
            {'class': 'story-body'}
        ]:
            if isinstance(selector, str):
                article = soup.find(selector)
            else:
                article = soup.find(attrs=selector)
            if article:
                break
        
        # Fallback: use main or body
        if not article:
            article = soup.find('main') or soup.find('body')
        
        if not article:
            return {'success': False, 'error': 'No content found'}
        
        # Extract title
        title = None
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)
        if not title:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
        
        # Extract paragraphs
        paragraphs = article.find_all('p')
        text_parts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50]
        
        extracted_text = ' '.join(text_parts)
        
        # Limit to 1000 characters
        if len(extracted_text) > 1000:
            extracted_text = extracted_text[:1000] + '...'
        
        if not extracted_text or len(extracted_text) < 100:
            return {'success': False, 'error': 'Insufficient content'}
        
        logger.info(f"✓ Extracted {len(extracted_text)} chars from {urlparse(url).netloc}")
        
        # Translate title and content to English
        title_en = detect_and_translate(title or '', 'title')
        content_en = detect_and_translate(extracted_text, 'blog content')
        
        return {
            'success': True,
            'text': content_en,
            'title': title_en,
            'domain': urlparse(url).netloc
        }
        
    except requests.Timeout:
        return {'success': False, 'error': 'Timeout'}
    except requests.RequestException as e:
        return {'success': False, 'error': f'Request failed: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Extraction failed: {str(e)}'}


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'content-extractor'})


@app.route('/extract', methods=['POST'])
def extract_url():
    """Extract content from a single URL"""
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    result = extract_article_content(url)
    return jsonify(result)


@app.route('/process/pending', methods=['POST'])
def process_pending():
    """Process posts that need content extraction and translation"""
    
    # Get posts that need extraction OR translation
    rows = db.execute_query('''
        SELECT id, text, link_url
        FROM raw_posts
        WHERE (needs_extraction = 1 AND link_url IS NOT NULL)
           OR (needs_extraction = 0 AND link_url IS NULL)
        LIMIT 100
    ''')
    
    processed = 0
    enriched = 0
    
    for row in rows:
        post_id, original_text, link_url = row
        
        final_text = original_text
        
        # Step 1: Extract blog content if needed
        if link_url:
            result = extract_article_content(link_url)
            
            if result['success']:
                # Combine title + blog content
                final_text = f"{result.get('title', original_text)}. {result['text']}"
                logger.info(f"✓ Extracted blog content for post {post_id}")
            else:
                logger.warning(f"⚠️  Failed to extract {link_url}: {result.get('error')}")
        
        # Step 2: Translate the combined text to English
        # Translate the entire text at once to maintain context and reduce API calls
        final_text = detect_and_translate(final_text, 'post text')
        
        # Update database with translated content
        try:
            db.execute_commit('''
                UPDATE raw_posts
                SET text = ?, needs_extraction = 0
                WHERE id = ?
            ''', (final_text, post_id))
            
            enriched += 1
            logger.info(f"✓ Processed and translated post {post_id}")
        except Exception as e:
            logger.error(f"Error updating post {post_id}: {e}")
        
        processed += 1
    
    return jsonify({
        'processed': processed,
        'enriched': enriched,
        'failed': processed - enriched
    })


@app.route('/stats', methods=['GET'])
def get_stats():
    """Get extraction statistics"""
    try:
        pending = db.execute_query('''
            SELECT COUNT(*) FROM raw_posts WHERE needs_extraction = 1
        ''')[0][0]
        
        total_links = db.execute_query('''
            SELECT COUNT(*) FROM raw_posts WHERE post_type = 'link'
        ''')[0][0]
        
        return jsonify({
            'pending_extraction': pending,
            'total_link_posts': total_links
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5007))
    app.run(host='0.0.0.0', port=port, debug=False)
