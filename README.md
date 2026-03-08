# Vinted Tracker

GitHub Actions-based Vinted notifications system that emails you when new listings match your search criteria.

## How It Works

This tracker runs automatically every 30 minutes via GitHub Actions. It searches Vinted for items matching your criteria and sends you an email whenever new items appear that you haven't seen before.

## Setup

### 1. Add GitHub Secrets

Go to your [repository settings](../../settings/secrets/actions) and add three secrets:

- **EMAIL_USER** - Your Gmail address
- **EMAIL_PASS** - Your Gmail app password ([how to create one](https://support.google.com/accounts/answer/185833))
- **EMAIL_TO** - The email address where you want to receive notifications

### 2. Configure Your Searches

Edit `main.py` and modify the `SEARCHES` dictionary. Each search needs:

- **base_url**: The Vinted domain (e.g., `https://www.vinted.be`, `https://www.vinted.fr`)
- **params**: A dictionary with your search criteria

#### Example:

```python
SEARCHES = {
    "Nike Shoes under 50€": {
        "base_url": "https://www.vinted.fr",
        "params": {
            "search_text": "nike shoes",
            "price_to": "50",
            "currency": "EUR",
            "order": "newest_first",
        },
    },
}
```

#### Available Parameters:

- `search_text`: Keywords to search for
- `price_from`: Minimum price
- `price_to`: Maximum price
- `currency`: Currency code (EUR, USD, GBP, etc.)
- `brand_ids`: List of brand IDs (e.g., `["53", "88"]`)
- `size_ids`: List of size IDs (e.g., `["784"]`)
- `status_ids`: Item condition - `["1"]` = new, `["6"]` = very good, etc.
- `order`: Sort order - `newest_first`, `price_low_to_high`, `price_high_to_low`

#### Finding Brand/Size IDs:

1. Go to Vinted and do your search with all filters
2. Look at the URL - it contains parameters like `brand_ids[]=3272194`
3. Copy those IDs into your params dictionary

### 3. Test It

Go to the [Actions tab](../../actions) and manually run the "Check Vinted Searches" workflow to test immediately.

## How History Works

The tracker maintains a `vinted_history.json` file with all item IDs you've already been notified about. This ensures:

- You only get emails about NEW items
- No duplicate notifications
- The system picks up where it left off after each run

This is the same logic used by the [camper tracker](https://github.com/impca201/tracker).

## Schedule

The tracker runs automatically every 30 minutes. You can adjust this in `.github/workflows/vinted-check.yml` by changing the cron schedule.

## Email Format

Emails are styled to match your camper tracker:

- Subject: "🛍️ X new items available on Vinted!"
- Grouped by search name
- Each item shows: title, price, and a "View item" link

## Adding More Searches

Just add another entry to the `SEARCHES` dictionary in `main.py`:

```python
SEARCHES = {
    "Search 1": { ... },
    "Search 2": { ... },
    "Search 3": { ... },
}
```

No limit on the number of searches!
