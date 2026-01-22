# analysis/q3_analysis.py

import pandas as pd
import numpy as np
import re
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from django.core.cache import cache
from util.chart_config import COLORS, get_base_layout, get_axis_style

# Canonical language mappings
CANONICAL_LANGUAGES = {
    "English": ["english", "anglais", "englisch", "англий", "英"],
    "Chinese": ["chinese", "中文", "简体", "繁体", "chine"],
    "Russian": ["russian", "рус", "rosyj", "russe"],
    "Japanese": ["japanese", "日本", "japon", "giappon"],
    "Korean": ["korean", "한국", "coré"],
    "Spanish": ["spanish", "españ", "espagn", "hiszp"],
    "French": ["french", "français", "francus", "franz"],
    "German": ["german", "deutsch", "allemand", "niemie"],
    "Portuguese": ["portuguese", "português", "portug"],
    "Italian": ["italian", "italiano", "italien"],
}

def clean_language(lang):
    """Clean and normalize language strings"""
    if pd.isna(lang):
        return None
    
    lang = lang.lower()
    
    # Remove common noise phrases
    lang = re.sub(r'languages with full audio support', '', lang)
    lang = re.sub(r'full audio support', '', lang)
    lang = re.sub(r'idiomas con.*', '', lang)
    lang = re.sub(r'langues avec.*', '', lang)
    lang = re.sub(r'sprachen mit.*', '', lang)
    
    # Remove HTML tags, brackets, symbols
    lang = re.sub(r'<.*?>', '', lang)
    lang = re.sub(r'\[.*?\]', '', lang)
    lang = re.sub(r'[^a-zA-Z\u4e00-\u9fff\u0400-\u04FF\s]', '', lang)
    
    # Normalize spaces
    lang = re.sub(r'\s+', ' ', lang).strip()
    
    return lang

def normalize_language(lang):
    """Map language to canonical form"""
    if not lang:
        return None
    
    for canonical, variants in CANONICAL_LANGUAGES.items():
        for v in variants:
            if v in lang:
                return canonical
    return "Other"

def load_q3_data():
    """Load and process language and engagement data"""
    cache_key = 'q3_data'
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Load CSVs
    games_df = pd.read_csv(
        "games.csv",
        sep=",",
        quotechar='"',
        escapechar="\\",
        engine="python",
        on_bad_lines="skip"
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
    games_df.columns = games_df.columns.str.strip().str.replace('"', '', regex=False)
    reviews_df.columns = reviews_df.columns.str.replace('"', '', regex=False)
    
    # Clean reviews data
    reviews_df["app_id"] = reviews_df["app_id"].astype(str).str.replace('"', '', regex=False)
    reviews_df["total"] = reviews_df["total"].astype(str).str.replace('"', '', regex=False)
    reviews_df["app_id"] = pd.to_numeric(reviews_df["app_id"], errors="coerce")
    reviews_df["total"] = pd.to_numeric(reviews_df["total"], errors="coerce")
    reviews_df = reviews_df.dropna(subset=["app_id"])
    reviews_df["app_id"] = reviews_df["app_id"].astype(int)
    
    # Keep only games
    games_df = games_df[games_df["type"] == "game"]
    games_df = games_df[["app_id", "languages"]]
    games_df = games_df.dropna(subset=["languages"])
    
    # Clean language strings
    games_df["languages"] = (
        games_df["languages"]
        .str.replace(r"<.*?>", "", regex=True)
        .str.replace("*", "", regex=False)
    )
    
    # Split languages into rows
    languages_df = (
        games_df
        .assign(language=games_df["languages"].str.split(","))
        .explode("language")
    )
    
    languages_df["language"] = languages_df["language"].str.strip()
    languages_df["language_clean"] = languages_df["language"].apply(clean_language)
    languages_df["language_normalized"] = languages_df["language_clean"].apply(normalize_language)
    
    # Merge with reviews
    languages_reviews = languages_df.merge(
        reviews_df[["app_id", "total"]],
        on="app_id",
        how="left"
    )
    languages_reviews["total"] = languages_reviews["total"].fillna(0)
    
    # Cache for 1 hour
    result = {
        'languages_df': languages_df,
        'languages_reviews': languages_reviews
    }
    cache.set(cache_key, result, 3600)
    
    return result

def create_language_engagement_chart():
    """Create horizontal bar chart showing language engagement share"""
    data = load_q3_data()
    languages_reviews = data['languages_reviews']
    
    # Calculate engagement
    language_engagement = (
        languages_reviews
        .groupby("language_normalized")["total"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    
    # Remove "Other" and calculate share
    language_engagement_no_other = language_engagement[
        language_engagement["language_normalized"] != "Other"
    ]
    total_engagement = language_engagement_no_other["total"].sum()
    language_engagement_no_other["share"] = (
        language_engagement_no_other["total"] / total_engagement * 100
    )
    
    # Sort for plotting
    language_engagement_no_other = language_engagement_no_other.sort_values("share", ascending=True)
    
    # Create gradient colors
    colors = []
    shares = language_engagement_no_other["share"].values
    max_share = shares.max()
    
    for share in shares:
        if share > max_share * 0.85:
            colors.append(COLORS['accent_blue'])
        elif share > max_share * 0.60:
            colors.append(COLORS['primary_blue'])
        else:
            colors.append(COLORS['light_blue'])
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=language_engagement_no_other["language_normalized"],
        x=language_engagement_no_other["share"],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color=COLORS['accent_blue'], width=1.5)
        ),
        text=[f'{val:.1f}%' for val in language_engagement_no_other["share"]],
        textposition='outside',
        textfont=dict(size=11, color=COLORS['text_white']),
        hovertemplate='<b>%{y}</b><br>' +
                      'Part d\'engagement: %{x:.2f}%<br>' +
                      '<extra></extra>',
    ))
    
    layout = get_base_layout('Engagement des Jeux Indie par Langue', height=700)
    layout['xaxis'] = get_axis_style('Part de l\'engagement total (%)')
    layout['yaxis'] = get_axis_style('Langue', grid=False)
    layout['showlegend'] = False
    layout['margin'] = dict(t=80, b=60, l=120, r=120)
    
    fig.update_layout(**layout)
    
    return fig.to_html(include_plotlyjs='cdn', div_id='language-engagement-chart')

