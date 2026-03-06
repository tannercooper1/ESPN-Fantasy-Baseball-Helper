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

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    padding: 0.3rem 0 !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
    color: #c8d8e8;
    font-size: 0.92rem;
    line-height: 1.7;
}
/* User bubble */
[data-testid="stChatMessage"][data-role="user"] {
    flex-direction: row-reverse;
}
[data-testid="stChatMessage"][data-role="user"] .stChatMessageContent {
    background: #1e3a5f !important;
    border-radius: 16px 4px 16px 16px !important;
    padding: 0.6rem 1rem !important;
}
/* Assistant bubble */
[data-testid="stChatMessage"][data-role="assistant"] .stChatMessageContent {
    background: #111827 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 4px 16px 16px 16px !important;
    padding: 0.6rem 1rem !important;
}
/* Chat input bar */
[data-testid="stChatInput"] {
    background: #111827 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 12px !important;
}
[data-testid="stChatInput"] textarea {
    color: #e8e8e8 !important;
    font-size: 0.92rem !important;
}
/* Scrollable message container — remove default border/bg */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: none !important;
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SESSION STATE DEFAULTS
# ─────────────────────────────────────────────
_SS_DEFAULTS = {
    "page":               "login",   # login | profiles | dashboard
    "user_id":            None,
    "username":           None,
    "active_profile":     None,      # decrypted profile dict
    "editing_profile":    False,
    "chat_messages":      [],        # AI chat history for active session
    "league_refresh_key": 0,         # increment to bust load_league cache
    "ai_advice":          None,      # cached AI recommendation text
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
def load_league(league_id, year, espn_s2, swid, refresh_key=0):
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


def build_system_prompt(prof: dict, league, my_team) -> str:
    """
    Build a rich system prompt that encodes everything the AI needs to know
    about this specific league and team — live data + user's saved context notes.
    This is the 'league-specific AI skill' that persists across interactions.
    """
    roster_lines, standings_lines, fa_lines, matchup_str = build_context(league, my_team)

    league_context_section = ""
    if prof.get("league_context", "").strip():
        league_context_section = f"""
=== LEAGUE NOTES (provided by the user — treat as authoritative) ===
{prof['league_context'].strip()}
"""

    return f"""You are a dedicated fantasy baseball AI advisor for the team "{my_team.team_name}" \
in the "{league.settings.name}" ESPN league (season {prof['season_year']}).

Your job is to give specific, actionable advice grounded in the live data and the \
user's league notes below. Always reference real player names. Factor in keeper \
considerations, trade restrictions, league quirks, and strategic context from the \
notes when they are relevant.
{league_context_section}
=== LIVE LEAGUE DATA ===

MY ROSTER:
{roster_lines}

STANDINGS:
{standings_lines}

FREE AGENTS:
{fa_lines}

CURRENT MATCHUP:
{matchup_str}
"""


def get_ai_advice(roster, standings, fa, matchup, api_key, league_context: str = ""):
    client = anthropic.Anthropic(api_key=api_key)

    context_section = ""
    if league_context.strip():
        context_section = f"""
=== LEAGUE NOTES (treat as authoritative) ===
{league_context.strip()}

"""

    prompt = f"""You are an expert fantasy baseball analyst. Based on the league data below,
provide specific actionable recommendations. Name actual players and be direct.
{context_section}
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

    # ── Sidebar ──
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
            st.session_state.active_profile   = None
            st.session_state.chat_messages    = []
            st.session_state.ai_advice        = None
            go_to("profiles")
        if st.button("✏️ Edit Settings", use_container_width=True):
            st.session_state.editing_profile = True
            st.rerun()
        if st.button("🚪 Log Out", use_container_width=True):
            logout()

        # ── League Notes (inline, always visible) ──
        st.markdown("---")
        st.markdown(
            "<div style='font-size:0.75rem;text-transform:uppercase;"
            "letter-spacing:1.5px;color:#4a7fa5;margin-bottom:0.4rem'>"
            "📝 League Notes</div>",
            unsafe_allow_html=True,
        )
        st.caption("Keepers, trade rules, strategy — the AI reads this every time.")
        new_ctx = st.text_area(
            "league_notes_area",
            value=prof.get("league_context", ""),
            height=220,
            label_visibility="collapsed",
            placeholder=(
                "Examples:\n"
                "• 3 keepers allowed, cost = last round drafted − 1\n"
                "• I'm keeping Acuña (rd 1), Betts (rd 2), Witt (rd 3)\n"
                "• We're in win-now mode — don't suggest selling stars\n"
                "• Avoid trading with Team X, they lowball\n"
                "• Our league uses 6x6 with OPS instead of AVG"
            ),
        )
        if st.button("💾 Save Notes", use_container_width=True, key="save_notes"):
            auth.save_league_context(
                prof["id"], st.session_state.user_id, new_ctx
            )
            st.session_state.active_profile["league_context"] = new_ctx
            prof = st.session_state.active_profile
            st.success("Saved!")

    # ── Profile editor (full-page overlay) ──
    if st.session_state.get("editing_profile"):
        _render_profile_editor(prof)
        return

    # ── Hero + refresh button ──
    hero_col, refresh_col = st.columns([5, 1])
    with hero_col:
        st.markdown(f"""
        <div class="hero">
            <h1>Fantasy Baseball Advisor</h1>
            <p>{prof['name']} · League {prof['league_id']} · {prof['season_year']}</p>
        </div>
        """, unsafe_allow_html=True)
    with refresh_col:
        st.markdown("<div style='padding-top:1.6rem'>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", use_container_width=True, key="refresh_league",
                     help="Fetch latest roster/standings from ESPN"):
            st.session_state.league_refresh_key += 1
            st.session_state.ai_advice = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Connect to ESPN ──
    try:
        with st.spinner("Connecting to ESPN..."):
            league = load_league(
                prof["league_id"], prof["season_year"],
                prof["espn_s2"], prof["swid"],
                st.session_state.league_refresh_key,
            )
    except Exception as e:
        st.error(f"❌ Could not connect to ESPN: {e}")
        return

    # ── Team selection ──
    my_team = find_team(league, prof["team_name_filter"])
    if not my_team:
        team_options = {t.team_name: t for t in league.teams}
        sel_col, save_col = st.columns([4, 1])
        with sel_col:
            selected = st.selectbox("Select your team", list(team_options.keys()))
        with save_col:
            st.markdown("<div style='padding-top:1.75rem'>", unsafe_allow_html=True)
            if st.button("💾 Save", use_container_width=True, key="save_team",
                         help="Save this as your default team for this profile"):
                auth.update_profile(
                    prof["id"], st.session_state.user_id,
                    prof["name"], prof["league_id"], int(prof["season_year"]),
                    prof["espn_s2"], prof["swid"], prof["api_key"],
                    selected, prof.get("league_context", ""),
                )
                st.session_state.active_profile["team_name_filter"] = selected
                st.success(f'"{selected}" saved as your team.')
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        my_team = team_options[selected]

    # ── Stats bar ──
    roster_data = get_roster_data(my_team)
    matchup     = get_matchup(league, my_team)
    sorted_teams = sorted(league.teams, key=lambda t: t.wins, reverse=True)
    my_standing  = next((i + 1 for i, t in enumerate(sorted_teams) if t == my_team), "?")
    injured      = [p for p in roster_data if p["injury"]]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="stat-card"><div class="stat-label">Record</div>
        <div class="stat-value">{my_team.wins}–{my_team.losses}</div></div>""",
                    unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="stat-card"><div class="stat-label">Standing</div>
        <div class="stat-value">{my_standing}
        <span style="font-size:0.9rem;color:#4a7fa5"> of {len(league.teams)}</span>
        </div></div>""", unsafe_allow_html=True)
    with col3:
        if matchup:
            score_color = "#34d399" if matchup["my_score"] > matchup["opp_score"] else "#f87171"
            score_str   = (f'<span style="color:{score_color}">{matchup["my_score"]}</span>'
                           f' – {matchup["opp_score"]}')
            opp_label   = matchup["opponent"]
        else:
            score_str, opp_label = "N/A", "—"
        st.markdown(f"""<div class="stat-card">
        <div class="stat-label">vs {opp_label}</div>
        <div class="stat-value" style="font-size:1.4rem;margin-top:4px">{score_str}</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        inj_color = "#f87171" if injured else "#34d399"
        inj_label = f"{len(injured)} injured" if injured else "All healthy"
        inj_list  = ", ".join(p["name"].split()[-1] for p in injured[:3])
        if len(injured) > 3:
            inj_list += f" +{len(injured)-3}"
        st.markdown(f"""<div class="stat-card"><div class="stat-label">Roster Health</div>
        <div class="stat-value" style="font-size:1.1rem;margin-top:4px;color:{inj_color}">
        {inj_label}</div>
        {"<div style='color:#4a7fa5;font-size:0.75rem;margin-top:2px'>" + inj_list + "</div>"
         if inj_list else ""}
        </div>""", unsafe_allow_html=True)

    # ── Tabs ──
    tab_overview, tab_chat = st.tabs(["📊 Overview", "🤖 AI Chat"])

    # ════════════════
    #  OVERVIEW TAB
    # ════════════════
    with tab_overview:
        team_col, ai_col = st.columns([5, 4])

        # ── LEFT: Team Summary ──
        with team_col:
            # Injury callout banner
            if injured:
                alerts = " &nbsp;·&nbsp; ".join(
                    f'<b>{p["name"]}</b> <span class="injury-tag">{p["injury"]}</span>'
                    for p in injured
                )
                st.markdown(
                    f'<div style="background:#3d1a1a;border:1px solid #7f1d1d;'
                    f'border-radius:8px;padding:0.6rem 1rem;margin-bottom:0.8rem;'
                    f'font-size:0.85rem">⚠️ &nbsp;{alerts}</div>',
                    unsafe_allow_html=True,
                )

            # Roster split into batters / pitchers
            batters  = [p for p in roster_data if p["pos"] not in ("SP", "RP", "P")]
            pitchers = [p for p in roster_data if p["pos"] in ("SP", "RP", "P")]

            def roster_table(players):
                rows = ""
                for p in players:
                    inj = (f'<span class="injury-tag">{p["injury"]}</span>'
                           if p["injury"] else "")
                    rows += (f"<tr><td>{p['name']} {inj}</td>"
                             f"<td>{p['pos']}</td><td>{p['proj']}</td></tr>")
                return (f'<table class="roster-table"><thead><tr>'
                        f'<th>Player</th><th>Pos</th><th>Proj</th>'
                        f'</tr></thead><tbody>{rows}</tbody></table>')

            st.markdown('<div class="section-header">🏏 Batters</div>',
                        unsafe_allow_html=True)
            st.markdown(roster_table(batters), unsafe_allow_html=True)
            st.markdown('<div class="section-header">⚾ Pitchers</div>',
                        unsafe_allow_html=True)
            st.markdown(roster_table(pitchers), unsafe_allow_html=True)

        # ── RIGHT: AI Recommendations ──
        with ai_col:
            st.markdown('<div class="section-header">🤖 AI Recommendations</div>',
                        unsafe_allow_html=True)
            if not prof["api_key"]:
                st.warning("Add an Anthropic API key to this profile.")
            else:
                btn_label = ("🔄 Regenerate" if st.session_state.ai_advice
                             else "⚾ Get Recommendations")
                if st.button(btn_label, use_container_width=True, key="get_advice"):
                    roster_ctx, standings_ctx, fa_ctx, matchup_ctx = build_context(
                        league, my_team
                    )
                    st.session_state.ai_advice = get_ai_advice(
                        roster_ctx, standings_ctx, fa_ctx, matchup_ctx,
                        prof["api_key"], prof.get("league_context", ""),
                    )
                    st.rerun()

                if st.session_state.ai_advice:
                    for section in st.session_state.ai_advice.split("##"):
                        section = section.strip()
                        if not section:
                            continue
                        lines   = section.split("\n", 1)
                        title   = lines[0].strip()
                        content = lines[1].strip() if len(lines) > 1 else ""
                        st.markdown(f"**{title}**")
                        st.markdown(f'<div class="rec-card">{content}</div>',
                                    unsafe_allow_html=True)
                else:
                    st.markdown(
                        "<div style='color:#4a7fa5;font-size:0.88rem;padding:1rem 0'>"
                        "Click the button above to get AI-powered recommendations "
                        "for your roster, lineup, waiver wire, and trades."
                        "</div>",
                        unsafe_allow_html=True,
                    )

        # ── Secondary: Standings + Free Agents in expanders ──
        st.markdown("<br>", unsafe_allow_html=True)
        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            with st.expander("🏆 League Standings"):
                for i, team in enumerate(sorted_teams, 1):
                    hl = ("border-left:3px solid #3b82f6;padding-left:0.5rem;"
                          if team == my_team else "")
                    st.markdown(f"""
                    <div class="standing-row" style="{hl}">
                        <span class="standing-rank">{i}</span>
                        <span class="standing-name">{team.team_name}</span>
                        <span class="standing-record">{team.wins}–{team.losses}</span>
                    </div>""", unsafe_allow_html=True)
        with exp_col2:
            with st.expander("🔄 Top Free Agents"):
                for fa in get_free_agents(league):
                    st.markdown(f"""
                    <div class="fa-card">
                        <span class="fa-name">{fa['name']}</span>
                        <span class="fa-pos">{fa['pos']}</span>
                        <span class="fa-proj">{fa['proj']} pts</span>
                    </div>""", unsafe_allow_html=True)

    # ════════════════
    #  AI CHAT TAB
    # ════════════════
    with tab_chat:
        if not prof["api_key"]:
            st.warning("Add an Anthropic API key to this profile to use AI Chat.")
        else:
            _render_ai_chat(prof, league, my_team)


def _render_ai_chat(prof: dict, league, my_team):
    """Conversational AI chat grounded in live league data + league notes."""
    system_prompt = build_system_prompt(prof, league, my_team)
    client        = anthropic.Anthropic(api_key=prof["api_key"])
    messages      = st.session_state.chat_messages

    # ── Thin header: context badge + clear button ──
    hdr_left, hdr_right = st.columns([5, 1])
    with hdr_left:
        has_notes = bool(prof.get("league_context", "").strip())
        badge = ("🟢 League notes loaded" if has_notes
                 else "⚪ No league notes — add them in the sidebar")
        st.markdown(
            f"<div style='color:#4a7fa5;font-size:0.8rem;padding:0.3rem 0'>{badge}</div>",
            unsafe_allow_html=True,
        )
    with hdr_right:
        if messages and st.button("🗑 Clear", key="clear_chat"):
            st.session_state.chat_messages = []
            st.rerun()

    # ── Message area (fixed height, scrolls up as conversation grows) ──
    # Declared here so it sits above the input visually; filled below.
    msg_container = st.container(height=540, border=False)

    # ── Input — Streamlit pins this to the bottom of the tab ──
    user_input = st.chat_input("Ask about your team, trades, lineup, keepers…")

    # ── Fill the message container ──
    with msg_container:
        if not messages:
            st.markdown(
                "<div style='color:#4a7fa5;font-size:0.88rem;"
                "padding:1rem 0 0.5rem'>"
                "Ask me anything about your roster, matchup, free agents, or "
                "trade strategy. I already have your live league data loaded."
                "</div>",
                unsafe_allow_html=True,
            )

        # Render existing history
        for msg in messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Handle new message + stream response inside the container
        if user_input:
            messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                placeholder = st.empty()
                full_text   = ""
                with client.messages.stream(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1500,
                    system=system_prompt,
                    messages=messages,
                ) as stream:
                    for chunk in stream.text_stream:
                        full_text += chunk
                        placeholder.markdown(full_text + "▌")
                placeholder.markdown(full_text)

            messages.append({"role": "assistant", "content": full_text})
            st.session_state.chat_messages = messages


def _render_profile_editor(prof: dict):
    st.markdown("### ✏️ Edit Profile Settings")
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
            prof.get("league_context", ""),
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
