import streamlit as st
from clash_api import get_player, get_battlelog
from analysis import compute_win_rate
from youtube_api import search_videos

st.title("Clash Royale Analyzer")

tag = st.text_input("Player Tag", key="tag")

if tag:
    try:
        player = get_player(tag)
        battles = get_battlelog(tag)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
    else:
        st.subheader(player.get("name", "Unknown"))
        st.write(f"Trophies: {player.get('trophies', 'N/A')}")
        win_rate = compute_win_rate(battles)
        st.write(f"Recent Win Rate: {win_rate:.0%}")
        if st.checkbox("Show raw battle log"):
            st.json(battles)

        query = st.text_input("Video search (optional)")
        if query:
            try:
                videos = search_videos(query, max_results=5)
            except Exception as e:
                st.error(f"Video search failed: {e}")
            else:
                st.write("### Video Results")
                for v in videos:
                    st.markdown(f"[{v['title']}]({v['url']})")
else:
    st.info("Enter your player tag (without #)")
