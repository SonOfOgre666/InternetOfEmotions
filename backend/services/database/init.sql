-- Internet of Emotions - Microservices Database Schema
-- PostgreSQL 15+

-- ============================================================================
-- Service 1: Post Fetcher - Raw Posts Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS raw_posts (
    id SERIAL PRIMARY KEY,
    reddit_id VARCHAR(20) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    text TEXT,
    url TEXT,
    author VARCHAR(100),
    subreddit VARCHAR(50),
    score INTEGER DEFAULT 0,
    num_comments INTEGER DEFAULT 0,
    reddit_created_at TIMESTAMP NOT NULL,  -- Reddit post creation date (for cleanup)
    fetched_at TIMESTAMP DEFAULT NOW(),     -- When we fetched it
    has_url BOOLEAN DEFAULT FALSE,         -- True if post needs URL extraction
    country VARCHAR(100),
    region VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for raw_posts
CREATE INDEX IF NOT EXISTS idx_raw_posts_reddit_created ON raw_posts(reddit_created_at);
CREATE INDEX IF NOT EXISTS idx_raw_posts_country ON raw_posts(country);
CREATE INDEX IF NOT EXISTS idx_raw_posts_has_url ON raw_posts(has_url);
CREATE INDEX IF NOT EXISTS idx_raw_posts_fetched_at ON raw_posts(fetched_at);
CREATE INDEX IF NOT EXISTS idx_raw_posts_region ON raw_posts(region);

-- ============================================================================
-- Service 2: URL Extractor - URL Content Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS url_content (
    id SERIAL PRIMARY KEY,
    post_id INTEGER UNIQUE NOT NULL REFERENCES raw_posts(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    domain VARCHAR(255),
    content_type VARCHAR(50),  -- 'blog', 'news', 'social_media', 'ignored'
    extracted_text TEXT,
    title TEXT,
    author VARCHAR(255),
    published_date TIMESTAMP,
    extraction_status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'success', 'failed', 'ignored'
    extracted_at TIMESTAMP DEFAULT NOW(),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for url_content
CREATE INDEX IF NOT EXISTS idx_url_content_post_id ON url_content(post_id);
CREATE INDEX IF NOT EXISTS idx_url_content_extraction_status ON url_content(extraction_status);
CREATE INDEX IF NOT EXISTS idx_url_content_domain ON url_content(domain);
CREATE INDEX IF NOT EXISTS idx_url_content_content_type ON url_content(content_type);

-- ============================================================================
-- Service 3: ML Analyzer - Analyzed Posts Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS analyzed_posts (
    id SERIAL PRIMARY KEY,
    post_id INTEGER UNIQUE NOT NULL REFERENCES raw_posts(id) ON DELETE CASCADE,
    emotion VARCHAR(20) NOT NULL,  -- joy, sadness, anger, fear, surprise, disgust, neutral
    confidence FLOAT,
    is_collective BOOLEAN,         -- True if post is about collective/country issue
    detected_countries TEXT[],     -- Array of detected countries (for cross-country posts)
    analysis_timestamp TIMESTAMP DEFAULT NOW(),
    model_version VARCHAR(50),
    roberta_emotion VARCHAR(20),
    roberta_confidence FLOAT,
    vader_sentiment FLOAT,
    textblob_sentiment FLOAT,
    keyword_match VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for analyzed_posts
CREATE INDEX IF NOT EXISTS idx_analyzed_posts_post_id ON analyzed_posts(post_id);
CREATE INDEX IF NOT EXISTS idx_analyzed_posts_emotion ON analyzed_posts(emotion);
CREATE INDEX IF NOT EXISTS idx_analyzed_posts_is_collective ON analyzed_posts(is_collective);
CREATE INDEX IF NOT EXISTS idx_analyzed_posts_timestamp ON analyzed_posts(analysis_timestamp);

-- ============================================================================
-- Service 4: DB Cleanup - Cleanup Logs Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS cleanup_logs (
    id SERIAL PRIMARY KEY,
    cleanup_timestamp TIMESTAMP DEFAULT NOW(),
    posts_removed INTEGER DEFAULT 0,
    url_content_removed INTEGER DEFAULT 0,
    analyzed_posts_removed INTEGER DEFAULT 0,
    duration_seconds FLOAT,
    status VARCHAR(20),  -- 'success', 'failed', 'partial'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for cleanup_logs
CREATE INDEX IF NOT EXISTS idx_cleanup_logs_timestamp ON cleanup_logs(cleanup_timestamp);
CREATE INDEX IF NOT EXISTS idx_cleanup_logs_status ON cleanup_logs(status);

-- ============================================================================
-- Service 5: Country Aggregation - Country Emotions Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS country_emotions (
    id SERIAL PRIMARY KEY,
    country VARCHAR(100) UNIQUE NOT NULL,
    dominant_emotion VARCHAR(20),
    confidence FLOAT,
    algorithm_votes JSONB,  -- {majority: 'anger', weighted: 'fear', intensity: 'fear', median: 'anger'}
    post_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    emotion_distribution JSONB,  -- {joy: 10, sadness: 20, anger: 30, ...}
    weighted_scores JSONB,       -- {anger: 0.85, fear: 0.72, ...} - intensity × confidence scores
    average_confidence FLOAT DEFAULT 0.5,  -- Average confidence across all posts
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for country_emotions
CREATE INDEX IF NOT EXISTS idx_country_emotions_country ON country_emotions(country);
CREATE INDEX IF NOT EXISTS idx_country_emotions_last_updated ON country_emotions(last_updated);
CREATE INDEX IF NOT EXISTS idx_country_emotions_dominant_emotion ON country_emotions(dominant_emotion);

-- ============================================================================
-- Service 8: Statistics - Global Statistics Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS global_statistics (
    id SERIAL PRIMARY KEY,
    total_posts INTEGER,
    countries_ready INTEGER,
    emotion_distribution JSONB,  -- {joy: 1000, sadness: 2000, ...}
    top_countries JSONB,          -- [{country: 'USA', count: 500}, ...]
    top_events JSONB,             -- [{topic: 'election', count: 100}, ...]
    calculated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for global_statistics
CREATE INDEX IF NOT EXISTS idx_global_stats_calculated_at ON global_statistics(calculated_at);

-- ============================================================================
-- Combined View: Full Post Details (Joins all tables)
-- ============================================================================

CREATE OR REPLACE VIEW post_details AS
SELECT
    rp.id,
    rp.reddit_id,
    rp.title,
    rp.text,
    rp.url,
    rp.author,
    rp.subreddit,
    rp.score,
    rp.num_comments,
    rp.reddit_created_at,
    rp.fetched_at,
    rp.country,
    rp.region,
    uc.extracted_text,
    uc.domain,
    uc.content_type,
    ap.emotion,
    ap.confidence,
    ap.is_collective,
    ap.detected_countries
FROM raw_posts rp
LEFT JOIN url_content uc ON rp.id = uc.post_id
LEFT JOIN analyzed_posts ap ON rp.id = ap.post_id;

-- ============================================================================
-- Utility Functions
-- ============================================================================

-- Function to get post age in days
CREATE OR REPLACE FUNCTION get_post_age_days(post_id INTEGER)
RETURNS FLOAT AS $$
BEGIN
    RETURN EXTRACT(EPOCH FROM (NOW() - (SELECT reddit_created_at FROM raw_posts WHERE id = post_id))) / 86400;
END;
$$ LANGUAGE plpgsql;

-- Function to check if post should be cleaned up (>30 days old)
CREATE OR REPLACE FUNCTION should_cleanup_post(post_id INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN get_post_age_days(post_id) > 30;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Triggers for updated_at timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_raw_posts_updated_at BEFORE UPDATE ON raw_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_url_content_updated_at BEFORE UPDATE ON url_content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analyzed_posts_updated_at BEFORE UPDATE ON analyzed_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_country_emotions_updated_at BEFORE UPDATE ON country_emotions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Initial Data
-- ============================================================================

-- Insert placeholder for global statistics
INSERT INTO global_statistics (total_posts, countries_ready, emotion_distribution, top_countries, top_events)
VALUES (0, 0, '{}'::jsonb, '[]'::jsonb, '[]'::jsonb)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Useful Queries
-- ============================================================================

-- Get posts pending URL extraction
-- SELECT * FROM raw_posts WHERE has_url = TRUE AND id NOT IN (SELECT post_id FROM url_content);

-- Get posts pending ML analysis
-- SELECT * FROM raw_posts WHERE id NOT IN (SELECT post_id FROM analyzed_posts);

-- Get posts older than 30 days (candidates for cleanup)
-- SELECT * FROM raw_posts WHERE reddit_created_at < NOW() - INTERVAL '30 days';

-- Get country emotion summary
-- SELECT country, COUNT(*) as post_count, dominant_emotion, confidence
-- FROM country_emotions
-- ORDER BY post_count DESC;

-- ============================================================================
-- Permissions (Optional - for production)
-- ============================================================================

-- Create application user (if needed)
-- CREATE USER ioe_app WITH PASSWORD 'secure_password';
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ioe_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ioe_app;

COMMENT ON DATABASE internet_of_emotions IS 'Internet of Emotions - Microservices Database';
