import streamlit as st
import itertools
import pandas as pd

st.set_page_config(page_title="Golf Trip Match Optimizer", layout="wide")

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

# ---------- STATE ----------
if "matches" not in st.session_state:
    st.session_state.matches = []
if "remaining_a" not in st.session_state:
    st.session_state.remaining_a = team_a.copy()
if "remaining_b" not in st.session_state:
    st.session_state.remaining_b = team_b.copy()

# ---------- FUNCTIONS ----------
def pairing_score(pair, balance_weight):
    h1, h2 = pair[0][1], pair[1][1]
    # Balance score: closer handicaps get higher score
    balance = 1 - abs(h1 - h2) / 36
    return balance_weight * balance

def matchup_score(pair_a, pair_b):
    avg_a = (pair_a[0][1] + pair_a[1][1]) / 2
    avg_b = (pair_b[0][1] + pair_b[1][1]) / 2
    # Matchup score: smaller difference between averages gets higher score
    return 1 - abs(avg_a - avg_b) / 36

def best_pair(team, remaining, balance_weight):
    best_combo = None
    best_score = -1
    for pair in itertools.combinations(remaining, 2):
        score = pairing_score(pair, balance_weight)
        if score > best_score:
            best_score = score
            best_combo = pair
    return best_combo

def best_counter_pair(first_pair, remaining, balance_weight):
    best_combo = None
    best_score = -1
    for pair in itertools.combinations(remaining, 2):
        score = matchup_score(first_pair, pair) + pairing_score(pair, balance_weight)
        if score > best_score:
            best_score = score
            best_combo = pair
    return best_combo

def remove_players(remaining, pair):
    return [p for p in remaining if p not in pair]

# ---------- SIDEBAR ----------
st.sidebar.header("⚙️ Settings")
balance_weight = st.sidebar.slider(
    "⚖️ Balance vs Matchup Weight",
    0.0, 1.0, 0.5, 0.1,
    help="0.0 = favor handicap advantage, 1.0 = favor balanced pairings"
)
if st.sidebar.button("🔁 Reset Draft"):
    st.session_state.matches = []
    st.session_state.remaining_a = team_a.copy()
    st.session_state.remaining_b = team_b.copy()
    st.rerun()

# ---------- MAIN TITLE ----------
st.title("🏌️ Golf Trip Match Optimizer")

