import streamlit as st
import pandas as pd
import time
import subprocess
import sys
import tempfile
import re
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict
import numpy as np

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

def parse_ballot_data(ballot_text):
    """Parse ballot text to extract all song ratings and album information"""
    lines = ballot_text.strip().split('\n')
    
    songs_data = []
    current_album = None
    float_pattern = re.compile(r"[-+]?\d*\.\d+|\d+")
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith("Username:") or line == "END":
            continue
            
        if line.startswith("BONUS TRACKS"):
            current_album = None
            continue
            
        if line.startswith("Album:"):
            # Extract album title
            album_info = line.split(":", 1)[1].strip()
            if ":" in album_info:
                current_album = album_info.split(":", 1)[0].strip()
            else:
                current_album = album_info
            continue
        
        # Parse song line
        if current_album and ":" in line:
            parts = line.split(":", 1)
            song_name = parts[0].strip()
            after_colon = parts[1].strip() if len(parts) > 1 else ""
            
            if after_colon:
                match = float_pattern.search(after_colon)
                if match:
                    rating = float(match.group())
                    songs_data.append({
                        'song': song_name,
                        'album': current_album,
                        'rating': rating
                    })
    
    return pd.DataFrame(songs_data)

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
        
        # Parse ballot data for visualizations
        df = parse_ballot_data(st.session_state.ballot)
        
        if not df.empty:
            st.markdown("---")
            
            # Calculate statistics
            overall_avg = df['rating'].mean()
            album_avgs = df.groupby('album')['rating'].mean().sort_values(ascending=False)
            highest_album = album_avgs.index[0] if len(album_avgs) > 0 else "N/A"
            lowest_album = album_avgs.index[-1] if len(album_avgs) > 0 else "N/A"
            num_tens = len(df[df['rating'] == 10.0])
            eleven_song = df[df['rating'] == 11.0]['song'].tolist()
            zero_song = df[df['rating'] == 0.0]['song'].tolist()
            
            # Cumulative Stats Cards
            st.markdown("## Cumulative Stats")
            
            # Create columns for stats cards
            cols = st.columns(4)
            
            with cols[0]:
                st.metric("Overall Average", f"{overall_avg:.{precision}f}")
            
            with cols[1]:
                st.metric("Highest Rated Album", highest_album, f"{album_avgs.iloc[0]:.{precision}f}")
            
            with cols[2]:
                st.metric("Lowest Rated Album", lowest_album, f"{album_avgs.iloc[-1]:.{precision}f}")
            
            with cols[3]:
                st.metric("Number of 10s", num_tens)
            
            # Additional row for 11 and 0 if they exist
            special_cols = []
            if eleven_song:
                special_cols.append(("11 Recipient:", eleven_song[0]))
            if zero_song:
                special_cols.append(("0 Recipient:", zero_song[0]))
            
            if special_cols:
                cols2 = st.columns(len(special_cols))
                for idx, (label, song) in enumerate(special_cols):
                    with cols2[idx]:
                        st.metric(label, song)
            
            # Score Distribution Histogram
            st.markdown("---")
            st.markdown("## Score Distribution")
            
            # Create score bins (0-11)
            df['score_bin'] = df['rating'].apply(lambda x: int(x))
            score_counts = df.groupby('score_bin').size().reset_index(name='count')
            
            # Create a complete range from 0 to 11
            all_scores = pd.DataFrame({'score_bin': range(0, 12)})
            score_counts = all_scores.merge(score_counts, on='score_bin', how='left').fillna(0)
            score_counts['count'] = score_counts['count'].astype(int)
            
            # Create hover text with song lists
            hover_texts = []
            for score in range(0, 12):
                songs_in_bin = df[df['score_bin'] == score]['song'].tolist()
                if songs_in_bin:
                    hover_text = f"Score {score}: {len(songs_in_bin)} song(s)<br>" + "<br>".join([f"• {song}" for song in songs_in_bin])
                else:
                    hover_text = f"Score {score}: 0 songs"
                hover_texts.append(hover_text)
            
            score_counts['hover_text'] = hover_texts
            
            fig_hist = px.bar(
                score_counts,
                x='score_bin',
                y='count',
                labels={'score_bin': 'Score', 'count': 'Number of Songs'},
                title='Distribution of Scores',
                hover_data={'hover_text': True, 'score_bin': False, 'count': False},
                color_discrete_sequence=['#BB7F03']
            )
            
            fig_hist.update_traces(hovertemplate='%{customdata[0]}<extra></extra>')
            fig_hist.update_xaxes(tickmode='linear', tick0=0, dtick=1)
            fig_hist.update_layout(height=400)
            
            st.plotly_chart(fig_hist, use_container_width=True)
            
            # Album Distribution Box Plot
            st.markdown("---")
            st.markdown("## Album Score Distribution")
            
            fig_box = px.box(
                df,
                x='album',
                y='rating',
                labels={'album': 'Album', 'rating': 'Score'},
                title='Variance per Album',
                points='all',
                hover_data={'song': True},
                color_discrete_sequence=['#BB7F03']
            )
            
            fig_box.update_layout(height=500, xaxis_tickangle=-45)
            fig_box.update_traces(marker=dict(size=8, color='#BB7F03'))
            
            st.plotly_chart(fig_box, use_container_width=True)
            
            # Top 5 and Bottom 5 Songs
            st.markdown("---")
            st.markdown("## Top 5 Songs")
            
            top_5 = df.nlargest(5, 'rating')[['song', 'album', 'rating']].reset_index(drop=True)
            top_5.index = top_5.index + 1
            
            for idx, row in top_5.iterrows():
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    st.markdown(f"**#{idx}**")
                with col2:
                    st.markdown(f"**{row['song']}** ")
                with col3:
                    st.markdown(f"**{row['rating']:.{precision}f}**")
            
            st.markdown("## Bottom 5 Songs")
            
            bottom_5 = df.nsmallest(5, 'rating')[['song', 'album', 'rating']].reset_index(drop=True)
            bottom_5 = bottom_5.iloc[::-1].reset_index(drop=True)
            bottom_5.index = bottom_5.index + 1
            
            for idx, row in bottom_5.iterrows():
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    st.markdown(f"**#{idx}**")
                with col2:
                    st.markdown(f"**{row['song']}**")
                with col3:
                    st.markdown(f"**{row['rating']:.{precision}f}**")
    else:
        st.error(f"Error during calculation: {result.stderr}")
        st.text(result.stderr)

# Made with Bob
