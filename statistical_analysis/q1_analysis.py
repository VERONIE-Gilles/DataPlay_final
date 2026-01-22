# analysis/q1_analysis.py

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from django.core.cache import cache
from util.chart_config import COLORS, get_base_layout, get_axis_style

# Excluded genres and canonical mappings
EXCLUDED_GENRES = {
    "Indie", "Early Access", "Free To Play", "Free to Play",
    "Utilities", "Software", "Animation & Modeling",
    "Design & Illustration", "Education", "Audio Production",
    "Video Production", "Web Publishing", "Accounting",
    "Photo Editing", "Game Development", "Tutorial"
}

CANONICAL_GENRES = {
    "Action": ["Actie", "Ackja", "Azione", "Action"],
    "Adventure": ["Aventura", "Abenteuer", "Aventure", "Avontuur", 
                  "Eventyr", "Avventura", "Seikkailu", "Adventure"],
    "RPG": ["Rollenspiel", "Rol", "GDR", "Roolipelit", "RPG"],
    "Strategy": ["Strategie", "Estrategia", "Strategia", "Strategi", "Strategy"],
    "Simulation": ["Simuladores", "Simulationen", "Simulatie", 
                   "Simulaatio", "Simulering", "Simulation"],
    "Casual": ["Gelegenheitsspiele", "Occasionnel", "Passatempo", "Casual"],
    "Racing": ["Carreras", "Course automobile", "Race", "Racing"],
    "Sports": ["Deportes", "Sport"],
    "Massively Multiplayer": ["Multijugador masivo", "Massivement multijoueur", 
                              "MMO", "Massively Multiplayer"],
}

def normalize_genre(raw_genre):
    """Normalize genre names to canonical form"""
    g = raw_genre.strip()
    for canonical, variants in CANONICAL_GENRES.items():
        for v in variants:
            if v in g:
                return canonical
    return None

def load_q1_data():
    """Load and process genres, tags, and reviews data"""
    cache_key = 'q1_data'
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Load CSVs
    df = pd.read_csv(
        "games.csv",
        sep=',',
        quotechar='"',
        escapechar='\\',
        on_bad_lines="skip",
        engine='python'
    )
    
    genres_df = pd.read_csv(
        "genres.csv",
        sep=",",
        quotechar='"',
        engine="python"
    )
    
    tags_df = pd.read_csv(
        "tags.csv",
        engine="python",
        sep=",",
        quotechar='"'
    )
    
    reviews_df = pd.read_csv(
        "reviews.csv",
        sep=",",
        engine="python",
        quoting=3,
        escapechar="\\",
        on_bad_lines="skip",
        encoding="utf-8",
    )
    
    # Clean column names
    df.columns = df.columns.str.strip().str.replace('"', '', regex=False)
    reviews_df.columns = reviews_df.columns.str.replace('"', '', regex=False)
    
    # Clean genres and tags
    genres_df["genre"] = genres_df["genre"].str.strip()
    tags_df["tag"] = tags_df["tag"].str.strip()
    
    # Get only games
    df_games = df[df["type"] == "game"][["app_id", "name"]].copy()
    
    # Merge with genres and tags
    genres_indie = genres_df.merge(df_games, on="app_id", how="inner")
    tags_indie = tags_df.merge(df_games, on="app_id", how="inner")
    
    # Filter and normalize genres
    genres_filtered = genres_indie[
        ~genres_indie["genre"].isin(EXCLUDED_GENRES)
    ].copy()
    genres_filtered["genre_normalized"] = genres_filtered["genre"].apply(normalize_genre)
    genres_clean = genres_filtered.dropna(subset=["genre_normalized"])
    
    # Clean reviews data
    for col in reviews_df.columns:
        reviews_df[col] = (
            reviews_df[col]
            .astype(str)
            .str.replace('"', '', regex=False)
            .replace('N', np.nan)
        )
    
    numeric_cols = ["positive", "negative", "total", "recommendations", "metacritic_score"]
    for col in numeric_cols:
        if col in reviews_df.columns:
            reviews_df[col] = pd.to_numeric(reviews_df[col], errors="coerce")
    
    reviews_df["app_id"] = pd.to_numeric(reviews_df["app_id"], errors="coerce")
    reviews_df = reviews_df.dropna(subset=["app_id"])
    reviews_df["app_id"] = reviews_df["app_id"].astype(int)
    
    # Cache for 1 hour
    result = {
        'genres_clean': genres_clean,
        'tags_indie': tags_indie,
        'reviews_df': reviews_df
    }
    cache.set(cache_key, result, 3600)
    
    return result

def create_genre_popularity_weighted():
    """Create chart showing genre popularity weighted by engagement (reviews)"""
    data = load_q1_data()
    genres_clean = data['genres_clean']
    reviews_df = data['reviews_df']
    
    # Merge genres with reviews
    genres_with_reviews = genres_clean.merge(
        reviews_df[["app_id", "total"]],
        on="app_id",
        how="left"
    )
    
    genres_with_reviews["total"] = genres_with_reviews["total"].fillna(0)
    
    # Calculate popularity
    genre_popularity = (
        genres_with_reviews
        .groupby("genre_normalized")
        .agg(
            games_count=("app_id", "nunique"),
            total_reviews=("total", "sum"),
            avg_reviews_per_game=("total", "mean")
        )
        .sort_values("total_reviews", ascending=True)
        .reset_index()
    )
    
    # Create colors - highlight top 3
    colors = [COLORS['primary_blue']] * len(genre_popularity)
    for i in range(max(0, len(colors) - 3), len(colors)):
        colors[i] = COLORS['accent_blue']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=genre_popularity["genre_normalized"],
        x=genre_popularity["total_reviews"],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color=COLORS['accent_blue'], width=1.5)
        ),
        text=[f'{int(val):,}' for val in genre_popularity["total_reviews"]],
        textposition='outside',
        textfont=dict(size=11, color=COLORS['text_white']),
        hovertemplate='<b>%{y}</b><br>' +
                      'Total Reviews: %{x:,}<br>' +
                      '<extra></extra>',
    ))
    
    layout = get_base_layout('Popularité des Genres Indie (Pondérée par l\'Engagement)', height=600)
    layout['xaxis'] = get_axis_style('Nombre total de reviews (engagement des joueurs)')
    layout['yaxis'] = get_axis_style('Genre', grid=False)
    layout['showlegend'] = False
    layout['margin'] = dict(t=80, b=60, l=150, r=100)
    
    fig.update_layout(**layout)
    
    return fig.to_html(include_plotlyjs='cdn', div_id='genre-weighted-chart')

