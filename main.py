import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from vinted_scraper import VintedScraper

# Add your Vinted searches here
# Each search has a base_url (the Vinted domain) and params (search criteria)
SEARCHES = {
    "Ledmaskers onder 90 EUR": {
        "base_url": "https://www.vinted.be",
        "params": {
            "search_text": "led mask",
            "brand_ids": ["3272194", "165906", "9591971"],
            "price_to": "90",
            "currency": "EUR",
            "order": "price_low_to_high",
        },
    },
    "Salomon X Ultra 360 GTX onder 90 EUR": {
        "base_url": "https://www.vinted.be",
        "params": {
            "search_text": "Salomon X Ultra 360 GTX",
            "size_ids": ["784"],
            "status_ids": ["1", "6"],  # 1=new, 6=very good condition
            "price_to": "90",
            "currency": "EUR",
            "order": "newest_first",
        },
    },
    "Salomon X Ultra 4 GTX onder 90 EUR": {
        "base_url": "https://www.vinted.be",
        "params": {
            "search_text": "Salomon X Ultra 4 GTX",
            "size_ids": ["784"],
            "status_ids": ["1", "6"],
            "price_to": "90",
            "currency": "EUR",
            "order": "newest_first",
        },
    },
    "Nike schoenen maat 42 onder 100 EUR": {
        "base_url": "https://www.vinted.be",
        "params": {
            "search_text": "nike",
            "size_ids": ["206"],  # size 42 men's shoes
            "price_to": "100",
            "currency": "EUR",
            "order": "newest_first",
        },
    },
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

    for search_name, cfg in SEARCHES.items():
        print(f"🔎 Checking: {search_name}")
        base_url = cfg["base_url"]
        params = dict(cfg["params"])  # shallow copy
        
        try:
            scraper = VintedScraper(base_url)
            items = scraper.search(params)
            new_items_found[search_name] = []
            
            # Only check first 20 items to match original behavior
            for item in list(items)[:20]:
                item_id = str(item.id)
                if item_id not in history:
                    new_items_found[search_name].append(item)
                    updated_history.add(item_id)
                    print(f"  ✅ New item found: {item.title} - {item.price} {item.currency}")
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
