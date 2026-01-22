# utils/chart_config.py

# Your color scheme - used across all charts
COLORS = {
    'bg_dark': '#0a0e1a',
    'bg_darker': '#000814',
    'dark_blue': '#0a2540',
    'primary_blue': '#1e90ff',
    'accent_blue': '#00d4ff',
    'light_blue': '#4dabf7',
    'text_light': '#e0e0e0',
    'text_white': '#ffffff',
}

def get_base_layout(title, height=600):
    """
    Returns base Plotly layout configuration
    Use this for consistent styling across all charts
    """
    return {
        'title': {
            'text': title,
            'font': {'size': 20, 'color': COLORS['text_white'], 'family': 'Segoe UI'},
            'x': 0.5,
            'xanchor': 'center'
        },
        'plot_bgcolor': COLORS['dark_blue'],
        'paper_bgcolor': COLORS['bg_dark'],
        'font': dict(family='Segoe UI', color=COLORS['text_light']),
        'hovermode': 'closest',
        'height': height,
        'margin': dict(t=80, b=60, l=60, r=40)
    }

def get_axis_style(title, grid=True):
    """Returns axis styling configuration"""
    config = {
        'title': title,
        'color': COLORS['text_light'],
    }
    if grid:
        config.update({
            'gridcolor': COLORS['primary_blue'],
            'gridwidth': 0.5
        })
    return config