import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from vinted_scraper import VintedScraper

# Add your Vinted search URLs here
SEARCHES = {
    "Nike Shoes under 50€": "https://www.vinted.fr/catalog?search_text=nike&price_to=50&currency=EUR",
}

HISTORY_FILE = 'vinted_history.json'

def send_email(new_items):
    sender = os.environ.get('EMAIL_USER')
    password = os.environ.get('EMAIL_PASS')
    receiver = os.environ.get('EMAIL_TO')

    if not sender or not password or not receiver:
        print("Email credentials missing. Skipping email.")
        return

    msg = MIMEMultipart("alternative")
    msg['Subject'] = f"🛍️ {sum(len(items) for items in new_items.values())} New Vinted Items Found!"
    msg['From'] = sender
    msg['To'] = receiver

    html = "<h2>New Vinted Items Found!</h2>"
    for search_name, items in new_items.items():
        if not items: continue
        html += f"<h3>{search_name}</h3><ul>"
        for item in items:
            html += f"<li><a href='{item['url']}'><strong>{item['title']}</strong></a> - {item['price']}</li>"
        html += "</ul>"

    msg.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

def main():
    scraper = VintedScraper("https://www.vinted.fr")
    
    # Load past seen items
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            history = set(json.load(f))
    else:
        history = set()

    new_items_found = {}
    updated_history = set(history)

    for search_name, url in SEARCHES.items():
        print(f"Checking {search_name}...")
        try:
            # Extract query params from URL
            items = scraper.search(url, limit=20)
            new_items_found[search_name] = []
            
            for item in items:
                item_id = str(item['id'])
                if item_id not in history:
                    new_items_found[search_name].append(item)
                    updated_history.add(item_id)
                    print(f"  New item: {item['title']} - {item['price']}")
        except Exception as e:
            print(f"Error fetching {search_name}: {e}")

    # Trigger email if anything new was found
    if any(len(items) > 0 for items in new_items_found.values()):
        send_email(new_items_found)
    else:
        print("No new items found.")

    # Save state back to GitHub
    with open(HISTORY_FILE, 'w') as f:
        json.dump(sorted(list(updated_history)), f, indent=2)

if __name__ == "__main__":
    main()
