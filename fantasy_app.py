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

# Initialise DB (idempotent)
database.init_db()

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Fantasy Baseball Advisor",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  SHARED STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp { background: #0a0e1a; color: #e8e8e8; }

/* ── Login page ── */
.login-wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 80vh;
}

/* ── Profile cards ── */
.profile-card {
    background: #111827;
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    margin-bottom: 0.5rem;
}
.profile-card:hover { border-color: #3b82f6; }
.profile-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.25rem;
    letter-spacing: 1.5px;
    color: #ffffff;
    margin-bottom: 0.1rem;
}
.profile-meta { color: #4a7fa5; font-size: 0.82rem; }

/* ── Hero banner (dashboard) ── */
.hero {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a2744 50%, #0d1b2a 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 1.6rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "⚾";
    position: absolute;
    right: 2rem; top: 50%;
    transform: translateY(-50%);
    font-size: 6rem;
    opacity: 0.08;
}
.hero h1 {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.6rem;
    letter-spacing: 3px;
    color: #ffffff;
    margin: 0;
    line-height: 1;
}
.hero p { color: #7a9cc0; margin: 0.3rem 0 0; font-size: 0.95rem; }

/* ── Stat cards ── */
.stat-card {
    background: #111827;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 1rem 1.4rem;
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

/* ── Section headers ── */
.section-header {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.4rem;
    letter-spacing: 2px;
    color: #5ba3d9;
    border-bottom: 1px solid #1e3a5f;
    padding-bottom: 0.5rem;
    margin: 1.5rem 0 1rem;
}

/* ── Roster table ── */
.roster-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
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
.roster-table tr:hover td { background: #111827; }
.injury-tag {
    background: #3d1a1a;
    color: #f87171;
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 0.7rem;
    font-weight: 600;
}

/* ── AI rec cards ── */
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

/* ── Standings ── */
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

/* ── Free agents ── */
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

/* ── Buttons ── */
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

/* ── Inputs ── */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background: #111827 !important;
    border: 1px solid #1e3a5f !important;
    color: #e8e8e8 !important;
    border-radius: 8px !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0d1b2a !important;
    border-right: 1px solid #1e3a5f !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SESSION STATE DEFAULTS
# ─────────────────────────────────────────────
_SS_DEFAULTS = {
    "page":             "login",   # login | profiles | dashboard
    "user_id":          None,
    "username":         None,
    "active_profile":   None,      # decrypted profile dict
    "editing_profile":  False,
}
for _k, _v in _SS_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─────────────────────────────────────────────
#  NAVIGATION HELPERS
# ─────────────────────────────────────────────
def go_to(page: str):
    st.session_state.page = page
    st.rerun()


def logout():
    for k, v in _SS_DEFAULTS.items():
        st.session_state[k] = v
    st.rerun()


# ═════════════════════════════════════════════
#  PAGE 1 — LOGIN / REGISTER
# ═════════════════════════════════════════════
def render_login():
    st.markdown('<style>[data-testid="collapsedControl"]{display:none}</style>',
                unsafe_allow_html=True)

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.markdown("""
        <div style="text-align:center; margin-top:4rem; margin-bottom:2rem;">
            <div style="font-family:'Bebas Neue',sans-serif; font-size:3rem;
                        letter-spacing:4px; color:#fff;">⚾ Fantasy Baseball</div>
            <div style="color:#4a7fa5; font-size:0.95rem; margin-top:0.3rem;">
                AI-powered ESPN league advisor
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_reg = st.tabs(["Log In", "Create Account"])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            lu = st.text_input("Username", key="li_user", placeholder="your username")
            lp = st.text_input("Password", key="li_pass", type="password",
                               placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Log In", use_container_width=True, key="btn_login"):
                if lu and lp:
                    ok, uid, msg = auth.login_user(lu, lp)
                    if ok:
                        st.session_state.user_id  = uid
                        st.session_state.username = lu.strip()
                        go_to("profiles")
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill in both fields.")

        with tab_reg:
            st.markdown("<br>", unsafe_allow_html=True)
            ru  = st.text_input("Username", key="reg_user",
                                placeholder="choose a username")
            rp  = st.text_input("Password", key="reg_pass", type="password",
                                placeholder="at least 6 characters")
            rp2 = st.text_input("Confirm password", key="reg_pass2", type="password",
                                placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Create Account", use_container_width=True, key="btn_reg"):
                if not (ru and rp and rp2):
                    st.warning("Please fill in all fields.")
                elif rp != rp2:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = auth.register_user(ru, rp)
                    if ok:
                        st.success(msg + " Switch to the Log In tab to continue.")
                    else:
                        st.error(msg)


# ═════════════════════════════════════════════
#  PAGE 2 — PROFILE SELECTION
# ═════════════════════════════════════════════
def render_profiles():
    st.markdown('<style>[data-testid="collapsedControl"]{display:none}</style>',
                unsafe_allow_html=True)

    hcol1, hcol2 = st.columns([5, 1])
    with hcol1:
        st.markdown(f"""
        <div style="margin-top:1rem; margin-bottom:2rem;">
            <div style="font-family:'Bebas Neue',sans-serif; font-size:2.2rem;
                        letter-spacing:3px; color:#fff;">⚾ My League Profiles</div>
            <div style="color:#4a7fa5; font-size:0.9rem;">
                Logged in as
                <strong style="color:#7ab8e8">{st.session_state.username}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with hcol2:
        st.markdown("<div style='margin-top:1.8rem'>", unsafe_allow_html=True)
        if st.button("Log Out", key="prof_logout"):
            logout()
        st.markdown("</div>", unsafe_allow_html=True)

    profiles = auth.list_profiles(st.session_state.user_id)

    if profiles:
        cols = st.columns(3)
        for i, prof in enumerate(profiles):
            with cols[i % 3]:
                private = "🔒 Private" if prof["espn_s2"] else "🔓 Public"
                st.markdown(f"""
                <div class="profile-card">
                    <div class="profile-title">{prof['name']}</div>
                    <div class="profile-meta">League ID: {prof['league_id'] or '—'}</div>
                    <div class="profile-meta">Season: {prof['season_year']}</div>
                    <div class="profile-meta" style="margin-top:0.3rem">{private}</div>
                </div>
                """, unsafe_allow_html=True)

                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("Select", key=f"sel_{prof['id']}",
                                 use_container_width=True):
                        st.session_state.active_profile  = prof
                        st.session_state.editing_profile = False
                        go_to("dashboard")
                with btn_col2:
                    if st.button("Delete", key=f"del_{prof['id']}",
                                 use_container_width=True):
                        auth.delete_profile(prof["id"], st.session_state.user_id)
                        st.rerun()
    else:
        st.info("You don't have any profiles yet. Create one below to get started.")

    st.markdown("---")

    # ── Create new profile ──
    st.markdown("### ➕ New Profile")
    with st.form("new_profile_form", clear_on_submit=True):
        p_name = st.text_input("Profile name",
                               placeholder='e.g. "Tanner 2026 Fantasy Baseball"')
        c1, c2 = st.columns(2)
        with c1:
            p_lid  = st.text_input("League ID", placeholder="ESPN League ID")
        with c2:
            p_year = st.number_input("Season Year", value=2025,
                                     min_value=2020, max_value=2030, step=1)
        p_s2     = st.text_input("espn_s2 cookie", type="password",
                                 help="Required for private leagues only")
        p_swid   = st.text_input("SWID cookie", type="password",
                                 help="Required for private leagues only")
        p_apikey = st.text_input("Anthropic API Key", type="password")
        p_team   = st.text_input("Team name (optional)",
                                 placeholder="Leave blank to choose after loading")
        submitted = st.form_submit_button("Save Profile", use_container_width=True)

    if submitted:
        if not p_name.strip():
            st.error("Please give the profile a name.")
        elif not p_lid.strip():
            st.error("League ID is required.")
        else:
            auth.create_profile(
                st.session_state.user_id,
                p_name.strip(), p_lid.strip(), int(p_year),
                p_s2, p_swid, p_apikey, p_team,
            )
            st.success(f'Profile "{p_name}" saved!')
            st.rerun()

    st.caption("ESPN cookies are only needed for private leagues. "
               "Find them in browser DevTools → Application → Cookies → espn.com")


# ═════════════════════════════════════════════
#  LEAGUE HELPERS
# ═════════════════════════════════════════════
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
    matches = [t for t in league.teams
               if name_filter.lower() in t.team_name.lower()]
    return matches[0] if matches else None


def get_roster_data(team):
    rows = []
    for p in team.roster:
        injury = getattr(p, "injuryStatus", "ACTIVE")
        rows.append({
            "name":   p.name,
            "pos":    p.position,
            "proj":   round(p.projected_total_points, 1),
            "injury": injury if injury not in ("ACTIVE", "NORMAL", None) else "",
        })
    return rows


def get_free_agents(league, size=25):
    try:
        fas = league.free_agents(size=size)
        return [{"name": fa.name, "pos": fa.position,
                 "proj": round(fa.projected_total_points, 1)} for fa in fas[:15]]
    except Exception:
        return []


def get_matchup(league, team):
    try:
        for box in league.box_scores():
            if box.home_team == team or box.away_team == team:
                opp       = box.away_team  if box.home_team == team else box.home_team
                my_score  = box.home_score if box.home_team == team else box.away_score
                opp_score = box.away_score if box.home_team == team else box.home_score
                return {"opponent":  opp.team_name,
                        "my_score":  round(my_score, 1),
                        "opp_score": round(opp_score, 1)}
    except Exception:
        pass
    return None


def build_context(league, my_team):
    roster_lines = "\n".join(
        f"  {p['name']:<25} | {p['pos']:<5} | Proj: {p['proj']} pts"
        + (f" [{p['injury']}]" if p["injury"] else "")
        for p in get_roster_data(my_team)
    )
    standings_lines = "\n".join(
        f"  {i}. {t.team_name:<25} | W:{t.wins} L:{t.losses}"
        for i, t in enumerate(
            sorted(league.teams, key=lambda t: t.wins, reverse=True), 1
        )
    )
    fa_lines = "\n".join(
        f"  {fa['name']:<25} | {fa['pos']:<5} | Proj: {fa['proj']} pts"
        for fa in get_free_agents(league)
    )
    matchup = get_matchup(league, my_team)
    matchup_str = (
        f"  {my_team.team_name} ({matchup['my_score']}) vs "
        f"{matchup['opponent']} ({matchup['opp_score']})"
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


# ═════════════════════════════════════════════
#  PAGE 3 — DASHBOARD
# ═════════════════════════════════════════════
def render_dashboard():
    prof = st.session_state.active_profile

    # ── Sidebar: nav controls ──
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        st.markdown(f"**{prof['name']}**")
        st.markdown(
            f"<span style='color:#4a7fa5;font-size:0.82rem'>"
            f"League {prof['league_id']} · {prof['season_year']}</span>",
            unsafe_allow_html=True,
        )
        st.markdown("---")
        if st.button("⬅ Switch Profile", use_container_width=True):
            st.session_state.active_profile = None
            go_to("profiles")
        if st.button("✏️ Edit This Profile", use_container_width=True):
            st.session_state.editing_profile = True
            st.rerun()
        if st.button("🚪 Log Out", use_container_width=True):
            logout()

    # ── Profile editor (full-page overlay) ──
    if st.session_state.get("editing_profile"):
        _render_profile_editor(prof)
        return

    # ── Hero ──
    st.markdown(f"""
    <div class="hero">
        <h1>Fantasy Baseball Advisor</h1>
        <p>{prof['name']} · League {prof['league_id']} · {prof['season_year']}</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Connect to ESPN ──
    try:
        with st.spinner("Connecting to ESPN..."):
            league = load_league(
                prof["league_id"], prof["season_year"],
                prof["espn_s2"], prof["swid"],
            )
    except Exception as e:
        st.error(f"❌ Could not connect to ESPN: {e}")
        return

    # ── Team selection ──
    my_team = find_team(league, prof["team_name_filter"])
    if not my_team:
        team_options = {t.team_name: t for t in league.teams}
        selected = st.selectbox("Select your team", list(team_options.keys()))
        my_team  = team_options[selected]

    # ── Stats bar ──
    matchup = get_matchup(league, my_team)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="stat-card"><div class="stat-label">League</div>
        <div class="stat-value" style="font-size:1.1rem;margin-top:4px">
        {league.settings.name}</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="stat-card"><div class="stat-label">Your Team</div>
        <div class="stat-value" style="font-size:1.1rem;margin-top:4px">
        {my_team.team_name}</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="stat-card"><div class="stat-label">Record</div>
        <div class="stat-value">{my_team.wins}–{my_team.losses}</div></div>""",
                    unsafe_allow_html=True)
    with col4:
        opp_str = matchup["opponent"] if matchup else "N/A"
        st.markdown(f"""<div class="stat-card"><div class="stat-label">This Week vs</div>
        <div class="stat-value" style="font-size:1.1rem;margin-top:4px">
        {opp_str}</div></div>""", unsafe_allow_html=True)

    # ── Two-column layout ──
    left, right = st.columns([3, 2])

    with left:
        st.markdown('<div class="section-header">📋 Current Roster</div>',
                    unsafe_allow_html=True)
        roster_data = get_roster_data(my_team)
        rows_html = ""
        for p in roster_data:
            inj = (f'<span class="injury-tag">{p["injury"]}</span>'
                   if p["injury"] else "")
            rows_html += f"""<tr>
                <td>{p['name']} {inj}</td>
                <td>{p['pos']}</td>
                <td>{p['proj']}</td>
            </tr>"""
        st.markdown(f"""
        <table class="roster-table">
            <thead><tr><th>Player</th><th>Position</th><th>Proj Pts</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-header">🏆 Standings</div>',
                    unsafe_allow_html=True)
        for i, team in enumerate(
            sorted(league.teams, key=lambda t: t.wins, reverse=True), 1
        ):
            hl = ("border-left:3px solid #3b82f6;padding-left:0.5rem;"
                  if team == my_team else "")
            st.markdown(f"""
            <div class="standing-row" style="{hl}">
                <span class="standing-rank">{i}</span>
                <span class="standing-name">{team.team_name}</span>
                <span class="standing-record">{team.wins}–{team.losses}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-header">🔄 Top Free Agents</div>',
                    unsafe_allow_html=True)
        for fa in get_free_agents(league):
            st.markdown(f"""
            <div class="fa-card">
                <span class="fa-name">{fa['name']}</span>
                <span class="fa-pos">{fa['pos']}</span>
                <span class="fa-proj">{fa['proj']} pts</span>
            </div>""", unsafe_allow_html=True)

    # ── AI Recommendations ──
    st.markdown("---")
    if not prof["api_key"]:
        st.warning("Add an Anthropic API key to this profile to get AI recommendations.")
    else:
        if st.button("⚾  GET AI RECOMMENDATIONS"):
            roster_ctx, standings_ctx, fa_ctx, matchup_ctx = build_context(
                league, my_team
            )
            advice = get_ai_advice(
                roster_ctx, standings_ctx, fa_ctx, matchup_ctx, prof["api_key"]
            )
            for section in advice.split("##"):
                section = section.strip()
                if not section:
                    continue
                lines   = section.split("\n", 1)
                title   = lines[0].strip()
                content = lines[1].strip() if len(lines) > 1 else ""
                st.markdown(f"### {title}")
                st.markdown(f'<div class="rec-card">{content}</div>',
                            unsafe_allow_html=True)


def _render_profile_editor(prof: dict):
    st.markdown("### ✏️ Edit Profile")
    with st.form("edit_profile_form"):
        e_name   = st.text_input("Profile name", value=prof["name"])
        c1, c2   = st.columns(2)
        with c1:
            e_lid  = st.text_input("League ID", value=prof["league_id"])
        with c2:
            e_year = st.number_input("Season Year", value=int(prof["season_year"]),
                                     min_value=2020, max_value=2030, step=1)
        e_s2     = st.text_input("espn_s2 cookie", type="password",
                                 value=prof["espn_s2"])
        e_swid   = st.text_input("SWID cookie", type="password",
                                 value=prof["swid"])
        e_apikey = st.text_input("Anthropic API Key", type="password",
                                 value=prof["api_key"])
        e_team   = st.text_input("Team name filter", value=prof["team_name_filter"])
        save_col, cancel_col = st.columns(2)
        with save_col:
            saved = st.form_submit_button("Save Changes", use_container_width=True)
        with cancel_col:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

    if saved:
        auth.update_profile(
            prof["id"], st.session_state.user_id,
            e_name.strip(), e_lid.strip(), int(e_year),
            e_s2, e_swid, e_apikey, e_team,
        )
        updated_row = database.get_profile(prof["id"], st.session_state.user_id)
        if updated_row:
            st.session_state.active_profile = auth._decrypt_profile(updated_row)
        st.session_state.editing_profile = False
        st.success("Profile updated!")
        st.rerun()

    if cancelled:
        st.session_state.editing_profile = False
        st.rerun()


# ═════════════════════════════════════════════
#  ROUTER
# ═════════════════════════════════════════════
_page = st.session_state.page

if _page == "login":
    render_login()
elif _page == "profiles":
    if not st.session_state.user_id:
        go_to("login")
    else:
        render_profiles()
elif _page == "dashboard":
    if not st.session_state.user_id or not st.session_state.active_profile:
        go_to("profiles")
    else:
        render_dashboard()
