"""
ESPN Fantasy Baseball AI Advisor — Streamlit App
=================================================
Run with: streamlit run fantasy_app.py
"""

import streamlit as st
from espn_api.baseball import League
import anthropic
import database
import auth

# Initialise DB (no-op if already created)
database.init_db()

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Fantasy Baseball Advisor",
    page_icon="⚾",
    layout="wide",
)

# ─────────────────────────────────────────────
#  CUSTOM STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Dark stadium background */
.stApp {
    background: #0a0e1a;
    color: #e8e8e8;
}

/* Header */
.hero {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a2744 50%, #0d1b2a 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "⚾";
    position: absolute;
    right: 2rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 6rem;
    opacity: 0.08;
}
.hero h1 {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3rem;
    letter-spacing: 3px;
    color: #ffffff;
    margin: 0;
    line-height: 1;
}
.hero p {
    color: #7a9cc0;
    margin: 0.4rem 0 0 0;
    font-size: 1rem;
}

/* Stat cards */
.stat-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.stat-card {
    background: #111827;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 1rem 1.4rem;
    flex: 1;
}
.stat-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #4a7fa5;
    margin-bottom: 0.3rem;
}
.stat-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.8rem;
    color: #e8f4fd;
    letter-spacing: 1px;
}

/* Section headers */
.section-header {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.4rem;
    letter-spacing: 2px;
    color: #5ba3d9;
    border-bottom: 1px solid #1e3a5f;
    padding-bottom: 0.5rem;
    margin: 1.5rem 0 1rem 0;
}

/* Roster table */
.roster-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.88rem;
}
.roster-table th {
    background: #0d1b2a;
    color: #4a7fa5;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    padding: 0.6rem 0.8rem;
    text-align: left;
    border-bottom: 1px solid #1e3a5f;
}
.roster-table td {
    padding: 0.55rem 0.8rem;
    border-bottom: 1px solid #131f2e;
    color: #c8d8e8;
}
.roster-table tr:hover td {
    background: #111827;
}
.injury-tag {
    background: #3d1a1a;
    color: #f87171;
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 0.7rem;
    font-weight: 600;
}

/* AI recommendation cards */
.rec-card {
    background: #111827;
    border: 1px solid #1e3a5f;
    border-left: 4px solid #3b82f6;
    border-radius: 0 10px 10px 0;
    padding: 1.5rem;
    margin-bottom: 1rem;
    white-space: pre-wrap;
    line-height: 1.7;
    font-size: 0.92rem;
    color: #c8d8e8;
}

