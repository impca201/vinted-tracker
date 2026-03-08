import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from vinted_scraper import VintedScraper
from urllib.parse import urlparse, parse_qs

# Add your Vinted search URLs here
SEARCHES = {
    "Ledmaskers onder 90 EUR": "https://www.vinted.be/catalog?search_text=led%20mask&brand_ids[]=3272194&brand_ids[]=165906&brand_ids[]=9591971&page=1&time=1772988124&search_by_image_uuid=&currency=EUR&order=price_low_to_high&price_to=90&search_id=31925953769",
}

HISTORY_FILE = 'vinted_history.json'

def send_email(new_items):
    sender = os.environ.get('EMAIL_USER')
    password = os.environ.get('EMAIL_PASS')
    receiver = os.environ.get('EMAIL_TO')

    if not sender or not password or not receiver:
        print("Email credentials missing. Skipping email.")
        return

    total_items = sum(len(items) for items in new_items.values())
    subject = f"🛍️ {total_items} new {'item' if total_items == 1 else 'items'} available on Vinted!"

    # Build email body matching camper tracker style
    blocks = []
    for search_name, items in new_items.items():
        if not items:
            continue
        
        lines = []
        for item in items:
            lines.append(
                f"<strong>🛍️ {item.title}</strong><br>"
                f"💶 {item.price} {item.currency}<br>"
                f"🔗 <a href='{item.url}' style='color: #007BFF; text-decoration: none;'>View item</a>"
            )
        
        blocks.append(
            f"<h3 style='margin: 16px 0 8px;'>{search_name}</h3>"
            f"<p>{'<br><br>'.join(lines)}</p>"
        )
    
    body = (
        "<p>Hi!</p>"
        "<p>New items matching your searches have just become available:</p>"
        f"{''.join(blocks)}"
        "<p>👉 <a href='https://www.vinted.com' style='color: #007BFF; font-weight: bold; text-decoration: none;'>Browse Vinted now!</a></p>"
    )

    msg = MIMEMultipart("alternative")
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    msg.attach(MIMEText(body, "html"))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

def parse_vinted_url(url):
    """Extract search parameters from Vinted URL"""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    
    # Convert lists to single values and handle brand_ids as array
    search_params = {}
    for key, value in params.items():
        if key == 'brand_ids[]':
            search_params['brand_ids'] = value  # Keep as list
        elif len(value) == 1:
            search_params[key] = value[0]
        else:
            search_params[key] = value
    
    return search_params

def main():
    print('Vinted tracker started...')
    
    # Load past seen items
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            history = set(json.load(f))
    else:
        history = set()

    new_items_found = {}
    updated_history = set(history)

    for search_name, url in SEARCHES.items():
        print(f"🔎 Checking: {search_name}")
        try:
            # Extract domain and params
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            search_params = parse_vinted_url(url)
            
            # Initialize scraper with the correct domain
            scraper = VintedScraper(base_url)
            
            # Search with parameters - returns up to 96 items by default
            items = scraper.search(search_params)
            new_items_found[search_name] = []
            
            # Only check first 20 items to match original behavior
            for item in list(items)[:20]:
                item_id = str(item.id)
                if item_id not in history:
                    new_items_found[search_name].append(item)
                    updated_history.add(item_id)
                    print(f"  ✅ New item found: {item.title}")
        except Exception as e:
            print(f"[Error] Failed to fetch {search_name}: {e}")

    # Trigger email if anything new was found
    if any(len(items) > 0 for items in new_items_found.values()):
        send_email(new_items_found)
    else:
        print('No new items found. No email sent.')

    # Save state back to GitHub (sorted to reduce git diff noise)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(sorted(list(updated_history)), f, indent=2)

if __name__ == "__main__":
    main()
