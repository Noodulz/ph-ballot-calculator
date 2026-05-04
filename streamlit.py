import streamlit as st
import pandas as pd
import time
import subprocess
import sys
import tempfile
import re
import altair as alt

st.markdown("# Popheads Ballot Calculator")

choices = pd.DataFrame({
    'ballot type': ['Albums', 'All Stars']
})

ballot_type_option = st.selectbox(
    'What type of rate are you scoring?',
    choices['ballot type']
)

left_column, right_column = st.columns(2)

with right_column:
    chosen = st.radio(
        'Would you like to spoiler tag your scores for Discord pasting purposes?',
        ("Yes", "No"))

precision = st.slider(
    "How many decimal places?",
    min_value=1,
    max_value=3,
    value=1,
    step=1
)

st.text_area("Your ballot:", value="", height=150, key="ballot", label_visibility="visible", help="Paste your ballot here. Make sure that scores are no more than 1 decimal place, song comments are spaced after the score only if using them, album comments have a colon and space after the album title if using them, and only one song can have an 11 and one song can have a 0.")
if st.button("Calculate"):
    latest_iteration = st.empty()
    bar = st.progress(0)

    for i in range(100):
        time.sleep(0.01)
        bar.progress(i + 1, text="Calculating averages...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
        tmp.write(st.session_state.ballot)
        tmp_path = tmp.name
    
    if ballot_type_option == "Albums":
        if chosen == "Yes":
            result = subprocess.run([sys.executable, "calcs/album_calc_SPOILERED.py", tmp_path, str(precision)], capture_output=True, text=True)
        else:
            result = subprocess.run([sys.executable, "calcs/album_calc_NOSPOILER.py", tmp_path, str(precision)], capture_output=True, text=True)
    
    elif ballot_type_option == "All Stars":
        if chosen == "Yes":
            result = subprocess.run([sys.executable, "calcs/allstars_calc_SPOILERED.py", tmp_path, str(precision)], capture_output=True, text=True)
        else:
            result = subprocess.run([sys.executable, "calcs/allstars_calc_NOSPOILER.py", tmp_path, str(precision)], capture_output=True, text=True)

    if result.returncode == 0:
        st.code(result.stdout, language=None, line_numbers=False, wrap_lines=True)
    else:
        st.error("Error during calculation:")
        st.text(result.stderr)