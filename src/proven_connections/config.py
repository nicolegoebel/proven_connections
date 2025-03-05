import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
MAPBOX_ACCESS_TOKEN = os.getenv('MAPBOX_ACCESS_TOKEN')
CLEARBIT_API_KEY = os.getenv('CLEARBIT_API_KEY')

# Default map settings
DEFAULT_MAP_STYLE = 'mapbox://styles/mapbox/light-v10'
DEFAULT_MAP_CENTER = [-98.5795, 39.8283]  # Center of USA
DEFAULT_MAP_ZOOM = 3
