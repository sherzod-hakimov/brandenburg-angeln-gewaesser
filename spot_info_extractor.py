import requests
import json
import urllib.parse
from typing import List, Dict, Any

def query_fishing_spot(gewaesser_id: str) -> Dict[Any, Any]:
    """
    Query the fishing spot API for a given gewaesser_id
    
    Args:
        gewaesser_id: The ID to query (e.g., "P 04-116")
    
    Returns:
        Dictionary containing the API response
    """
    # URL encode the ID
    encoded_id = urllib.parse.quote(gewaesser_id)
    
    # Construct the API URL
    url = f"https://gws.lavb.de/api/detail?gewaesser_id={encoded_id}"
    
    try:
        # Make the GET request
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Return the JSON response
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Error querying ID '{gewaesser_id}': {e}")
        return {"error": str(e), "gewaesser_id": gewaesser_id}
    
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON for ID '{gewaesser_id}': {e}")
        return {"error": f"JSON decode error: {str(e)}", "gewaesser_id": gewaesser_id}

def main():
    """
    Main function to process all IDs and save results
    """
    # List of IDs to query
    ids_to_query = [
    ]

    # read IDs from these files: potsdam_ids.txt, cottbus_ids.txt, frankfurt_oder_ids.txt, salmoniden_ids.txt
    try:
        with open('potsdam_ids.txt', 'r', encoding='utf-8') as f:
            ids_to_query.extend(line.strip() for line in f if line.strip())
        
        with open('cottbus_ids.txt', 'r', encoding='utf-8') as f:
            ids_to_query.extend(line.strip() for line in f if line.strip())
        
        with open('frankfurt_oder_ids.txt', 'r', encoding='utf-8') as f:
            ids_to_query.extend(line.strip() for line in f if line.strip())
        
        with open('salmoniden_ids.txt', 'r', encoding='utf-8') as f:
            ids_to_query.extend(line.strip() for line in f if line.strip())
    except FileNotFoundError as e:
        print(f"Error reading input files: {e}")
        return
    
    print(f"Starting to query {len(ids_to_query)} fishing spot(s)...")
    
    # List to store all results
    results = []
    
    # Process each ID
    ids_to_query = list(set(ids_to_query))  # Remove duplicates
    for i, gewaesser_id in enumerate(ids_to_query, 10):
        print(f"Processing {i}/{len(ids_to_query)}: {gewaesser_id}")
        
        # Query the API
        result = query_fishing_spot(gewaesser_id)
        
        # Add the result to our list
        results.append(result)
    
    # Save results to JSON file
    output_filename = "data.json"
    
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to '{output_filename}'")
        print(f"Total records processed: {len(results)}")
        
    except Exception as e:
        print(f"Error saving results to file: {e}")

if __name__ == "__main__":
    main()
