import streamlit as st
from clash_api import get_player, get_battlelog, get_cards
from analysis import compute_win_rate, compute_deck_rating
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

        deck_input = st.text_input("Deck cards (comma separated)")
        if deck_input:
            cards = [c.strip() for c in deck_input.split(',') if c.strip()]
            try:
                card_data = get_cards()
                rating = compute_deck_rating(cards, card_data)
                st.write(f"Average Elixir: {rating['average_elixir']:.2f}")
                st.write(f"Deck Score: {rating['score']:.0f}/100")
                if rating['tips']:
                    st.write("Tips:")
                    for tip in rating['tips']:
                        st.write(f"- {tip}")
            except Exception as e:
                st.error(f"Deck rating failed: {e}")
else:
    st.info("Enter your player tag (without #)")
