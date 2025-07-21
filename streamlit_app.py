import streamlit as st
from itertools import combinations

# ========== DATA SETUP ==========
team_a = [
    ('Farley', 19), ('Fil', 28.7), ('Sean', 1.4), ('Tom', 14.2),
    ('Alexandra', 9.4), ('Pail', 22.3), ('Greg', 13.7), ('Zimmel', 20.6)
]
team_b = [
    ('Adawg Maize', 12.6), ('Beans Kujava', 16.3), ('Jerry Curl', 13.3),
    ('Pat Swag', 16.9), ('Dmac', 5.7), ('Oobs', 11.9),
    ('Ribs McClure', 17.9), ('Bman', 3.8)
]

# ========== SESSION STATE ==========
if 'used_a' not in st.session_state:
    st.session_state.used_a = set()
if 'used_b' not in st.session_state:
    st.session_state.used_b = set()
if 'round' not in st.session_state:
    st.session_state.round = 1
if 'matchups' not in st.session_state:
    st.session_state.matchups = []

# ========== HELPERS ==========
def get_available(pool, used):
    return [p for p in pool if p[0] not in used]

def pairing_score(pair_sent, pair_counter, alpha=1.0, beta=0.75):
    avg_sent = sum(p[1] for p in pair_sent) / 2
    avg_counter = sum(p[1] for p in pair_counter) / 2
    avg_diff = abs(avg_sent - avg_counter)
    balance = abs(pair_counter[0][1] - pair_counter[1][1])
    return alpha * avg_diff - beta * balance

def get_best_pair(pool, used):
    best_spread = -1
    best_pair = None
    for a, b in combinations(get_available(pool, used), 2):
        spread = abs(a[1] - b[1])
        if spread > best_spread:
            best_spread = spread
            best_pair = (a, b)
    return best_pair

def get_best_counter(sent, pool, used):
    best_score = float('inf')
    best = None
    for a, b in combinations(get_available(pool, used), 2):
        score = pairing_score(sent, (a, b))
        if score < best_score:
            best_score = score
            best = (a, b)
    return best

def format_pair(pair):
    return f"{pair[0][0]} ({pair[0][1]}) + {pair[1][0]} ({pair[1][1]})"

# ========== UI ==========
st.title("🏌️ Golf Trip Draft Pairing Optimizer")
st.subheader(f"Match {st.session_state.round} of 4")

if st.session_state.round > 4:
    st.success("✅ All 4 matches locked in!")
    for i, match in enumerate(st.session_state.matchups, 1):
        st.markdown(f"**Match {i}**")
        st.write(f"🔹 {match['sender_team']} sent: {format_pair(match['sent'])}")
        st.write(f"🔸 {match['counter_team']} countered with: {format_pair(match['counter'])}")
    st.button("🔁 Reset Draft", on_click=lambda: [st.session_state.clear()])
    st.stop()

# Who sends this round?
sender = "Atown" if st.session_state.round % 2 == 1 else "Pittsburgh"
receiver = "Pittsburgh" if sender == "Atown" else "Atown"

pool_send = team_a if sender == "Atown" else team_b
pool_recv = team_b if sender == "Atown" else team_a
used_send = st.session_state.used_a if sender == "Atown" else st.session_state.used_b
used_recv = st.session_state.used_b if sender == "Atown" else st.session_state.used_a

st.markdown(f"**{sender} sends out a pairing**")
avail_send = get_available(pool_send, used_send)
p1 = st.selectbox("Choose first player", [p[0] for p in avail_send], key=f"{sender}_1")
p2_options = [p[0] for p in avail_send if p[0] != p1]
p2 = st.selectbox("Choose second player", p2_options, key=f"{sender}_2")

if p1 and p2:
    sent_pair = [p for p in pool_send if p[0] in (p1, p2)]
    st.markdown(f"### {receiver} Suggested Counter Pairing")
    suggested = get_best_counter(sent_pair, pool_recv, used_recv)
    if suggested:
        st.write(format_pair(suggested))
    else:
        st.warning("No counter pairings available.")

    st.markdown(f"**Override {receiver}'s counter?**")
    avail_recv = get_available(pool_recv, used_recv)
    c1 = st.selectbox("Choose first counter player", [p[0] for p in avail_recv], key=f"{receiver}_1")
    c2_options = [p[0] for p in avail_recv if p[0] != c1]
    c2 = st.selectbox("Choose second counter player", c2_options, key=f"{receiver}_2")

    if st.button("✅ Lock In Match"):
        counter_pair = [p for p in pool_recv if p[0] in (c1, c2)]
        st.session_state.used_a.update([p[0] for p in sent_pair]) if sender == "Atown" else st.session_state.used_b.update([p[0] for p in sent_pair])
        st.session_state.used_b.update([p[0] for p in counter_pair]) if receiver == "Pittsburgh" else st.session_state.used_a.update([p[0] for p in counter_pair])
        st.session_state.matchups.append({
            'sender_team': sender,
            'sent': sent_pair,
            'counter_team': receiver,
            'counter': counter_pair
        })
        st.session_state.round += 1
        st.experimental_rerun()