round_num = len(st.session_state.matches) + 1
if round_num <= 4:
    st.markdown(f"### Round {round_num}")

    # Select who picks first
    first_picker = st.radio("Who picks first this match?", ["Atown (Kelly Green)", "Pittsburgh (Orange)"], horizontal=True)

    col1, col2 = st.columns(2)

    with col1:
        if first_picker.startswith("Atown"):
            st.markdown("### 🟢 Atown First Pick")
            suggested_first = best_pair("Atown", st.session_state.remaining_a, balance_weight)
            st.write(
                f"**Recommended Pair:** {suggested_first[0][0]} ({suggested_first[0][1]}), "
                f"{suggested_first[1][0]} ({suggested_first[1][1]})"
            )
            manual_first = st.text_input("Manual Override (comma-separated, e.g. Farley, Tom)", "")
        else:
            st.markdown("### 🟠 Pittsburgh First Pick")
            suggested_first = best_pair("Pittsburgh", st.session_state.remaining_b, balance_weight)
            st.write(
                f"**Recommended Pair:** {suggested_first[0][0]} ({suggested_first[0][1]}), "
                f"{suggested_first[1][0]} ({suggested_first[1][1]})"
            )
            manual_first = st.text_input("Manual Override (comma-separated, e.g. Bman, Dmac)", "")

    with col2:
        if first_picker.startswith("Atown"):
            suggested_counter = best_counter_pair(suggested_first, st.session_state.remaining_b, balance_weight)
            st.markdown("### 🟠 Pittsburgh Counter Pick")
            st.write(
                f"**Recommended Counter:** {suggested_counter[0][0]} ({suggested_counter[0][1]}), "
                f"{suggested_counter[1][0]} ({suggested_counter[1][1]})"
            )
            manual_counter = st.text_input("Manual Override (comma-separated, e.g. Oobs, Beans Kujava)", "")
        else:
            suggested_counter = best_counter_pair(suggested_first, st.session_state.remaining_a, balance_weight)
            st.markdown("### 🟢 Atown Counter Pick")
            st.write(
                f"**Recommended Counter:** {suggested_counter[0][0]} ({suggested_counter[0][1]}), "
                f"{suggested_counter[1][0]} ({suggested_counter[1][1]})"
            )
            manual_counter = st.text_input("Manual Override (comma-separated, e.g. Greg, Farley)", "")

    if st.button("✅ Lock in Match"):
        if manual_first:
            first_names = [x.strip() for x in manual_first.split(",")]
            if first_picker.startswith("Atown"):
                suggested_first = [p for p in st.session_state.remaining_a if p[0] in first_names]
            else:
                suggested_first = [p for p in st.session_state.remaining_b if p[0] in first_names]
        if manual_counter:
            counter_names = [x.strip() for x in manual_counter.split(",")]
            if first_picker.startswith("Atown"):
                suggested_counter = [p for p in st.session_state.remaining_b if p[0] in counter_names]
            else:
                suggested_counter = [p for p in st.session_state.remaining_a if p[0] in counter_names]

        st.session_state.matches.append((first_picker, suggested_first, suggested_counter))
        if first_picker.startswith("Atown"):
            st.session_state.remaining_a = remove_players(st.session_state.remaining_a, suggested_first)
            st.session_state.remaining_b = remove_players(st.session_state.remaining_b, suggested_counter)
        else:
            st.session_state.remaining_b = remove_players(st.session_state.remaining_b, suggested_first)
            st.session_state.remaining_a = remove_players(st.session_state.remaining_a, suggested_counter)
        st.rerun()

else:
    st.success("✅ All 4 matches locked in!")

# ---------- DISPLAY CURRENT MATCHES ----------
st.markdown("---")
st.markdown("## 📋 Match Summary")
for i, (first_picker, first_pair, counter_pair) in enumerate(st.session_state.matches, 1):
    st.markdown(f"**Match {i}:** {first_picker}")
    if first_picker.startswith("Atown"):
        st.markdown(
            f"<span style='color:#00A86B;font-weight:bold'>Atown:</span> "
            f"{first_pair[0][0]} ({first_pair[0][1]}), {first_pair[1][0]} ({first_pair[1][1]})",
            unsafe_allow_html=True)
        st.markdown(
            f"<span style='color:#FF6600;font-weight:bold'>Pittsburgh:</span> "
            f"{counter_pair[0][0]} ({counter_pair[0][1]}), {counter_pair[1][0]} ({counter_pair[1][1]})",
            unsafe_allow_html=True)
    else:
        st.markdown(
            f"<span style='color:#FF6600;font-weight:bold'>Pittsburgh:</span> "
            f"{first_pair[0][0]} ({first_pair[0][1]}), {first_pair[1][0]} ({first_pair[1][1]})",
            unsafe_allow_html=True)
        st.markdown(
            f"<span style='color:#00A86B;font-weight:bold'>Atown:</span> "
            f"{counter_pair[0][0]} ({counter_pair[0][1]}), {counter_pair[1][0]} ({counter_pair[1][1]})",
            unsafe_allow_html=True)

# ---------- REMAINING PLAYERS ----------
st.markdown("---")
colA, colB = st.columns(2)
with colA:
    st.markdown("### 🟢 Remaining Atown Players")
    df_a = pd.DataFrame(st.session_state.remaining_a, columns=["Player", "Handicap"])
    st.table(df_a)
with colB:
    st.markdown("### 🟠 Remaining Pittsburgh Players")
    df_b = pd.DataFrame(st.session_state.remaining_b, columns=["Player", "Handicap"])
    st.table(df_b)



