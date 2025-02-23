import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
import logging
from tqdm import tqdm
import redis
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Base URL to fetch package details
BASE_URL = "https://pypi.org/pypi/{}/json"

# Connect to Redis
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0))
)

# Function to fetch package details asynchronously
async def fetch_package_details(session, package_name):
    try:
        async with session.get(BASE_URL.format(package_name)) as response:
            if response.status == 200:
                return await response.json()  # Return the JSON response
            else:
                return {'name': package_name, 'error': f"Failed to fetch details (status code: {response.status})"}
    except Exception as e:
        return {'name': package_name, 'error': str(e)}

# Function to fetch and parse package list from PyPI Simple
async def fetch_pypi_packages(url="https://pypi.org/simple/"):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    soup = BeautifulSoup(text, 'html.parser')
                    package_names = [a.text for a in soup.find_all('a')]
                    return package_names
                else:
                    logging.error(f"Failed to retrieve data from PyPI (status code: {response.status})")
                    return []
    except Exception as e:
        logging.error(f"Error fetching package list: {str(e)}")
        return []

# Function to store package details in Redis
def store_package_details(package_name, package_details):
    redis_client.set(package_name, json.dumps(package_details))
    # Publish an update message
    redis_client.publish('package_updates', json.dumps({
        'package_name': package_name,
        'message': f"Updated details for {package_name}"
    }))

# Function to fetch all package details and store in Redis
async def fetch_all_package_details(packages):
    total_packages = len(packages)
    logging.info(f"Fetching details for {total_packages} packages...")

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_package_details(session, package) for package in packages]
        for task in tqdm(asyncio.as_completed(tasks), total=total_packages, desc="Fetching Packages"):
            try:
                package_detail = await task
                store_package_details(package_detail['name'], package_detail)
            except Exception as e:
                logging.error(f"Error occurred while fetching package details: {str(e)}")

    logging.info("Package details fetching and storing completed.")

# Main script
async def main():
    # Fetch the list of packages from PyPI Simple
    package_names = await fetch_pypi_packages()
    logging.info(f"Found {len(package_names)} packages.")

    # If packages were fetched, proceed to fetch details in parallel
    if package_names:
        await fetch_all_package_details(package_names)

if __name__ == "__main__":
    asyncio.run(main())
