web: uvicorn pred_service.app:app --host=0.0.0.0 --port=${PORT:-8000}
worker: python collectors/simple_collector.py
bot: python bot/app.py