def create_language_pie_chart():
    """Create pie chart showing top languages by engagement"""
    data = load_q3_data()
    languages_reviews = data['languages_reviews']
    
    # Calculate engagement
    language_engagement = (
        languages_reviews
        .groupby("language_normalized")["total"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    
    # Get top 10 languages (excluding "Other")
    top_languages = language_engagement[
        language_engagement["language_normalized"] != "Other"
    ].head(10)
    
    # Custom colors
    colors_list = [
        COLORS['accent_blue'],
        COLORS['primary_blue'],
        COLORS['light_blue'],
        '#4169e1',
        '#6495ed',
        '#87ceeb',
        '#00bfff',
        '#1e90ff',
        '#4dabf7',
        '#00d4ff'
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Pie(
        labels=top_languages["language_normalized"],
        values=top_languages["total"],
        marker=dict(
            colors=colors_list[:len(top_languages)],
            line=dict(color=COLORS['bg_dark'], width=2)
        ),
        textinfo='label+percent',
        textfont=dict(size=12, color=COLORS['text_white']),
        hovertemplate='<b>%{label}</b><br>' +
                      'Reviews totales: %{value:,}<br>' +
                      'Pourcentage: %{percent}<br>' +
                      '<extra></extra>',
        pull=[0.05, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ))
    
    fig.update_layout(
        title={
            'text': 'Top 10 des Langues par Engagement',
            'font': {'size': 20, 'color': COLORS['text_white'], 'family': 'Segoe UI'},
            'x': 0.5,
            'xanchor': 'center'
        },
        plot_bgcolor=COLORS['dark_blue'],
        paper_bgcolor=COLORS['bg_dark'],
        font=dict(family='Segoe UI', color=COLORS['text_light']),
        height=600,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            font=dict(size=11, color=COLORS['text_light']),
            bgcolor='rgba(0,0,0,0)'
        ),
        margin=dict(t=80, b=60, l=60, r=200)
    )
    
    return fig.to_html(include_plotlyjs='cdn', div_id='language-pie-chart')

def create_cumulative_engagement_chart():
    """Create line chart showing cumulative language engagement"""
    data = load_q3_data()
    languages_reviews = data['languages_reviews']
    
    # Calculate engagement
    language_engagement = (
        languages_reviews
        .groupby("language_normalized")["total"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    
    # Remove "Other" and calculate share
    language_engagement_no_other = language_engagement[
        language_engagement["language_normalized"] != "Other"
    ]
    total_engagement = language_engagement_no_other["total"].sum()
    language_engagement_no_other["share"] = (
        language_engagement_no_other["total"] / total_engagement * 100
    )
    language_engagement_no_other["cumulative_share"] = (
        language_engagement_no_other["share"].cumsum()
    )
    
    fig = go.Figure()
    
    # Add line
    fig.add_trace(go.Scatter(
        x=list(range(1, len(language_engagement_no_other) + 1)),
        y=language_engagement_no_other["cumulative_share"],
        mode='lines+markers',
        line=dict(color=COLORS['accent_blue'], width=3),
        marker=dict(size=8, color=COLORS['primary_blue'], line=dict(color=COLORS['accent_blue'], width=2)),
        hovertemplate='<b>Top %{x} langues</b><br>' +
                      'Engagement cumulé: %{y:.1f}%<br>' +
                      '<extra></extra>',
    ))
    
    # Add reference lines
    fig.add_hline(y=50, line_dash="dash", line_color=COLORS['text_light'], 
                  annotation_text="50%", annotation_position="right")
    fig.add_hline(y=80, line_dash="dash", line_color=COLORS['text_light'], 
                  annotation_text="80%", annotation_position="right")
    
    layout = get_base_layout('Engagement Cumulé par Langue', height=600)
    layout['xaxis'] = get_axis_style('Nombre de langues (classées par engagement)')
    layout['yaxis'] = get_axis_style('Engagement cumulé (%)')
    layout['yaxis']['range'] = [0, 105]
    layout['showlegend'] = False
    
    fig.update_layout(**layout)
    
    return fig.to_html(include_plotlyjs='cdn', div_id='cumulative-chart')

def create_language_game_count_chart():
    """Create bar chart showing number of games per language"""
    data = load_q3_data()
    languages_df = data['languages_df']
    
    # Count games per language
    language_game_counts = (
        languages_df
        .groupby("language_normalized")["app_id"]
        .nunique()
        .sort_values(ascending=False)
        .reset_index()
    )
    language_game_counts.columns = ["language", "game_count"]
    
    # Remove "Other" and get top 10
    top_languages = language_game_counts[
        language_game_counts["language"] != "Other"
    ].head(10).sort_values("game_count", ascending=True)
    
    # Colors
    colors = [COLORS['light_blue'] if i % 2 == 0 else COLORS['primary_blue'] 
              for i in range(len(top_languages))]
    colors[-1] = COLORS['accent_blue']  # Highlight top
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=top_languages["language"],
        x=top_languages["game_count"],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color=COLORS['accent_blue'], width=1.5)
        ),
        text=[f'{int(val):,}' for val in top_languages["game_count"]],
        textposition='outside',
        textfont=dict(size=11, color=COLORS['text_white']),
        hovertemplate='<b>%{y}</b><br>' +
                      'Nombre de jeux: %{x:,}<br>' +
                      '<extra></extra>',
    ))
    
    layout = get_base_layout('Nombre de Jeux par Langue (Top 10)', height=600)
    layout['xaxis'] = get_axis_style('Nombre de jeux')
    layout['yaxis'] = get_axis_style('Langue', grid=False)
    layout['showlegend'] = False
    layout['margin'] = dict(t=80, b=60, l=120, r=100)
    
    fig.update_layout(**layout)
    
    return fig.to_html(include_plotlyjs='cdn', div_id='language-count-chart')

