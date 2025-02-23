from apscheduler.schedulers.background import BackgroundScheduler
from scripts.fetch_packages import main as fetch_packages
import asyncio

# Create a scheduler
scheduler = BackgroundScheduler()

# Add a job to fetch package details every hour
scheduler.add_job(lambda: asyncio.run(fetch_packages()), 'interval', hours=1)

# Start the scheduler
scheduler.start()
