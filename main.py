import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import urllib.parse
import time

# Add your Vinted searches here
# Each search has a base_url (the Vinted domain) and params (search criteria)
SEARCHES = {
    "Ledmaskers onder 90 EUR (EN)": {
        "base_url": "https://www.vinted.be",
        "params": {
            "search_text": "led mask",
            "brand_ids": ["3272194", "165906", "9591971"],
            "price_to": "90",
            "currency": "EUR",
            "order": "price_low_to_high",
        },
    },
    "Ledmaskers onder 90 EUR (FR)": {
        "base_url": "https://www.vinted.be",
        "params": {
            "search_text": "masque led",
            "brand_ids": ["3272194", "165906", "9591971"],
            "price_to": "90",
            "currency": "EUR",
            "order": "price_low_to_high",
        },
    },
    "Ledmaskers onder 90 EUR (NL)": {
        "base_url": "https://www.vinted.be",
        "params": {
            "search_text": "led masker",
            "brand_ids": ["3272194", "165906", "9591971"],
            "price_to": "90",
            "currency": "EUR",
            "order": "price_low_to_high",
        },
    },
    "Ledmaskers onder 90 EUR (ES)": {
        "base_url": "https://www.vinted.be",
        "params": {
            "search_text": "mascara led",
            "brand_ids": ["3272194", "165906", "9591971"],
            "price_to": "90",
            "currency": "EUR",
            "order": "price_low_to_high",
        },
    },
    "Ledmaskers onder 90 EUR (IT)": {
        "base_url": "https://www.vinted.be",
        "params": {
            "search_text": "maschera led",
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
            title = item.get('title', 'Unknown')
            price_info = item.get('price', {})
            price = price_info.get('amount', '?') if isinstance(price_info, dict) else item.get('price', '?')
            currency = price_info.get('currency_code', 'EUR') if isinstance(price_info, dict) else item.get('currency', 'EUR')
            url = item.get('url', '')
            
            lines.append(
                f"<strong>🛍️ {title}</strong><br>"
                f"💶 {price} {currency}<br>"
                f"🔗 <a href='{url}' style='color: #007BFF; text-decoration: none;'>View item</a>"
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

def get_vinted_items(base_url, params):
    """Fetch items directly from Vinted API with custom User-Agent to bypass 406 errors"""
    session = requests.Session()
    # A standard modern browser User-Agent prevents Vinted's Cloudflare from instantly returning 406
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
    })
    
    # 1. Fetch initial page to obtain a session cookie
    try:
        session.get(base_url, timeout=10)
    except Exception as e:
        print(f"  [Warning] Could not fetch initial cookie: {e}")
        
    # 2. Reformat parameters for the API
    # IMPORTANT: Vinted API requires array parameters like brand_ids or size_ids 
    # to be comma-separated strings (e.g. brand_ids=1,2,3) rather than standard URL arrays
    api_params = {}
    for k, v in params.items():
        if isinstance(v, list):
            api_params[k] = ",".join(str(x) for x in v)
        else:
            api_params[k] = v
            
    # 3. Call the catalog API
    url = f"{base_url}/api/v2/catalog/items"
    res = session.get(url, params=api_params, timeout=10)
    
    if res.status_code == 200:
        return res.json().get('items', [])
    else:
        raise Exception(f"API returned {res.status_code}: {res.text[:100]}")

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
        params = dict(cfg["params"])
        
        try:
            items = get_vinted_items(base_url, params)
            new_items_found[search_name] = []
            
            # Only check first 20 items
            for item in list(items)[:20]:
                item_id = str(item.get('id', ''))
                if not item_id:
                    continue
                    
                if item_id not in history:
                    new_items_found[search_name].append(item)
                    updated_history.add(item_id)
                    
                    title = item.get('title', 'Unknown')
                    price_info = item.get('price', {})
                    price = price_info.get('amount', '?') if isinstance(price_info, dict) else item.get('price', '?')
                    currency = price_info.get('currency_code', 'EUR') if isinstance(price_info, dict) else item.get('currency', 'EUR')
                    
                    print(f"  ✅ New item found: {title} - {price} {currency}")
            
            # Sleep slightly to avoid rate limits
            time.sleep(1.5)
            
        except Exception as e:
            print(f"[Error] Failed to fetch {search_name}: {e}")

    # Trigger email if anything new was found
    if any(len(items) > 0 for items in new_items_found.values()):
        send_email(new_items_found)
    else:
        print('No new items found. No email sent.')

    # Save state back to GitHub
    with open(HISTORY_FILE, 'w') as f:
        json.dump(sorted(list(updated_history)), f, indent=2)

if __name__ == "__main__":
    main()