def get_q3_statistics():
    """Calculate Q3 statistics"""
    data = load_q3_data()
    languages_df = data['languages_df']
    languages_reviews = data['languages_reviews']
    
    # Total languages
    total_languages = len(languages_df["language_normalized"].unique()) - 1  # Exclude "Other"
    
    # Total games with language data
    total_games = languages_df["app_id"].nunique()
    
    # Calculate engagement
    language_engagement = (
        languages_reviews
        .groupby("language_normalized")["total"]
        .sum()
        .sort_values(ascending=False)
    )
    
    language_engagement_no_other = language_engagement[
        language_engagement.index != "Other"
    ]
    total_engagement = language_engagement_no_other.sum()
    
    # Top language
    top_language = language_engagement_no_other.index[0]
    top_language_share = (language_engagement_no_other.iloc[0] / total_engagement * 100)
    
    # Count games per language
    language_game_counts = languages_df.groupby("language_normalized")["app_id"].nunique()
    language_game_counts_no_other = language_game_counts[language_game_counts.index != "Other"]
    most_common_language = language_game_counts_no_other.idxmax()
    most_common_count = int(language_game_counts_no_other.max())
    
    # Calculate cumulative for top N
    shares = (language_engagement_no_other / total_engagement * 100).values
    top_3_cumulative = shares[:3].sum()
    top_5_cumulative = shares[:5].sum()
    
    return {
        'total_languages': int(total_languages),
        'total_games': int(total_games),
        'top_language': top_language,
        'top_language_share': float(top_language_share),
        'most_common_language': most_common_language,
        'most_common_count': most_common_count,
        'top_3_cumulative': float(top_3_cumulative),
        'top_5_cumulative': float(top_5_cumulative),
    }