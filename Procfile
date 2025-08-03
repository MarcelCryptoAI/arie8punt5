web: cd backend && gunicorn app:app --bind 0.0.0.0:$PORT
release: cd backend && python -c "from app import app, db; app.app_context().push(); db.create_all()"