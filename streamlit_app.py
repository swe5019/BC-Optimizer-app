import streamlit as st
import itertools
import pandas as pd

st.set_page_config(page_title="Golf Trip Match Optimizer", layout="wide")

# ---------- COLORS ----------
ATOWN_COLOR = "#00A86B"   # Kelly Green
PITT_COLOR  = "#FF6600"   # Orange

# ---------- PLAYER DATA ----------
team_a = [
    ('Farley', 19.3), ('Fil', 28.4), ('Sean', -0.5), ('Tom', 13.9),
    ('Smith', 9.2), ('Paul', 19.2), ('Greg', 12.4), ('Zimmel', 20.6)
]
team_b = [
    ('Maize', 13.4), ('Kuj', 16.0), ('Jerry', 13.3),
    ('Pat', 15.6), ('Dave', 6.1), ('Oobs', 11.5),
    ('Ben', 19.0), ('Boardman', 4.3)
]

# ---------- HELPERS ----------
def avg_hcp(pair):
    return (pair[0][1] + pair[1][1]) / 2

def pairing_balance_score(pair):
    h1, h2 = pair[0][1], pair[1][1]
    return 1 - abs(h1 - h2) / 36

def stroke_advantage_for_team(your_pair, opp_pair):
    """Positive means your_pair gets strokes (higher avg handicap)."""
    return avg_hcp(your_pair) - avg_hcp(opp_pair)

def remove_players(remaining, pair):
    return [p for p in remaining if p not in pair]

def pair_to_names(pair):
    return f"{pair[0][0]} ({pair[0][1]}) + {pair[1][0]} ({pair[1][1]})"

# ---------- APP START ----------
st.title("🏌️ Golf Trip Match Optimizer")

tab1, tab2, tab3 = st.tabs([
    "🏌️ Best Ball Rounds",
    "🎯 Singles Round",
    "📈 Pairing Rankings"
])

