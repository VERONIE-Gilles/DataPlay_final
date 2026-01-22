# analysis/data_loader.py

import pandas as pd
import numpy as np
import re
from django.core.cache import cache

# Exchange rates (as of Dec 31, 2024)
EXCHANGE_RATES_TO_EUR = {
    'EUR': 1.0, 'USD': 1 / 1.0389, 'GBP': 1 / 0.82918,
    'JPY': 1 / 163.06, 'CAD': 1 / 1.4785, 'AUD': 1 / 1.6631,
    'CHF': 1 / 0.9367, 'CNY': 1 / 7.5496, 'SEK': 1 / 11.4840,
    'NZD': 1 / 1.8417, 'MXN': 1 / 21.2110, 'SGD': 1 / 1.4159,
    'HKD': 1 / 8.0726, 'NOK': 1 / 11.8500, 'KRW': 1 / 1518.82,
    'TRY': 1 / 36.7285, 'RUB': 1 / 103.50, 'INR': 1 / 89.05,
    'BRL': 1 / 6.32, 'ZAR': 1 / 19.2520, 'DKK': 1 / 7.4578,
    'PLN': 1 / 4.2625, 'THB': 1 / 35.54, 'MYR': 1 / 4.67,
    'HUF': 1 / 410.25, 'CZK': 1 / 25.185, 'ILS': 1 / 3.82,
    'CLP': 1 / 1023.50, 'PHP': 1 / 60.85, 'AED': 1 / 3.814,
    'COP': 1 / 4562.00, 'SAR': 1 / 3.896, 'VND': 1 / 26380,
}

def extract_price_and_currency(x):
    """Extract price and currency from price_overview field"""
    if pd.isna(x) or x == '\\N' or x == 'N':
        return None, None
    
    try:
        x = str(x)
        price_match = re.search(r'["\']?final["\']?\s*:\s*(\d+)', x)
        price = int(price_match.group(1)) / 100 if price_match else None
        
        currency_match = re.search(r'["\']?currency["\']?\s*:\s*["\']([A-Z]{3})["\']', x)
        currency = currency_match.group(1) if currency_match else None
        
        return price, currency
    except Exception:
        return None, None

def convert_to_eur(row):
    """Convert price to EUR using exchange rates"""
    if row['price'] == 0:
        return 0.0
    if pd.isna(row['price']) or pd.isna(row['currency']):
        return 0.0
    rate = EXCHANGE_RATES_TO_EUR.get(row['currency'])
    if rate is None:
        return 0.0
    return round(row['price'] * rate, 2)

def load_games_data(use_cache=True):
    """
    Load and preprocess games data
    Uses Django cache to avoid reloading CSV on every request
    """
    cache_key = 'games_dataframe'
    
    if use_cache:
        df = cache.get(cache_key)
        if df is not None:
            return df
    
    # Load CSV
    df = pd.read_csv(
        "games.csv",
        sep=',',
        quotechar='"',
        escapechar='\\',
        on_bad_lines="skip",
        engine='python'
    )
    
    # Clean column names
    df.columns = df.columns.str.strip().str.replace('"', '', regex=False)
    
    # Extract price and currency
    df[["price", "currency"]] = df["price_overview"].apply(
        lambda x: pd.Series(extract_price_and_currency(x))
    )
    
    # Convert to EUR
    df.loc[df['is_free'] == 1, 'price'] = 0
    df['price_eur'] = df.apply(convert_to_eur, axis=1)
    df['price_eur'] = df['price_eur'].fillna(0)
    df['price'] = df['price'].fillna(0)
    
    # Filter games only
    df_games = df[df["type"] == "game"].copy()
    
    # Cache for 1 hour
    if use_cache:
        cache.set(cache_key, df_games, 3600)
    
    return df_games