import os
import urllib.parse
from docx import Document 
from docx.shared import Pt, RGBColor

def generate_gmaps_search_link(name, address):
    """Genera un link di ricerca robusto per Google Maps."""
    if not name and not address:
        return None
    
    # Combina nome e indirizzo per massima precisione
    query = f"{name} {address}".strip()
    
    # Codifica la stringa (es. ' ' diventa '%20', 'ß' diventa '%C3%9F')
    safe_query = urllib.parse.quote(query)
    
    # Usa l'API universale di ricerca (funziona sempre, niente 404)
    return f"https://www.google.com/maps/search/?api=1&query={safe_query}"

def print_terminal_report(state):
    print("\n" + "="*60)
    print(f"✈️  ITINERARIO FINALE: {state.get('destination', 'Viaggio').upper()}")
    print("="*60)
    
    itinerary = state.get('itinerary', [])
    
    for day in itinerary:
        print(f"\n📅 Giorno {day['day_number']}: {day['focus']}")
        print("-" * 40)
        
        for p in day.get('places', []):
            name = p.get('name', 'Senza nome')
            rating = p.get('rating', 'N/A')
            address = p.get('address', '')
            
            print(f"   📍 {name} (⭐ {rating})")
            if address:
                print(f"      🏠 {address}")
            
            # Genera link immediato anche nel terminale
            link = generate_gmaps_search_link(name, address)
            if link:
                print(f"      🔗 Maps: {link}")
            print("      ---")

def generate_html_report(state):
    dest = state.get('destination', 'Viaggio')
    # Nome file sicuro (senza spazi)
    filename = f"viaggio_{dest.replace(' ', '_').lower()}.html"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Viaggio a {dest}</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background: #f0f2f5; color: #333; }}
            h1 {{ color: #2c3e50; text-align: center; margin-bottom: 30px; }}
            .day-card {{ background: white; padding: 25px; margin-bottom: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .day-title {{ color: #e67e22; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 15px; }}
            .place {{ margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #3498db; }}
            .place-name {{ font-weight: bold; font-size: 1.1em; }}
            .place-rating {{ color: #f1c40f; }}
            .btn-map {{ display: inline-block; background: #3498db; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; font-size: 0.9em; margin-top: 5px; }}
            .btn-map:hover {{ background: #2980b9; }}
        </style>
    </head>
    <body>
        <h1>✈️ Itinerario: {dest.upper()}</h1>
    """
    
    for day in state.get('itinerary', []):
        html += f"""
        <div class='day-card'>
            <h2 class='day-title'>📅 Giorno {day['day_number']}: {day['focus']}</h2>
        """
        
        for p in day.get('places', []):
            name = p.get('name', 'Nome non disp.')
            address = p.get('address', '')
            rating = p.get('rating', 'N/A')
            link = generate_gmaps_search_link(name, address)
            
            html += f"""
            <div class='place'>
                <div class='place-name'>{name} <span class='place-rating'>★ {rating}</span></div>
                <div style='color: #666; font-size: 0.9em; margin: 4px 0;'>{address}</div>
            """
            
            if link:
                html += f"<a href='{link}' class='btn-map' target='_blank'>📍 Vedi su Google Maps</a>"
            
            html += "</div>"
            
        html += "</div>"
        
    html += "</body></html>"
    
    # Scrittura file con encoding UTF-8 per supportare emoji e caratteri speciali
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
        
    return filename

def generate_docx_report(state):
    """Genera un file Word (.docx) con l'itinerario."""
    destination = state.get('destination', 'Viaggio')
    filename = f"viaggio_{destination.replace(' ', '_').lower()}.docx"
    
    # 1. Crea il documento
    doc = Document()
    
    # Titolo
    title = doc.add_heading(f'✈️ Itinerario: {destination.upper()}', 0)
    title.alignment = 1  # Center alignment

    # Intro
    doc.add_paragraph(f"Ecco il tuo piano di viaggio generato dall'AI per {destination}.")

    # 2. Loop sui giorni
    for day in state.get('itinerary', []):
        # Intestazione Giorno
        doc.add_heading(f"📅 Giorno {day['day_number']}: {day['focus']}", level=1)
        
        for p in day.get('places', []):
            name = p.get('name', 'Senza nome')
            rating = p.get('rating', 'N/A')
            address = p.get('address', '')
            
            # Nome del luogo 
            p_para = doc.add_paragraph()
            runner = p_para.add_run(f"📍 {name}")
            runner.bold = True
            runner.font.size = Pt(12)
            
            # Rating e Indirizzo
            doc.add_paragraph(f"   ⭐ Rating: {rating}")
            doc.add_paragraph(f"   🏠 Indirizzo: {address}")
            
            # Link (Word non supporta link facili via codice senza hack XML complessi, 
            # quindi mettiamo l'URL come testo cliccabile dai moderni reader)
            link = generate_gmaps_search_link(name, address)
            if link:
                doc.add_paragraph(f"   🔗 Maps: {link}", style='List Bullet')
            
            doc.add_paragraph("-" * 20) # Separatore visivo

    # 3. Salva
    doc.save(filename)
    return filename