/* Standings */
.standing-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0.8rem;
    border-bottom: 1px solid #131f2e;
    font-size: 0.88rem;
}
.standing-row:hover { background: #111827; border-radius: 6px; }
.standing-rank {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.2rem;
    color: #3b82f6;
    width: 2rem;
}
.standing-name { flex: 1; color: #c8d8e8; }
.standing-record { color: #4a7fa5; font-size: 0.82rem; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 2rem !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.1rem !important;
    letter-spacing: 2px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
    transform: translateY(-1px) !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0d1b2a !important;
    border-right: 1px solid #1e3a5f !important;
}
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: #111827 !important;
    border: 1px solid #1e3a5f !important;
    color: #e8e8e8 !important;
    border-radius: 8px !important;
}

/* Free agents */
.fa-card {
    background: #111827;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    margin-bottom: 0.4rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.88rem;
}
.fa-name { color: #c8d8e8; font-weight: 500; }
.fa-pos {
    background: #1e3a5f;
    color: #7ab8e8;
    border-radius: 4px;
    padding: 1px 8px;
    font-size: 0.75rem;
    font-weight: 600;
}
.fa-proj { color: #4a7fa5; font-size: 0.82rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SESSION STATE DEFAULTS
# ─────────────────────────────────────────────
_DEFAULTS = {
    "user_id":        None,
    "username":       None,
    "s_league_id":    "1740864810",
    "s_year":         2025,
    "s_espn_s2":      "",
    "s_swid":         "",
    "s_api_key":      "",
    "s_team_name":    "",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─────────────────────────────────────────────
#  SIDEBAR — AUTH + CONFIG
# ─────────────────────────────────────────────
with st.sidebar:

    # ── User account ──────────────────────────
    if st.session_state.user_id:
        st.markdown(f"### 👤 {st.session_state.username}")

        if st.button("📥 Load Saved Settings", use_container_width=True):
            settings = auth.load_settings(st.session_state.user_id)
            if settings:
                st.session_state.s_league_id = settings["league_id"]
                st.session_state.s_year      = settings["season_year"]
                st.session_state.s_espn_s2   = settings["espn_s2"]
                st.session_state.s_swid      = settings["swid"]
                st.session_state.s_api_key   = settings["api_key"]
                st.session_state.s_team_name = settings["team_name_filter"]
                st.success("Settings loaded!")
                st.rerun()
            else:
                st.info("No saved settings found.")

        if st.button("💾 Save Current Settings", use_container_width=True):
            auth.save_settings(
                st.session_state.user_id,
                st.session_state.get("s_league_id", ""),
                int(st.session_state.get("s_year", 2025)),
                st.session_state.get("s_espn_s2", ""),
                st.session_state.get("s_swid", ""),
                st.session_state.get("s_api_key", ""),
                st.session_state.get("s_team_name", ""),
            )
            st.success("Settings saved!")

        if st.button("🚪 Log Out", use_container_width=True):
            for _k in ("user_id", "username"):
                st.session_state[_k] = None
            st.rerun()

    else:
        st.markdown("### 🔐 Account")
        _tab_login, _tab_reg = st.tabs(["Log In", "Register"])

        with _tab_login:
            _lu = st.text_input("Username", key="_login_user")
            _lp = st.text_input("Password", type="password", key="_login_pass")
            if st.button("Log In", use_container_width=True):
                if _lu and _lp:
                    _ok, _uid, _msg = auth.login_user(_lu, _lp)
                    if _ok:
                        st.session_state.user_id  = _uid
                        st.session_state.username = _lu.strip()
                        st.rerun()
                    else:
                        st.error(_msg)
                else:
                    st.warning("Please fill in both fields.")

        with _tab_reg:
            _ru = st.text_input("Choose a username", key="_reg_user")
            _rp = st.text_input("Choose a password", type="password", key="_reg_pass")
            _rp2 = st.text_input("Confirm password", type="password", key="_reg_pass2")
            if st.button("Create Account", use_container_width=True):
                if not (_ru and _rp and _rp2):
                    st.warning("Please fill in all fields.")
                elif _rp != _rp2:
                    st.error("Passwords do not match.")
                else:
                    _ok, _msg = auth.register_user(_ru, _rp)
                    if _ok:
                        st.success(_msg)
                    else:
                        st.error(_msg)

    st.markdown("---")

    # ── League configuration ──────────────────
    st.markdown("### ⚙️ Configuration")
    league_id        = st.text_input("League ID", key="s_league_id")
    year             = st.number_input("Season Year", min_value=2020, max_value=2026,
                                       step=1, key="s_year")
    espn_s2          = st.text_input("espn_s2 cookie", type="password",
                                     key="s_espn_s2",
                                     help="Required for private leagues")
    swid             = st.text_input("SWID cookie", type="password",
                                     key="s_swid",
                                     help="Required for private leagues")
    api_key          = st.text_input("Anthropic API Key", type="password",
                                     key="s_api_key")
    st.markdown("---")
    st.markdown("##### Your Team")
    team_name_filter = st.text_input("Team name (partial match)",
                                     placeholder="Leave blank to select",
                                     key="s_team_name")
    st.markdown("---")
    st.caption("Cookies only needed for private leagues. "
               "Get them from browser DevTools → Application → Cookies → espn.com")


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_league(league_id, year, espn_s2, swid):
    kwargs = {"league_id": int(league_id), "year": int(year)}
    if espn_s2 and swid:
        kwargs["espn_s2"] = espn_s2
        kwargs["swid"]    = swid
    return League(**kwargs)


def find_team(league, name_filter):
    if not name_filter:
        return None
    matches = [t for t in league.teams if name_filter.lower() in t.team_name.lower()]
    return matches[0] if matches else None


def get_roster_data(team):
    rows = []
    for p in team.roster:
        injury = getattr(p, "injuryStatus", "ACTIVE")
        rows.append({
            "name":    p.name,
            "pos":     p.position,
            "proj":    round(p.projected_total_points, 1),
            "injury":  injury if injury not in ("ACTIVE", "NORMAL", None) else "",
        })
    return rows


def get_free_agents(league, size=25):
    try:
        fas = league.free_agents(size=size)
        return [{"name": fa.name, "pos": fa.position, "proj": round(fa.projected_total_points, 1)} for fa in fas[:15]]
    except:
        return []


def get_matchup(league, team):
    try:
        for box in league.box_scores():
            if box.home_team == team or box.away_team == team:
                opp       = box.away_team  if box.home_team == team else box.home_team
                my_score  = box.home_score if box.home_team == team else box.away_score
                opp_score = box.away_score if box.home_team == team else box.home_score
                return {"opponent": opp.team_name, "my_score": round(my_score, 1), "opp_score": round(opp_score, 1)}
    except:
        pass
    return None


def build_context(team, league, my_team):
    roster_lines = "\n".join(
        f"  {p['name']:<25} | {p['pos']:<5} | Proj: {p['proj']} pts"
        + (f" [{p['injury']}]" if p['injury'] else "")
        for p in get_roster_data(my_team)
    )
    standings_lines = "\n".join(
        f"  {i}. {t.team_name:<25} | W:{t.wins} L:{t.losses} | Standing: {t.standing}"
        for i, t in enumerate(sorted(league.teams, key=lambda t: t.wins, reverse=True), 1)
    )
    fa_lines = "\n".join(
        f"  {fa['name']:<25} | {fa['pos']:<5} | Proj: {fa['proj']} pts"
        for fa in get_free_agents(league)
    )
    matchup = get_matchup(league, my_team)
    matchup_str = (
        f"  {my_team.team_name} ({matchup['my_score']}) vs {matchup['opponent']} ({matchup['opp_score']})"
        if matchup else "  Could not retrieve matchup."
    )
    return roster_lines, standings_lines, fa_lines, matchup_str


def get_ai_advice(roster, standings, fa, matchup, api_key):
    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""You are an expert fantasy baseball analyst. Based on the league data below,
provide specific actionable recommendations. Name actual players and be direct.

=== MY ROSTER ===
{roster}

=== STANDINGS ===
{standings}

=== FREE AGENTS ===
{fa}

=== CURRENT MATCHUP ===
{matchup}

Respond in exactly these four sections with clear markdown headers:

## 🔄 Waiver Wire Pickups
Best free agents to pick up and what needs they address.

## 🏟️ Start / Sit Decisions
Who to start vs sit this week and why.

## 🤝 Trade Suggestions
Trades to pursue — who to target and what to offer.

## 📋 Lineup Optimization
How to optimize the lineup. Flag injured or underperforming players."""

    with st.spinner("🤖 Analyzing your league..."):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
    return response.content[0].text


# ─────────────────────────────────────────────
#  MAIN UI
# ─────────────────────────────────────────────

st.markdown("""
<div class="hero">
    <h1>Fantasy Baseball Advisor</h1>
    <p>AI-powered recommendations for your ESPN league</p>
</div>
""", unsafe_allow_html=True)

if not league_id or league_id == "0":
    st.info("👈 Enter your League ID in the sidebar to get started.")
    st.stop()

# Load league
try:
    with st.spinner("Connecting to ESPN..."):
        league = load_league(league_id, year, espn_s2, swid)
except Exception as e:
    st.error(f"❌ Could not connect: {e}")
    st.stop()

# Team selection
my_team = find_team(league, team_name_filter)
if not my_team:
    team_options = {t.team_name: t for t in league.teams}
    selected = st.selectbox("Select your team", list(team_options.keys()))
    my_team = team_options[selected]

# ── Stats bar ──
matchup = get_matchup(league, my_team)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="stat-card"><div class="stat-label">League</div>
    <div class="stat-value" style="font-size:1.1rem;margin-top:4px">{league.settings.name}</div></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="stat-card"><div class="stat-label">Your Team</div>
    <div class="stat-value" style="font-size:1.1rem;margin-top:4px">{my_team.team_name}</div></div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="stat-card"><div class="stat-label">Record</div>
    <div class="stat-value">{my_team.wins}–{my_team.losses}</div></div>""", unsafe_allow_html=True)
with col4:
    opp_str = matchup['opponent'] if matchup else "N/A"
    st.markdown(f"""<div class="stat-card"><div class="stat-label">This Week vs</div>
    <div class="stat-value" style="font-size:1.1rem;margin-top:4px">{opp_str}</div></div>""", unsafe_allow_html=True)

# ── Two column layout ──
left, right = st.columns([3, 2])

with left:
    # Roster
    st.markdown('<div class="section-header">📋 Current Roster</div>', unsafe_allow_html=True)
    roster_data = get_roster_data(my_team)
    rows_html = ""
    for p in roster_data:
        injury_html = f'<span class="injury-tag">{p["injury"]}</span>' if p["injury"] else ""
        rows_html += f"""<tr>
            <td>{p['name']} {injury_html}</td>
            <td>{p['pos']}</td>
            <td>{p['proj']}</td>
        </tr>"""
    st.markdown(f"""
    <table class="roster-table">
        <thead><tr><th>Player</th><th>Position</th><th>Proj Pts</th></tr></thead>
        <tbody>{rows_html}</tbody>
    </table>""", unsafe_allow_html=True)

with right:
    # Standings
    st.markdown('<div class="section-header">🏆 Standings</div>', unsafe_allow_html=True)
    sorted_teams = sorted(league.teams, key=lambda t: t.wins, reverse=True)
    for i, team in enumerate(sorted_teams, 1):
        highlight = "border-left: 3px solid #3b82f6; padding-left: 0.5rem;" if team == my_team else ""
        st.markdown(f"""
        <div class="standing-row" style="{highlight}">
            <span class="standing-rank">{i}</span>
            <span class="standing-name">{team.team_name}</span>
            <span class="standing-record">{team.wins}–{team.losses}</span>
        </div>""", unsafe_allow_html=True)

    # Free agents
    st.markdown('<div class="section-header">🔄 Top Free Agents</div>', unsafe_allow_html=True)
    fas = get_free_agents(league)
    for fa in fas:
        st.markdown(f"""
        <div class="fa-card">
            <span class="fa-name">{fa['name']}</span>
            <span class="fa-pos">{fa['pos']}</span>
            <span class="fa-proj">{fa['proj']} pts</span>
        </div>""", unsafe_allow_html=True)

# ── AI Recommendations ──
st.markdown("---")
if not api_key:
    st.warning("👈 Enter your Anthropic API key in the sidebar to get AI recommendations.")
else:
    if st.button("⚾  GET AI RECOMMENDATIONS"):
        roster_ctx, standings_ctx, fa_ctx, matchup_ctx = build_context(None, league, my_team)
        advice = get_ai_advice(roster_ctx, standings_ctx, fa_ctx, matchup_ctx, api_key)

        # Parse and display sections
        sections = advice.split("##")
        for section in sections:
            section = section.strip()
            if not section:
                continue
            lines   = section.split("\n", 1)
            title   = lines[0].strip()
            content = lines[1].strip() if len(lines) > 1 else ""
            st.markdown(f"### {title}")
            st.markdown(f'<div class="rec-card">{content}</div>', unsafe_allow_html=True)