def create_genre_count_chart():
    """Create chart showing genre popularity by game count"""
    data = load_q1_data()
    genres_clean = data['genres_clean']
    
    # Count games per genre
    genre_counts = (
        genres_clean["genre_normalized"]
        .value_counts()
        .reset_index()
    )
    genre_counts.columns = ["genre", "game_count"]
    genre_counts = genre_counts.sort_values("game_count", ascending=True)
    
    # Alternating colors, highlight top
    colors = [COLORS['light_blue'] if i % 2 == 0 else COLORS['primary_blue'] 
              for i in range(len(genre_counts))]
    colors[-1] = COLORS['accent_blue']  # Highlight top genre
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=genre_counts["genre"],
        x=genre_counts["game_count"],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color=COLORS['accent_blue'], width=1.5)
        ),
        text=[f'{int(val):,}' for val in genre_counts["game_count"]],
        textposition='outside',
        textfont=dict(size=11, color=COLORS['text_white']),
        hovertemplate='<b>%{y}</b><br>' +
                      'Nombre de jeux: %{x:,}<br>' +
                      '<extra></extra>',
    ))
    
    layout = get_base_layout('Popularité des Genres de Jeux Indie', height=600)
    layout['xaxis'] = get_axis_style('Nombre de jeux indie')
    layout['yaxis'] = get_axis_style('Genre', grid=False)
    layout['showlegend'] = False
    layout['margin'] = dict(t=80, b=60, l=150, r=100)
    
    fig.update_layout(**layout)
    
    return fig.to_html(include_plotlyjs='cdn', div_id='genre-count-chart')

def create_top_tags_chart():
    """Create chart showing top 20 most popular tags"""
    data = load_q1_data()
    tags_indie = data['tags_indie']
    
    # Count tags
    tag_counts = (
        tags_indie["tag"]
        .value_counts()
        .reset_index()
    )
    tag_counts.columns = ["tag", "game_count"]
    top_tags = tag_counts.head(20)
    
    # Color top 5 tags differently
    max_count = top_tags["game_count"].max()
    colors = [COLORS['accent_blue'] if count > max_count * 0.7 
              else COLORS['primary_blue'] for count in top_tags["game_count"]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=top_tags["tag"],
        y=top_tags["game_count"],
        marker=dict(
            color=colors,
            line=dict(color=COLORS['accent_blue'], width=1.5)
        ),
        text=[f'{int(val):,}' for val in top_tags["game_count"]],
        textposition='outside',
        textfont=dict(size=10, color=COLORS['text_white']),
        hovertemplate='<b>%{x}</b><br>' +
                      'Nombre de jeux: %{y:,}<br>' +
                      '<extra></extra>',
    ))
    
    layout = get_base_layout('Top 20 des Tags les Plus Populaires', height=600)
    layout['xaxis'] = get_axis_style('Tag', grid=False)
    layout['xaxis']['tickangle'] = -45
    layout['yaxis'] = get_axis_style('Nombre de jeux indie')
    layout['showlegend'] = False
    layout['margin'] = dict(t=80, b=150, l=60, r=40)
    
    fig.update_layout(**layout)
    
    return fig.to_html(include_plotlyjs='cdn', div_id='tags-chart')

def get_q1_statistics():
    """Calculate Q1 statistics"""
    data = load_q1_data()
    genres_clean = data['genres_clean']
    tags_indie = data['tags_indie']
    reviews_df = data['reviews_df']
    
    # Merge for weighted stats
    genres_with_reviews = genres_clean.merge(
        reviews_df[["app_id", "total"]],
        on="app_id",
        how="left"
    )
    genres_with_reviews["total"] = genres_with_reviews["total"].fillna(0)
    
    genre_popularity = (
        genres_with_reviews
        .groupby("genre_normalized")
        .agg(
            games_count=("app_id", "nunique"),
            total_reviews=("total", "sum")
        )
        .sort_values("total_reviews", ascending=False)
    )
    
    genre_counts = genres_clean["genre_normalized"].value_counts()
    tag_counts = tags_indie["tag"].value_counts()
    
    return {
        'total_genres': len(genre_counts),
        'total_tags': len(tag_counts),
        'most_popular_genre': genre_counts.index[0] if len(genre_counts) > 0 else "N/A",
        'most_popular_tag': tag_counts.index[0] if len(tag_counts) > 0 else "N/A",
        'most_engaged_genre': genre_popularity.index[0] if len(genre_popularity) > 0 else "N/A",
        'top_genre_count': int(genre_counts.iloc[0]) if len(genre_counts) > 0 else 0,
        'top_tag_count': int(tag_counts.iloc[0]) if len(tag_counts) > 0 else 0,
    }