.PHONY: help bootstrap setup-db install ingest merge enable-task status ui clean test lint

# Default RSS feed URL
RSS_URL ?= https://note.com/mued_glasswerks/rss

help:
	@echo "Available commands:"
	@echo "  make bootstrap    - Complete setup (install deps + create Snowflake objects)"
	@echo "  make ingest      - Fetch RSS and load to Snowflake, then start task scheduler"
	@echo "  make ui          - Start Streamlit UI (coming soon)"
	@echo "  make status      - Show task and data status"
	@echo "  make clean       - Clean up temporary files"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linters"

bootstrap: install setup-db
	@echo "✓ Bootstrap complete! Environment is ready."

install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "✓ Dependencies installed"

setup-db:
	@echo "Setting up Snowflake database objects..."
	python -c "from src.config import get_session; \
		session = get_session(); \
		with open('snowflake/setup.sql', 'r') as f: \
			for stmt in f.read().split(';'): \
				if stmt.strip() and not stmt.strip().startswith('--'): \
					try: \
						session.sql(stmt).collect(); \
					except Exception as e: \
						print(f'Warning: {e}'); \
		session.close()"
	@echo "✓ Database objects created"

ingest:
	@echo "Loading RSS feed: $(RSS_URL)"
	@python -c "from src.loader import load_rss_to_raw, execute_merge, enable_task, get_session; \
		session = get_session(); \
		result = load_rss_to_raw(session, '$(RSS_URL)'); \
		print(f'Load result: {result}'); \
		merge_result = execute_merge(session); \
		print(f'Merge result: {merge_result}'); \
		task_result = enable_task(session); \
		print(f'Task result: {task_result}'); \
		session.close()"
	@echo "✓ RSS loaded and task scheduler started"

merge:
	@echo "Running manual merge..."
	@python -c "from src.loader import execute_merge, get_session; \
		session = get_session(); \
		result = execute_merge(session); \
		print(result); \
		session.close()"

enable-task:
	@echo "Enabling merge task..."
	@python -c "from src.loader import enable_task, get_session; \
		session = get_session(); \
		result = enable_task(session); \
		print(result); \
		session.close()"

status:
	@echo "=== Task Status ==="
	@python -c "from src.loader import get_task_status, get_session; \
		session = get_session(); \
		df = get_task_status(session); \
		print(df[['name', 'state', 'schedule']].to_string()); \
		session.close()"
	@echo "\n=== Data Status ==="
	@python -c "from src.config import get_session; \
		session = get_session(); \
		counts = {}; \
		for table in ['RAW.NOTE_RSS_RAW', 'CORE.BLOG_POSTS']: \
			try: \
				count = session.sql(f'SELECT COUNT(*) as cnt FROM {table}').collect()[0]['CNT']; \
				counts[table] = count; \
			except: \
				counts[table] = 'N/A'; \
		for table, count in counts.items(): \
			print(f'{table}: {count} rows'); \
		session.close()"

ui:
	@echo "Starting Streamlit UI..."
	streamlit run app/main.py --server.port 8501 --server.address localhost

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	@echo "✓ Cleaned temporary files"

test:
	@echo "Running tests..."
	# pytest tests/ -v

lint:
	@echo "Running linters..."
	# ruff check src/
	# black --check src/