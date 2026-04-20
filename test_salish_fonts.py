import os
import requests
from PIL import Image, ImageDraw, ImageFont

API_KEY = "AIzaSyCI5rez2hos96uR55LNmt-3L4hUvNjLwJY"
FONTS_DIR = "fonts"
OUTPUT_DIR = "output"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
HTML_FILE = os.path.join(OUTPUT_DIR, "index.html")

TEST_TEXT = "k̓ʷ x̣"

# Create directories
os.makedirs(FONTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

def fetch_fonts_metadata():
    print("Fetching fonts list from Google API...")
    url = f"https://www.googleapis.com/webfonts/v1/webfonts?key={API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching fonts: {response.status_code} - {response.text}")
        return []
    
    data = response.json()
    return data.get("items", [])

def get_font_url(font_data):
    files = font_data.get("files", {})
    if "regular" in files:
        return files["regular"]
    elif files:
        # Fallback to the first available variant
        return list(files.values())[0]
    return None

def download_font(font_name, url):
    safe_name = font_name.replace(" ", "_").lower()
    local_path = os.path.join(FONTS_DIR, f"{safe_name}.ttf")
    
    if os.path.exists(local_path):
        return local_path

    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return local_path
        else:
            print(f"  Failed to download {font_name} (HTTP {response.status_code})")
    except Exception as e:
        print(f"  Error downloading {font_name}: {e}")
        
    return None

def render_font(font_name, font_path):
    safe_name = font_name.replace(" ", "_").lower()
    output_image_path = os.path.join(IMAGES_DIR, f"{safe_name}.png")
    
    # Try to generate it even if it exists, to allow re-rendering if needed, 
    # but we could skip to save time. Let's recreate.
    try:
        # Size chosen to fit text clearly
        font_size = 64
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        print(f"  Failed to load font {font_name} with PIL: {e}")
        return None
        
    width, height = 300, 150
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    
    # Center text approximately
    # Use textbbox if available, else textsize
    try:
        try:
            bbox = draw.textbbox((0, 0), TEST_TEXT, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            text_w, text_h = draw.textsize(TEST_TEXT, font=font)

        x = (width - text_w) / 2
        y = (height - text_h) / 2
        
        draw.text((x, y), TEST_TEXT, font=font, fill="black")
    except OSError as e:
        print(f"  Failed to render font {font_name} (likely an internal shaping error): {e}")
        return None
        
    image.save(output_image_path)
    return f"images/{safe_name}.png"  # Relative path for HTML

def create_html(results):
    print("Generating HTML report...")
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Salish Font Test Report</title>
    <style>
        body { font-family: sans-serif; background-color: #f4f4f4; padding: 20px; }
        .grid { display: flex; flex-wrap: wrap; gap: 20px; }
        .font-card { background: white; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; width: 300px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .font-card h3 { font-size: 16px; margin: 10px 0; color: #333; }
        .font-card img { width: 100%; height: auto; display: block; background: white; border-bottom: 1px solid #eee; }
    </style>
</head>
<body>
    <h1>Salish Font Rendering Test</h1>
    <p>Testing characters: <strong>k̓ʷ x̣</strong> against all Google Fonts.</p>
    <div class="grid">
"""
    for font_name, rel_img_path in results:
        html_content += f"""        <div class="font-card">
            <img src="{rel_img_path}" alt="{font_name} render" loading="lazy" />
            <h3>{font_name}</h3>
        </div>\n"""

    html_content += """    </div>
</body>
</html>
"""
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Report generated successfully: {HTML_FILE}")

def main():
    fonts = fetch_fonts_metadata()
    if not fonts:
        print("No fonts fetched, exiting.")
        return
        
    print(f"Total fonts found: {len(fonts)}")
    
    results = []
    
    # Optional: limit for testing purposes if you pass an argument
    import sys
    limit = None
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
        print(f"Limiting to first {limit} fonts for testing.")
        
    for i, font in enumerate(fonts):
        if limit is not None and i >= limit:
            break
            
        font_name = font["family"]
        url = get_font_url(font)
        
        if not url:
            print(f"[{i+1}/{len(fonts)}] Skipping {font_name}: no downloadable file found.")
            continue
            
        if i % 50 == 0:
            print(f"[{i+1}/{len(fonts)}] Processing fonts... (currently on {font_name})")

        
        font_path = download_font(font_name, url)
        if font_path:
            img_rel_path = render_font(font_name, font_path)
            if img_rel_path:
                results.append((font_name, img_rel_path))

    create_html(results)

if __name__ == "__main__":
    main()
