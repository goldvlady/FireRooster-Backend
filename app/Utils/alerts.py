import requests
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GOOGLE_GEOCODING_API_KEY")

def get_geocode_data(address):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    
    params = {
        'address': address,
        'key': api_key,
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        
        data = response.json()
        
        if data['results']:
            return data['results']
        else:
            print("No results found.")
            
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        
def get_score_by_location_type(location_type):
    if location_type == "ROOFTOP":
        return 1
    elif location_type == 'RANGE_INTERPOLATED':
        return 0.7
    elif location_type == 'GEOMETRIC_CENTER':
        return 0.5
    elif location_type == 'APPROXIMATE':
        return 0.3


def get_place_details(place_id):
    # Prepare the request for the Places API
    place_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={api_key}"
    
    # Make the API request
    response = requests.get(place_url)
    place_data = response.json()
    
    if place_data['status'] == 'OK':
        # Return the types from the Places API response
        return place_data['result'].get('types', [])
    else:
        return []

def is_residential_address(types):
    # Define all possible residential-related types
    residential_keywords = {
        'street_address', 'route', 'locality', 'sublocality', 
        'neighborhood', 'postal_code', 'premise', 'subpremise', 'political'
    }
    
    for t in types:
        if t in residential_keywords:
            return True
    return False

def is_intersection(types):
    for t in types:
        if t == "intersection":
            return True
    return False

def validate_address(result):
    # Step 1: Get Geocode data (place_id and types)
    place_id = result.get('place_id')
    geocode_types = result.get('types')    
    
    if not place_id:
        return "Invalid address or unable to fetch geocode data."

    # Step 2: Get Place details (more detailed types from Places API)
    place_types = get_place_details(place_id)
    
    # Combine geocode types and place types
    all_types = set(geocode_types + place_types)

    # Step 3: Determine if it's a residential or commercial address
    if is_residential_address(all_types):
        return "Residential Address"
    elif is_intersection(all_types):
        return "Intersection"
    else:
        print("all_types: ", all_types)
        return "Commercial Address"