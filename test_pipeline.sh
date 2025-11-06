#!/bin/bash
# Quick test script for pipeline testing

echo "🧪 Emotion Pipeline Test Runner"
echo "================================"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Virtual environment not activated"
    echo "Run: source .venv/bin/activate"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    echo "Create .env with your Reddit API credentials"
    exit 1
fi

# Check if test database exists
if [ -f "backend/test_posts.db" ]; then
    echo "⚠️  Test database already exists: backend/test_posts.db"
    read -p "Delete and start fresh? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm backend/test_posts.db
        echo "✓ Deleted old test database"
    fi
fi

echo ""
echo "🚀 Starting pipeline tests..."
echo "📊 Using test configuration:"
echo "   - 18 countries (limited regions)"
echo "   - Separate test database"
echo "   - Your Reddit API credentials"
echo ""

# Run the test script
python backend/test_pipeline.py

echo ""
echo "✅ Testing complete!"
echo ""
echo "📝 Tips:"
echo "   - View test database: sqlite3 backend/test_posts.db"
echo "   - Clean up: rm backend/test_posts.db"
echo "   - Read guide: cat backend/TEST_PIPELINE_README.md"
