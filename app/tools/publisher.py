import urllib.parse

def generate_maps_link(places):
    """Genera il link di Google Maps per una lista di luoghi."""
    route_stops = []
    for p in places:
        target = p.get('address') or p.get('name')
        if target:
            route_stops.append(urllib.parse.quote(target))
    
    if route_stops:
        return "http://googleusercontent.com/maps.google.com/maps/dir/" + "/".join(route_stops)
    return None

def print_terminal_report(state):
    print("\n" + "="*60)
    print(f"✈️  ITINERARIO FINALE: {state['destination'].upper()}")
    print("="*60)
    
    for day in state['itinerary']:
        print(f"\n📅 Giorno {day['day_number']}: {day['focus']}")
        print("-" * 40)
        
        for p in day['places']:
            print(f"   📍 {p.get('name')} (⭐ {p.get('rating', 'N/A')})")
            print(f"      🏠 {p.get('address')}")
            print("      ---")
            
        link = generate_maps_link(day['places'])
        if link:
            print(f"   🗺️  Link Maps: {link}")

def generate_html_report(state):
    dest = state['destination']
    filename = f"viaggio_{dest.replace(' ', '_')}.html"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Viaggio a {dest}</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; background: #f4f4f9; }}
            .card {{ background: white; padding: 20px; margin-bottom: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; text-align: center; }}
            .btn {{ display: block; background: #27ae60; color: white; padding: 10px; text-align: center; text-decoration: none; border-radius: 5px; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <h1>✈️ {dest.upper()}</h1>
    """
    
    for day in state['itinerary']:
        html += f"<div class='card'><h2>📅 Giorno {day['day_number']}</h2><ul>"
        for p in day['places']:
            html += f"<li><b>{p.get('name')}</b> (⭐ {p.get('rating', 'N/A')})<br>{p.get('address')}</li>"
        html += "</ul>"
        
        link = generate_maps_link(day['places'])
        if link:
            html += f"<a href='{link}' class='btn' target='_blank'>🗺️ Apri Mappa</a>"
        html += "</div>"
        
    html += "</body></html>"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
        
    return filename