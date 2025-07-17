import streamlit as st
from clash_api import get_player, get_battlelog, get_cards

st.set_page_config(page_title="CR Analyzer", layout="centered")
from analysis import (
    compute_win_rate,
    compute_deck_rating,
    detect_tilt,
    analyze_cycle,
    aggro_meter,
    collect_event_stats,
    daily_event_wr,
    load_progress,
    card_cycle_trainer,
    elixir_diff_timeline,
)
import pandas as pd
from youtube_api import search_videos
from coach import get_tips
from meta import (
    find_matchup_videos,
    meta_pulse,
    get_top_decks,
    get_top_players,
    quartile_benchmarks,
    league_benchmarks,
)
import streamlit_authenticator as stauth
from auth import (
    init_db,
    register_user,
    get_user,
    update_playstyle,
    update_mute_toast,
)
from analysis import (
    classify_playstyle,
    progress_to_csv,
    reset_progress,
)
from deck_optimizer import smart_swap, upgrade_optimizer
from digest import daily_digest_info
from goals import check_badges, update_goal_tracker
from gc_coach import start_run, record_match, summarize_run, get_gc_decks
from player_watch import check_new_video, check_deck_change
import json

init_db()
creds = load_credentials()
authenticator = stauth.Authenticate(creds, "crtool", "auth", cookie_expiry_days=7)
name, auth_status, username = authenticator.login("Login", "main")

if not auth_status:
    with st.sidebar.expander("Register"):
        r_email = st.text_input("Email", key="reg_email")
        r_pw = st.text_input("Password", type="password", key="reg_pw")
        r_tag = st.text_input("Player Tag", key="reg_tag")
        r_style = st.selectbox("Playstyle", ["Cycle", "Control", "Beatdown", "Siege", "Bait"], key="reg_style")
        if st.button("Create Account"):
            register_user(r_email, r_pw, r_tag, r_style)
            st.success("Account created. Reload.")
    st.stop()

user = get_user(username)
tag = user.get("player_tag", "")

st.title("Clash Royale Analyzer")

tag = st.text_input("Player Tag", value=tag, key="tag")
playstyle = st.selectbox(
    "Playstyle",
    ["Cycle", "Control", "Beatdown", "Siege", "Bait"],
    index=0 if user.get("playstyle") is None else ["Cycle", "Control", "Beatdown", "Siege", "Bait"].index(user.get("playstyle")),
)
if playstyle != user.get("playstyle"):
    update_playstyle(user["email"], playstyle)

mute_toast = st.checkbox("Mute daily toast", value=bool(user.get("mute_toast")))
if mute_toast != bool(user.get("mute_toast")):
    update_mute_toast(user["email"], mute_toast)

if tag:
    try:
        player = get_player(tag)
        battles = get_battlelog(tag)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
    else:
        digest = daily_digest_info(tag)
        if digest and not mute_toast:
            msg = (
                f"Δ {digest['delta_trophies']} trophies, step {digest['delta_step']} "
                f"WR 24h {digest['win_rate']:.0%}"
            )
            if digest["lucky_drop"]:
                msg += " Lucky Drop!"
            st.toast(msg)
        tabs = st.tabs(["Overview", "Events", "Progress", "Benchmarks", "GC Coach", "Merge Tactics", "Watch"])
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
                    detected = classify_playstyle(cards)
                    st.write(f"Detected playstyle: {detected}")
                    if detected != playstyle:
                        st.info(f"Consider switching playstyle to {detected}")
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

                    opp_full = st.text_input("Opponent full deck for trainer")
                    if opp_full:
                        deck_list = [c.strip() for c in opp_full.split(',') if c.strip()]
                        opp_plays = [e.get('card') for e in events if e.get('side') == 'opponent']
                        hands = card_cycle_trainer(deck_list, opp_plays)
                        if hands:
                            st.write("Opponent current hand:", ', '.join(hands[-1]))

                    timeline = elixir_diff_timeline(events)
                    if timeline:
                        df = pd.DataFrame(timeline)
                        max_t = int(df['time'].max())
                        rng = st.slider("Time range", 0, max_t, (0, max_t))
                        mask = (df['time'] >= rng[0]) & (df['time'] <= rng[1])
                        st.line_chart(df[mask].set_index('time')['diff'])
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
                    tips = get_tips(insights)
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
                csv_data = progress_to_csv(progress)
                st.download_button(
                    "Export CSV",
                    data=csv_data,
                    file_name="progress.csv",
                    mime="text/csv",
                )
            else:
                st.info("No progress recorded yet.")
            if st.button("Reset History"):
                reset_progress()
                st.success("History cleared")

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
                if player.get('leagueRank'):
                    lb = league_benchmarks(player.get('leagueRank'))
                    st.write(f"Your league avg WR: {lb.get('avg_win_rate',0):.0%}")
            except Exception as e:
                st.error(f"Benchmarks failed: {e}")

        with tabs[4]:
            st.write("### Grand Challenge Coach")
            deck_gc = st.text_input("GC Deck (comma separated)", key="gc_deck")
            if st.button("Start GC Run") and deck_gc:
                run_id = start_run([c.strip() for c in deck_gc.split(',') if c.strip()])
                st.session_state["gc_run_id"] = run_id
                st.success(f"Started run {run_id}")
            run_id = st.session_state.get("gc_run_id")
            if run_id:
                st.write(f"Current Run: {run_id}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Record Win"):
                        record_match(run_id, True, player.get("trophies", 0))
                with col2:
                    if st.button("Record Loss"):
                        record_match(run_id, False, player.get("trophies", 0))
                summary = summarize_run(run_id)
                st.write(f"{summary['wins']}/{summary['total']} wins", )
                st.write(f"Avg Opponent Trophies: {summary['avg_elo']:.0f}")
            if st.button("Show Top GC Decks"):
                try:
                    decks = get_gc_decks(limit=10)
                    for d in decks:
                        st.write(d.get("name", "unknown"))
                except Exception as e:
                    st.error(f"Failed to fetch GC decks: {e}")
        with tabs[5]:
            st.write("### Merge Tactics")
            if st.button("Show Tier List"):
                try:
                    stats = get_merge_leaderboard(limit=100)
                    tier = card_tier_list(stats)
                    for entry in tier[:10]:
                        st.write(f"{entry['card']}: {entry['eff']:.2f}")
                except Exception as e:
                    st.error(f"Merge data failed: {e}")
        with tabs[6]:
            st.write("### Watch")
            ch_id = st.text_input("YouTube channel ID")
            if st.button("Check Videos") and ch_id:
                try:
                    vid = check_new_video(ch_id)
                    if vid:
                        st.success(f"New video: [{vid['title']}]({vid['url']})")
                    else:
                        st.info("No new video")
                except Exception as e:
                    st.error(f"Video check failed: {e}")
            watch_tag = st.text_input("Player tag to watch")
            if st.button("Check Deck") and watch_tag:
                try:
                    deck = check_deck_change(watch_tag)
                    if deck:
                        st.success("New deck: " + ', '.join(deck))
                    else:
                        st.info("No change")
                except Exception as e:
                    st.error(f"Deck check failed: {e}")
