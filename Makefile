.PHONY: help init bootstrap setup-db install ingest transform status streamlit api clean test lint

# Default RSS feed URL
RSS_URL ?= https://note.com/mued_glasswerks/rss

help:
	@echo "MUED Snowflake AI App - Available commands:"
	@echo ""
	@echo "🚀 Setup:"
	@echo "  make init        - Initialize project (first time setup)"
	@echo "  make install     - Install Python dependencies"
	@echo "  make setup-db    - Show database setup instructions"
	@echo ""
	@echo "📊 Data Operations:"
	@echo "  make ingest      - Fetch RSS and load to Snowflake"
	@echo "  make transform   - Info about transformation (runs automatically)"
	@echo "  make status      - Show database status"
	@echo ""
	@echo "🖥️  Applications:"
	@echo "  make streamlit   - Start Streamlit UI (search interface)"
	@echo "  make api         - Start FastAPI server"
	@echo ""
	@echo "🧪 Development:"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run code formatters"
	@echo "  make clean       - Clean temporary files"

bootstrap: init setup-db
	@echo "✓ Bootstrap complete! Environment is ready."
	@echo "Next: Run 'make ingest' to load initial data"

install:
	@echo "Installing Python dependencies..."
	@poetry install
	@echo "✓ Dependencies installed"

setup-db:
	@echo "Setting up Snowflake database objects..."
	@echo "Please run the following SQL files in Snowflake:"
	@echo "1. sql/setup.sql - Create database objects"
	@echo "2. sql/create_task.sql - Create transformation task"

ingest:
	@echo "📡 Ingesting RSS feed to Snowflake..."
	@poetry run python src/ingest.py
	@echo "✅ Ingestion complete!"

transform:
	@echo "Running manual transformation..."
	@echo "Transformation is handled by Snowflake TASK automatically"
	@echo "To run manually, execute src/transform.sql in Snowflake"

init:
	@echo "Initializing project..."
	@poetry install
	@poetry run pre-commit install
	@echo "✓ Project initialized! Next steps:"
	@echo "1. Copy .env.example to .env and fill in your credentials"
	@echo "2. Run 'make setup-db' for database setup instructions"
	@echo "3. Run 'make ingest' to test RSS ingestion"

status:
	@echo "Checking project status..."
	@poetry run python -c "from src.config import get_snowflake_session; session = get_snowflake_session(); print('✓ Snowflake connection successful'); result = session.sql('SELECT COUNT(*) as cnt FROM BLOG_POSTS').collect(); print(f'Total blog posts: {result[0].CNT}'); session.close()"

streamlit:
	@echo "Starting Streamlit UI..."
	@poetry run streamlit run app/streamlit_app.py --server.port 8501 --server.address localhost

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	@echo "✓ Cleaned temporary files"

test:
	@echo "Running tests..."
	@poetry run pytest tests/ -q

lint:
	@echo "Running linters..."
	@poetry run ruff check --fix .
	@poetry run black .

api:
	@echo "Starting FastAPI server..."
	@poetry run uvicorn api.main:app --reload --port 8000
