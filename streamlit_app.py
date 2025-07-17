import streamlit as st
from clash_api import get_player, get_battlelog, get_cards
from analysis import (
    compute_win_rate,
    compute_deck_rating,
    detect_tilt,
    analyze_cycle,
    aggro_meter,
    collect_event_stats,
    daily_event_wr,
    record_daily_progress,
    load_progress,
)
import pandas as pd
from youtube_api import search_videos
from coach import request_coaching
from meta import (
    find_matchup_videos,
    meta_pulse,
    get_top_decks,
    get_top_players,
    quartile_benchmarks,
)
from deck_optimizer import smart_swap, upgrade_optimizer
from goals import check_badges, update_goal_tracker
import json

st.title("Clash Royale Analyzer")

tag = st.text_input("Player Tag", key="tag")

if tag:
    try:
        player = get_player(tag)
        battles = get_battlelog(tag)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
    else:
        record_daily_progress(battles, player.get("trophies", 0))
        tabs = st.tabs(["Overview", "Events", "Progress", "Benchmarks"])
        with tabs[0]:
            st.subheader(player.get("name", "Unknown"))
            st.write(f"Trophies: {player.get('trophies', 'N/A')}")
            win_rate = compute_win_rate(battles)
            st.write(f"Recent Win Rate: {win_rate:.0%}")
            if detect_tilt(battles):
                st.warning("Tilt detected: multiple losses in a short time. Consider a break.")
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

            deck_input = st.text_input("Your deck (comma separated)")
            st.write("### Match-up Finder")
            opponent_deck = st.text_input("Opponent deck (comma separated)")
            if deck_input and opponent_deck:
                try:
                    first = deck_input.split(',')[0].strip()
                    second = opponent_deck.split(',')[0].strip()
                    mu_videos = find_matchup_videos(first, second)
                    for mv in mu_videos:
                        st.markdown(f"[{mv['title']}]({mv['url']})")
                except Exception as e:
                    st.error(f"Match-up search failed: {e}")

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
                    if st.button("Smart Swap Suggestions"):
                        pool = [c['name'] for c in card_data]
                        fitness = lambda d: compute_deck_rating(d, card_data)["score"]
                        suggestions = smart_swap(cards, pool, fitness, generations=3)
                        for s in suggestions:
                            st.write(f"{s['deck']} → score {s['score']:.1f}")
                except Exception as e:
                    st.error(f"Deck rating failed: {e}")

            event_json = st.text_area("Battle events JSON (optional)")
            if event_json:
                try:
                    events = json.loads(event_json)
                    cycle = analyze_cycle(events)
                    ratio = aggro_meter(events)
                    st.write("Cycle Coverage:")
                    st.json(cycle)
                    st.write(f"Aggro Ratio (first 60s): {ratio:.2f}")
                except Exception as e:
                    st.error(f"Event analysis failed: {e}")

            if st.button("Get Coaching Tips"):
                insights = {
                    "win_rate": win_rate,
                    "tilt": detect_tilt(battles),
                }
                if event_json:
                    insights.update({"aggro": ratio, **cycle})
                try:
                    tips = request_coaching([
                        {"role": "system", "content": "Tu es coach Clash Royale."},
                        {"role": "user", "content": json.dumps(insights)},
                    ])
                    st.write(tips)
                except Exception as e:
                    st.error(f"Coaching failed: {e}")

            if st.button("Show Trending Decks"):
                try:
                    data = meta_pulse(get_top_decks(limit=1000))
                    for d in data:
                        st.write(d.get("name", "unknown"))
                except Exception as e:
                    st.error(f"Meta Pulse failed: {e}")

            trophies = player.get("trophies", 0)
            goals = {"Champion": 7500}
            update_goal_tracker(goals, trophies)
            st.write("Badges:", check_badges([trophies], goals))

        with tabs[1]:
            st.write("### Event Performance")
            stats = collect_event_stats(battles)
            for s in stats:
                st.write(f"{s['event_id']}: {s['WR']:.0%} ({s['wins']}W/{s['losses']}L)")
            chart = daily_event_wr(battles)
            if chart:
                df = pd.DataFrame(chart)
                st.line_chart(df.set_index('date'))

        with tabs[2]:
            st.write("### Daily Progress")
            progress = load_progress()
            if progress:
                df = pd.DataFrame(progress)
                st.line_chart(df.set_index('date')[['trophies', 'win_rate']])
            else:
                st.info("No progress recorded yet.")

        with tabs[3]:
            st.write("### Quartile Benchmarks")
            try:
                players = get_top_players(limit=1000)
                for p in players:
                    w = p.get('wins', 0)
                    l = p.get('losses', 0)
                    total = w + l
                    p['win_rate'] = w / total if total else 0
                qs = quartile_benchmarks(players, key='trophies')
                for q in qs:
                    st.write(f"Q{q['quartile']}: {q['avg_win_rate']:.0%} win rate")
            except Exception as e:
                st.error(f"Benchmarks failed: {e}")
else:
    st.info("Enter your player tag (without #)")
