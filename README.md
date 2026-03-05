# ⚾ Fantasy Baseball AI Advisor

AI-powered recommendations for your ESPN fantasy baseball league — waiver wire pickups, start/sit decisions, trade suggestions, and lineup optimization.

## Setup

### 1. Deploy on Streamlit Cloud
- Go to [share.streamlit.io](https://share.streamlit.io)
- Connect this GitHub repo
- Set main file path to `fantasy_app.py`

### 2. Add your secrets
In Streamlit Cloud, go to **App Settings → Secrets** and add:

```toml
ANTHROPIC_API_KEY = "your_anthropic_key"
```

Your ESPN League ID, cookies, and team name are entered directly in the app sidebar.

### 3. Get your ESPN cookies (private leagues only)
- Log into ESPN in Safari or Chrome
- Open DevTools → Application → Cookies → espn.com
- Copy `espn_s2` and `SWID`

## File Structure
```
fantasy-baseball-advisor/
├── fantasy_app.py          # Main Streamlit app
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml         # Streamlit theme config
├── .gitignore
└── README.md
```