# ===============================================================
# TAB 1 — BEST BALL OPTIMIZER
# ===============================================================
with tab1:
    if "matches" not in st.session_state:
        st.session_state.matches = []
    if "remaining_a" not in st.session_state:
        st.session_state.remaining_a = team_a.copy()
    if "remaining_b" not in st.session_state:
        st.session_state.remaining_b = team_b.copy()

    def best_pair(remaining, balance_weight):
        avg_pool = sum(p[1] for p in remaining) / len(remaining)
        best_combo, best_score = None, -1e9
        for pair in itertools.combinations(remaining, 2):
            avg = avg_hcp(pair)
            balance = pairing_balance_score(pair)
            deviation = abs(pair[0][1] - avg_pool) + abs(pair[1][1] - avg_pool)
            stroke_factor = avg / 36
            score = (1 - balance_weight) * (stroke_factor - deviation / 72) + balance_weight * balance
            if score > best_score:
                best_combo, best_score = pair, score
        return best_combo

    def best_counter_pair(first_pair, remaining, balance_weight):
        best_combo, best_score = None, -1e9
        for counter in itertools.combinations(remaining, 2):
            diff = abs(avg_hcp(first_pair) - avg_hcp(counter))
            strokes = max(0.0, avg_hcp(counter) - avg_hcp(first_pair))
            balance  = pairing_balance_score(counter)
            score = (1 - balance_weight) * (1 - diff / 36 + (strokes / 36)) + balance_weight * balance
            if score > best_score:
                best_combo, best_score = counter, score
        return best_combo

    st.markdown("### 🏌️ Best Ball Pairings")
    balance_weight = st.sidebar.slider(
        "⚖️ Balance vs Matchup Weight (Best Ball)",
        0.0, 1.0, 0.5, 0.1,
        help="0.0 = seek matchup/stroke advantage; 1.0 = prioritize balanced teammates"
    )

    if st.sidebar.button("🔁 Reset Best Ball Matches"):
        st.session_state.matches = []
        st.session_state.remaining_a = team_a.copy()
        st.session_state.remaining_b = team_b.copy()
        st.rerun()

    round_num = len(st.session_state.matches) + 1
    if round_num <= 4:
        st.markdown(f"### Round {round_num}")
        first_picker = st.radio("Who picks first this match?", ["Atown (Kelly Green)", "Pittsburgh (Orange)"], horizontal=True)
        col1, col2 = st.columns(2)

        with col1:
            if first_picker.startswith("Atown"):
                suggested_first = best_pair(st.session_state.remaining_a, balance_weight)
                st.markdown("### 🟢 Atown First Pick")
                st.write(f"**Recommended Pair:** {pair_to_names(suggested_first)}")
                manual_first = st.multiselect("Manual Override (optional)",
                    [p[0] for p in st.session_state.remaining_a],
                    max_selections=2)
                first_pair = [p for p in st.session_state.remaining_a if p[0] in manual_first] if len(manual_first)==2 else list(suggested_first)
            else:
                suggested_first = best_pair(st.session_state.remaining_b, balance_weight)
                st.markdown("### 🟠 Pittsburgh First Pick")
                st.write(f"**Recommended Pair:** {pair_to_names(suggested_first)}")
                manual_first = st.multiselect("Manual Override (optional)",
                    [p[0] for p in st.session_state.remaining_b],
                    max_selections=2)
                first_pair = [p for p in st.session_state.remaining_b if p[0] in manual_first] if len(manual_first)==2 else list(suggested_first)

        with col2:
            if first_picker.startswith("Atown"):
                suggested_counter = best_counter_pair(first_pair, st.session_state.remaining_b, balance_weight)
                st.markdown("### 🟠 Pittsburgh Counter Pick")
                st.write(f"**Recommended Counter:** {pair_to_names(suggested_counter)}")
            else:
                suggested_counter = best_counter_pair(first_pair, st.session_state.remaining_a, balance_weight)
                st.markdown("### 🟢 Atown Counter Pick")
                st.write(f"**Recommended Counter:** {pair_to_names(suggested_counter)}")

        if st.button("✅ Lock in Match"):
            if first_picker.startswith("Atown"):
                st.session_state.matches.append(("Atown first", first_pair, suggested_counter))
                st.session_state.remaining_a = remove_players(st.session_state.remaining_a, first_pair)
                st.session_state.remaining_b = remove_players(st.session_state.remaining_b, suggested_counter)
            else:
                st.session_state.matches.append(("Pittsburgh first", first_pair, suggested_counter))
                st.session_state.remaining_b = remove_players(st.session_state.remaining_b, first_pair)
                st.session_state.remaining_a = remove_players(st.session_state.remaining_a, suggested_counter)
            st.rerun()
    else:
        st.success("✅ All 4 matches locked in!")

    st.markdown("---")
    st.markdown("## 📋 Best Ball Match Summary")
    total_a, total_b = 0, 0
    for i, (who_first, first_pair, counter_pair) in enumerate(st.session_state.matches, 1):
        diff = stroke_advantage_for_team(first_pair, counter_pair)
        total_a += diff
        total_b -= diff
        st.markdown(f"**Match {i}:** {pair_to_names(first_pair)} vs {pair_to_names(counter_pair)}<br>"
                    f"<span style='color:{ATOWN_COLOR};font-weight:600'>Atown {'gets' if diff>=0 else 'gives'} {abs(diff):.2f}</span> • "
                    f"<span style='color:{PITT_COLOR};font-weight:600'>Pittsburgh {'gets' if diff<=0 else 'gives'} {abs(diff):.2f}</span>",
                    unsafe_allow_html=True)

    st.markdown(f"### 🧮 Total Stroke Advantage: 🟢 Atown = {total_a:.2f} | 🟠 Pittsburgh = {total_b:.2f}")

# ===============================================================
# TAB 3 — PAIRING RANKINGS
# ===============================================================
with tab3:
    st.markdown("### 📈 Ranking All Possible Pairings")

    def rank_pairings(team, team_name):
        avg_pool = sum(p[1] for p in team) / len(team)
        rows = []
        for pair in itertools.combinations(team, 2):
            balance = pairing_balance_score(pair)
            deviation = abs(pair[0][1] - avg_pool) + abs(pair[1][1] - avg_pool)
            avg_h = avg_hcp(pair)
            score = (1 - balance_weight) * (avg_h / 36 - deviation / 72) + balance_weight * balance
            rows.append({
                "Team": team_name,
                "Pair": pair_to_names(pair),
                "Avg Handicap": avg_h,
                "Balance Score": balance,
                "Overall Score": score
            })
        return pd.DataFrame(rows).sort_values("Overall Score", ascending=False)

    df_a = rank_pairings(team_a, "Atown")
    df_b = rank_pairings(team_b, "Pittsburgh")

    st.markdown("#### 🟢 Atown Pairing Rankings")
    st.dataframe(df_a.reset_index(drop=True), use_container_width=True)

    st.markdown("#### 🟠 Pittsburgh Pairing Rankings")
    st.dataframe(df_b.reset_index(drop=True), use_container_width=True)






