import gradio as gr
import json
import folium
from folium import plugins
import math

def load_fishing_spots():
    """Load and filter fishing spots data"""
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filter entries that have required fields
    filtered_spots = []
    for spot in data:
        # Check if required fields exist and are valid
        if (spot.get('lat') and spot.get('lng') and 
            spot.get('id') and spot.get('bezeichnung') and
            spot.get('lat') != 0 and spot.get('lng') != 0):
            
            try:
                # Convert lat/lng to float if they're strings
                lat = float(str(spot['lat']).strip())
                lng = float(str(spot['lng']).strip())
                
                # Basic validation for German coordinates
                if 47 <= lat <= 55 and 5 <= lng <= 16:
                    filtered_spots.append({
                        'id': spot['id'],
                        'bezeichnung': spot['bezeichnung'],
                        'verein': spot.get('verein', 'N/A'),
                        'lat': lat,
                        'lng': lng
                    })
            except (ValueError, TypeError):
                continue
    
    return filtered_spots

def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two points in kilometers"""
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lng/2) * math.sin(delta_lng/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def create_map(selected_cities=None):
    """Create a folium map with fishing spots"""
    fishing_spots = load_fishing_spots()
    
    # Filter spots by selected cities
    if selected_cities:
        filtered_spots = []
        for spot in fishing_spots:
            spot_id = spot['id']
            if any(spot_id.startswith(city_prefix) for city_prefix in selected_cities):
                filtered_spots.append(spot)
        fishing_spots = filtered_spots
    else:
        # If no cities are selected, show no spots
        fishing_spots = []
    
    # Default center (Germany)
    center_lat = 52.5
    center_lng = 13.4
    zoom_start = 6
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=zoom_start,
        tiles='OpenStreetMap'
    )
    
    # Create marker cluster for all fishing spots with adjusted threshold
    marker_cluster = plugins.MarkerCluster(
        name="Fishing Spots",
        overlay=True,
        control=True,
        max_cluster_radius=40,  # Reduced from default 80 to show individual markers sooner
        disable_clustering_at_zoom=12,  # Show individual markers at zoom level 12 and above
        icon_create_function="""
        function(cluster) {
            var childCount = cluster.getChildCount();
            var c = ' marker-cluster-';
            if (childCount < 10) {
                c += 'small';
            } else if (childCount < 100) {
                c += 'medium';
            } else {
                c += 'large';
            }
            return new L.DivIcon({ 
                html: '<div><span>' + childCount + '</span></div>', 
                className: 'marker-cluster' + c, 
                iconSize: new L.Point(40, 40) 
            });
        }
        """
    ).add_to(m)
    
    # Add all fishing spots to the cluster
    for spot in fishing_spots:
        # Create Google Maps link
        google_maps_url = f"https://www.google.com/maps?q={spot['lat']},{spot['lng']}"
        
        # Create popup content
        popup_content = f"""
        <div style="width: 220px;">
            <b>ID:</b> {spot['id']}<br>
            <b>Name:</b> {spot['bezeichnung']}<br>
            <b>Verein:</b> {spot['verein']}
        """
        
        if 'distance' in spot:
            popup_content += f"<br><b>Distance:</b> {spot['distance']:.1f} km"
        
        popup_content += f"""<br><br>
            <a href="{google_maps_url}" target="_blank" style="
                background-color: #4285f4; 
                color: white; 
                padding: 5px 10px; 
                text-decoration: none; 
                border-radius: 3px; 
                font-size: 12px;
                display: inline-block;
            ">📍 Navigation mit Google Maps</a>
        </div>"""
        
        # Create marker and add to cluster
        folium.Marker(
            [spot['lat'], spot['lng']],
            popup=folium.Popup(popup_content, max_width=250),
            tooltip=spot['bezeichnung'],
            icon=folium.Icon(color='blue', icon='tint')
        ).add_to(marker_cluster)
    
    return m

def update_map(lat_input, lng_input, distance_input):
    """Update map based on user input"""
    try:
        if lat_input and lng_input:
            user_lat = float(lat_input)
            user_lng = float(lng_input)
            max_distance = float(distance_input) if distance_input else 50
            
            # Validate coordinates for Germany/Europe
            if not (47 <= user_lat <= 55 and 5 <= user_lng <= 16):
                return create_map(), "⚠️ Please enter coordinates within Germany/Europe region"
            
            map_obj = create_map(user_lat, user_lng, max_distance)
            return map_obj, f"✅ Showing fishing spots within {max_distance} km of your location"
        else:
            map_obj = create_map()
            return map_obj, "📍 Showing all fishing spots. Enter your coordinates to see nearby spots."
    except ValueError:
        return create_map(), "❌ Please enter valid numeric coordinates"



# Load initial data
fishing_spots = load_fishing_spots()
total_spots = len(fishing_spots)

# Create Gradio interface with mobile-optimized CSS
with gr.Blocks(
    title="Brandenburg Angeln Gewaesser", 
    theme=gr.themes.Soft(),
    css="""
    /* Fix horizontal positioning and ensure full visibility */
    html, body {
        margin: 0 !important;
        padding: 0 !important;
        overflow-x: hidden !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    
    /* Mobile-first responsive design */
    .gradio-container {
        max-width: 100% !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        height: 100vh !important;
        overflow: hidden !important;
        position: relative !important;
        left: 0 !important;
        right: 0 !important;
        box-sizing: border-box !important;
    }
    
    /* Ensure main container is properly positioned */
    .main {
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
    }
    
    /* Minimize all spacing */
    .main > div:first-child {
        padding: 0.2rem !important;
        margin: 0 !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    
    /* Ultra-compact header for mobile */
    .gradio-container h1 {
        font-size: 1rem !important;
        margin: 0.2rem 0 !important;
        line-height: 1.2 !important;
        width: 100% !important;
        text-align: left !important;
    }
    
    .gradio-container p {
        font-size: 0.7rem !important;
        margin: 0.1rem 0 !important;
        line-height: 1.1 !important;
        width: 100% !important;
        text-align: left !important;
    }
    
    /* Compact city selection */
    .city-selection {
        margin: 0.2rem 0 !important;
        padding: 0.2rem !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    
    .city-selection label {
        font-size: 0.8rem !important;
        margin: 0.1rem !important;
        padding: 0.2rem 0.4rem !important;
    }
    
    /* Maximize map container for mobile vertical space */
    .map-container {
        width: 100% !important;
        max-width: 100% !important;
        height: calc(100vh - 10px) !important;
        margin: 0 !important;
        padding: 0 !important;
        position: relative !important;
        left: 0 !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }
    
    .map-container iframe {
        width: 100% !important;
        height: 100% !important;
        border: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Mobile portrait optimizations - maximize vertical space */
    @media (max-width: 768px) and (orientation: portrait) {
        .gradio-container {
            padding: 0 !important;
            height: 100vh !important;
        }
        
        .gradio-container h1 {
            font-size: 0.6rem !important;
            margin: 0.01rem 0 !important;
            line-height: 1 !important;
            padding: 0.01rem !important;
        }
        
        .gradio-container p {
            font-size: 0.5rem !important;
            margin: 0.01rem 0 !important;
            line-height: 1 !important;
            padding: 0.01rem !important;
        }
        
        .city-selection {
            margin: 0.01rem 0 !important;
            padding: 0.01rem !important;
        }
        
        .city-selection label {
            font-size: 0.5rem !important;
            margin: 0.005rem !important;
            padding: 0.01rem 0.05rem !important;
            line-height: 1 !important;
        }
        
        .map-container {
            height: 85vh !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        .map-container iframe {
            width: 100% !important;
            height: 85vh !important;
            min-height: 85vh !important;
            border: none !important;
            margin: 0 !important;
            padding: 0 !important;
        }
    }
    
    /* Mobile landscape optimizations */
    @media (max-width: 768px) and (orientation: landscape) {
        .map-container {
            height: calc(100vh - 50px) !important;
        }
        
        .gradio-container h1 {
            font-size: 0.8rem !important;
            margin: 0.1rem 0 !important;
        }
        
        .gradio-container p {
            display: none !important; /* Hide subtitle in landscape to save space */
        }
        
        .city-selection {
            margin: 0.1rem 0 !important;
            padding: 0.1rem !important;
        }
    }
    
    /* Tablet optimizations */
    @media (min-width: 769px) and (max-width: 1024px) {
        .map-container {
            height: calc(100vh - 120px) !important;
        }
    }
    
    /* Desktop optimizations */
    @media (min-width: 1025px) {
        .gradio-container {
            height: auto !important;
            overflow: visible !important;
        }
        
        .map-container {
            height: calc(100vh - 150px) !important;
        }
    }
    
    /* Very small phones - ultra-compact */
    @media (max-width: 480px) {
        .map-container {
            height: calc(100vh - 5px) !important;
        }
        
        .gradio-container h1 {
            font-size: 0.8rem !important;
            margin: 0.05rem 0 !important;
        }
        
        .city-selection label {
            font-size: 0.65rem !important;
            padding: 0.05rem 0.2rem !important;
        }
    }
    """
) as app:
    gr.Markdown("# Brandenburg Angeln 🎣 [LAVB Verbandsgewässer](https://www.lavb.de/gws/)")
    gr.Markdown(f"**Total: {total_spots}**")
    
    # City selection with custom CSS class
    city_selection = gr.CheckboxGroup(
        choices=["Potsdam", "Cottbus", "Frankfurt-Oder"],
        value=["Potsdam", "Cottbus", "Frankfurt-Oder"],  # All selected by default
        label="Gruppen auswählen",
        info="",
        elem_classes=["city-selection"]
    )
    
    # Full-width map with custom CSS class
    map_html = gr.HTML(
        value=create_map(["P", "C", "F"])._repr_html_(),  # Show all by default
        label="Fishing Spots Map",
        elem_classes=["map-container"]
    )
    
    # Event handler for city selection
    def update_map_by_cities(selected_cities):
        # Map city names to prefixes
        city_prefix_map = {
            "Potsdam": "P",
            "Cottbus": "C", 
            "Frankfurt-Oder": "F"
        }
        
        # Get prefixes for selected cities
        selected_prefixes = [city_prefix_map[city] for city in selected_cities if city in city_prefix_map]
        
        # Create map with filtered spots
        map_obj = create_map(selected_prefixes if selected_prefixes else None)
        return map_obj._repr_html_()
    
    # Update map when city selection changes
    city_selection.change(
        fn=update_map_by_cities,
        inputs=[city_selection],
        outputs=[map_html]
    )

if __name__ == "__main__":
    app.launch(share=True, server_name="0.0.0.0", server_port=7860)
