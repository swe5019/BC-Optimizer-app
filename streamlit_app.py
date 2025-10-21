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

# ---------- GENERAL HELPERS ----------
def avg_hcp(pair):
    return (pair[0][1] + pair[1][1]) / 2

def pairing_balance_score(pair):
    h1, h2 = pair[0][1], pair[1][1]
    return 1 - abs(h1 - h2) / 36

def matchup_evenness_score(pair_a, pair_b):
    return 1 - abs(avg_hcp(pair_a) - avg_hcp(pair_b)) / 36

def stroke_advantage_for_team(your_pair, opp_pair):
    """Positive means your_pair gets strokes (higher average handicap)."""
    return avg_hcp(your_pair) - avg_hcp(opp_pair)

def remove_players(remaining, pair):
    return [p for p in remaining if p not in pair]

def pair_to_names(pair):
    return f"{pair[0][0]} ({pair[0][1]})  +  {pair[1][0]} ({pair[1][1]})"

def stroke_summary_line(pair_a, pair_b, left_label="Atown", right_label="Pittsburgh"):
    a_gets = stroke_advantage_for_team(pair_a, pair_b)
    b_gets = stroke_advantage_for_team(pair_b, pair_a)
    a_color = ATOWN_COLOR if a_gets >= 0 else "#CC0000"
    b_color = PITT_COLOR  if b_gets >= 0 else "#CC0000"
    a_text = f"<span style='color:{a_color};font-weight:600'>{left_label} {'gets' if a_gets >= 0 else 'gives'} {abs(a_gets):.2f} strokes</span>"
    b_text = f"<span style='color:{b_color};font-weight:600'>{right_label} {'gets' if b_gets >= 0 else 'gives'} {abs(b_gets):.2f} strokes</span>"
    return a_text + " • " + b_text


# ---------- APP START ----------
st.title("🏌️ Golf Trip Match Optimizer")
tab1, tab2 = st.tabs(["🏌️ Best Ball Rounds", "🎯 Singles Round"])

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
            evenness = matchup_evenness_score(first_pair, counter)
            balance  = pairing_balance_score(counter)
            strokes  = max(0.0, stroke_advantage_for_team(counter, first_pair))
            score = (1 - balance_weight) * (evenness + (strokes / 36.0)) + balance_weight * balance
            if score > best_score:
                best_combo, best_score = counter, score
        return best_combo

    st.markdown("### 🏌️ Best Ball Pairings")
    balance_weight = st.sidebar.slider(
        "⚖️ Balance vs Matchup Weight",
        0.0, 1.0, 0.5, 0.1,
        help="0.0 = seek matchup/stroke advantage; 1.0 = prioritize balanced teammates"
    )

    if st.sidebar.button("🔁 Reset Best Ball"):
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
                st.markdown("### 🟢 Atown First Pick")
                suggested_first = best_pair(st.session_state.remaining_a, balance_weight)
                st.write(f"**Recommended Pair:** {pair_to_names(suggested_first)}")
                manual_first = st.multiselect("Manual Override (optional)",
                    [p[0] for p in st.session_state.remaining_a],
                    max_selections=2)
                first_pair = [p for p in st.session_state.remaining_a if p[0] in manual_first] if len(manual_first)==2 else list(suggested_first)
            else:
                st.markdown("### 🟠 Pittsburgh First Pick")
                suggested_first = best_pair(st.session_state.remaining_b, balance_weight)
                st.write(f"**Recommended Pair:** {pair_to_names(suggested_first)}")
                manual_first = st.multiselect("Manual Override (optional)",
                    [p[0] for p in st.session_state.remaining_b],
                    max_selections=2)
                first_pair = [p for p in st.session_state.remaining_b if p[0] in manual_first] if len(manual_first)==2 else list(suggested_first)

        with col2:
            if first_picker.startswith("Atown"):
                st.markdown("### 🟠 Pittsburgh Counter Pick")
                suggested_counter = best_counter_pair(first_pair, st.session_state.remaining_b, balance_weight)
                st.write(f"**Recommended Counter:** {pair_to_names(suggested_counter)}")
                manual_counter = st.multiselect("Manual Override (optional)",
                    [p[0] for p in st.session_state.remaining_b],
                    max_selections=2)
                counter_pair = [p for p in st.session_state.remaining_b if p[0] in manual_counter] if len(manual_counter)==2 else list(suggested_counter)
                st.write(f"**Atown Avg HCP:** {avg_hcp(first_pair):.2f} | **Pittsburgh Avg HCP:** {avg_hcp(counter_pair):.2f}")
                st.markdown(stroke_summary_line(first_pair, counter_pair, "Atown", "Pittsburgh"), unsafe_allow_html=True)
            else:
                st.markdown("### 🟢 Atown Counter Pick")
                suggested_counter = best_counter_pair(first_pair, st.session_state.remaining_a, balance_weight)
                st.write(f"**Recommended Counter:** {pair_to_names(suggested_counter)}")
                manual_counter = st.multiselect("Manual Override (optional)",
                    [p[0] for p in st.session_state.remaining_a],
                    max_selections=2)
                counter_pair = [p for p in st.session_state.remaining_a if p[0] in manual_counter] if len(manual_counter)==2 else list(suggested_counter)
                st.write(f"**Pittsburgh Avg HCP:** {avg_hcp(first_pair):.2f} | **Atown Avg HCP:** {avg_hcp(counter_pair):.2f}")
                st.markdown(stroke_summary_line(counter_pair, first_pair, "Atown", "Pittsburgh"), unsafe_allow_html=True)

        if st.button("✅ Lock in Match"):
            if first_picker.startswith("Atown"):
                st.session_state.matches.append(("Atown first", first_pair, counter_pair))
                st.session_state.remaining_a = remove_players(st.session_state.remaining_a, first_pair)
                st.session_state.remaining_b = remove_players(st.session_state.remaining_b, counter_pair)
            else:
                st.session_state.matches.append(("Pittsburgh first", first_pair, counter_pair))
                st.session_state.remaining_b = remove_players(st.session_state.remaining_b, first_pair)
                st.session_state.remaining_a = remove_players(st.session_state.remaining_a, counter_pair)
            st.rerun()
    else:
        st.success("✅ All 4 matches locked in!")

    st.markdown("---")
    st.markdown("## 📋 Match Summary")
    for i, (who_first, first_pair, counter_pair) in enumerate(st.session_state.matches, 1):
        st.markdown(f"**Match {i}:** {who_first}")
        if who_first.startswith("Atown"):
            st.markdown(f"<span style='color:{ATOWN_COLOR};font-weight:700'>Atown:</span> {pair_to_names(first_pair)}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:{PITT_COLOR};font-weight:700'>Pittsburgh:</span> {pair_to_names(counter_pair)}", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:{PITT_COLOR};font-weight:700'>Pittsburgh:</span> {pair_to_names(first_pair)}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:{ATOWN_COLOR};font-weight:700'>Atown:</span> {pair_to_names(counter_pair)}", unsafe_allow_html=True)
        st.write(f"**Avg HCP Diff:** {abs(avg_hcp(first_pair)-avg_hcp(counter_pair)):.2f}")
        st.markdown(stroke_summary_line(first_pair, counter_pair, "Atown", "Pittsburgh"), unsafe_allow_html=True)

# ===============================================================
# TAB 2 — SINGLES OPTIMIZER
# ===============================================================
with tab2:
    st.markdown("### 🎯 Singles Matchups")

    if "singles_matches" not in st.session_state:
        st.session_state.singles_matches = []
        st.session_state.remaining_a_singles = team_a.copy()
        st.session_state.remaining_b_singles = team_b.copy()

    def best_single(remaining, balance_weight):
        avg_pool = sum(p[1] for p in remaining) / len(remaining)
        best_player, best_score = None, -1e9
        for p in remaining:
            stroke_factor = p[1] / 36
            deviation = abs(p[1] - avg_pool)
            score = (1 - balance_weight) * (stroke_factor - deviation / 36)
            if score > best_score:
                best_player, best_score = p, score
        return best_player

    def best_counter_single(first, remaining, balance_weight):
        best_player, best_score = None, -1e9
        for p in remaining:
            diff = abs(p[1] - first[1])
            strokes = max(0.0, p[1] - first[1])
            evenness = 1 - diff / 36
            score = (1 - balance_weight) * (evenness + (strokes / 36))
            if score > best_score:
                best_player, best_score = p, score
        return best_player

    def remove_player(rem, player):
        return [p for p in rem if p != player]

    balance_weight = st.sidebar.slider(
        "⚖️ Singles Balance vs Matchup Weight",
        0.0, 1.0, 0.5, 0.1,
        help="0.0 = maximize stroke advantage; 1.0 = balance evenly"
    )

    round_num = len(st.session_state.singles_matches) + 1
    if round_num <= 8:
        first_picker = st.radio(
            "Who picks first?",
            ["Atown (Kelly Green)", "Pittsburgh (Orange)"],
            horizontal=True, key=f"singles_first_{round_num}"
        )

        if first_picker.startswith("Atown"):
            suggested_first = best_single(st.session_state.remaining_a_singles, balance_weight)
            st.write(f"🟢 **Atown Recommended:** {suggested_first[0]} ({suggested_first[1]})")
            first_override = st.selectbox("Manual Override (optional)",
                [p[0] for p in st.session_state.remaining_a_singles],
                index=0)
            first_player = next(p for p in st.session_state.remaining_a_singles if p[0] == first_override)
            suggested_counter = best_counter_single(first_player, st.session_state.remaining_b_singles, balance_weight)
            st.write(f"🟠 **Pittsburgh Counter:** {suggested_counter[0]} ({suggested_counter[1]})")
        else:
            suggested_first = best_single(st.session_state.remaining_b_singles, balance_weight)
            st.write(f"🟠 **Pittsburgh Recommended:** {suggested_first[0]} ({suggested_first[1]})")
            first_override = st.selectbox("Manual Override (optional)",
                [p[0] for p in st.session_state.remaining_b_singles],
                index=0)
            first_player = next(p for p in st.session_state.remaining_b_singles if p[0] == first_override)
            suggested_counter = best_counter_single(first_player, st.session_state.remaining_a_singles, balance_weight)
            st.write(f"🟢 **Atown Counter:** {suggested_counter[0]} ({suggested_counter[1]})")

        diff = abs(first_player[1] - suggested_counter[1])
        higher_gets = "Atown" if first_player[1] > suggested_counter[1] else "Pittsburgh"
        st.write(f"**Stroke Differential:** {diff:.2f} ({higher_gets} gets strokes)")

        if st.button("✅ Lock in Singles Match", key=f"singles_lock_{round_num}"):
            st.session_state.singles_matches.append((first_picker, first_player, suggested_counter))
            if first_picker.startswith("Atown"):
                st.session_state.remaining_a_singles = remove_player(st.session_state.remaining_a_singles, first_player)
                st.session_state.remaining_b_singles = remove_player(st.session_state.remaining_b_singles, suggested_counter)
            else:
                st.session_state.remaining_b_singles = remove_player(st.session_state.remaining_b_singles, first_player)
                st.session_state.remaining_a_singles = remove_player(st.session_state.remaining_a_singles, suggested_counter)
            st.rerun()
    else:
        st.success("✅ All 8 singles matches locked in!")

    st.markdown("---")
    st.markdown("### Singles Match Summary")
    for i, (who_first, p1, p2) in enumerate(st.session_state.singles_matches, 1):
        st.write(f"**Match {i}:** {who_first}")
        st.write(f"{p1[0]} ({p1[1]}) vs {p2[0]} ({p2[1]})")
        diff = abs(p1[1] - p2[1])
        higher_gets = "Atown" if p1[1] > p2[1] else "Pittsburgh"
        st.write(f"**Stroke Differential:** {diff:.2f} ({higher_gets} gets strokes)")





