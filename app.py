import streamlit as st
import pandas as pd
from graph import create_graph, simulate_tournament_monte_carlo
from db import get_team_base_data, get_h2h_matches, get_all_teams_data

st.set_page_config(
    page_title="2026 World Cup AI Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# スタイリング調整
st.markdown("""
<style>
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.2rem;
        color: #4B5563;
        text-align: center;
        margin-bottom: 2rem;
    }
    .debate-card {
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 5px solid #3B82F6;
        background-color: #F3F4F6;
    }
    .debate-agent {
        font-weight: bold;
        color: #1E40AF;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>⚽ 2026 World Cup AI Predictor</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>推論エージェント討論 ＆ モンテカルロ・トーナメントシミュレーター</div>", unsafe_allow_html=True)

# データベースからチーム一覧を取得
all_teams = get_all_teams_data()
if all_teams:
    team_names = sorted([t["name"] for t in all_teams])
else:
    # データベース未初期化時のフォールバック
    team_names = ["Japan", "Brazil", "Germany", "Spain", "Netherlands", "Argentina", "France", "England"]

# タブ定義
tab1, tab2 = st.tabs(["⚔️ 1試合 勝敗予想", "🏆 トーナメントシミュレータ"])

# ----------------------------------------------------
# タブ 1: 1試合勝敗予想
# ----------------------------------------------------
with tab1:
    st.header("対戦国の分析と勝率シミュレーション")
    
    col1, col2 = st.columns(2)
    with col1:
        team_a = st.selectbox("Team A (Home)", team_names, index=team_names.index("Japan") if "Japan" in team_names else 0)
    with col2:
        team_b = st.selectbox("Team B (Away)", team_names, index=team_names.index("Brazil") if "Brazil" in team_names else 1)
        
    # スタジアム選択を追加
    stadium_options = {
        "MetLife Stadium (New York/New Jersey) [標準環境]": ("MetLife Stadium (New York/New Jersey)", "standard"),
        "Estadio Azteca (Mexico City) [標高 2,200m 高地]": ("Estadio Azteca (Mexico City)", "altitude"),
        "BC Place (Vancouver) [高速人工芝]": ("BC Place (Vancouver)", "turf"),
        "Hard Rock Stadium (Miami) [酷暑多湿]": ("Hard Rock Stadium (Miami)", "heat"),
    }
    selected_stadium_label = st.selectbox("🏟️ 開催スタジアム（環境条件）を選択してください", list(stadium_options.keys()))
    stadium_name, stadium_env = stadium_options[selected_stadium_label]
        
    if st.button("AI予想を実行する", type="primary"):
        if team_a == team_b:
            st.error("異なるチームを選択してください。")
        else:
            with st.spinner("番記者エージェントが過去のデータを元に討論中..."):
                # Supabaseからデータ取得
                team_a_data = get_team_base_data(team_a)
                team_b_data = get_team_base_data(team_b)
                h2h_data = get_h2h_matches(team_a, team_b)
                
                # 重要度別の加重平均得点力を動的に算出
                team_a_weighted_goals = get_weighted_avg_goals(team_a, fallback_value=float(team_a_data["avg_goals"]))
                team_b_weighted_goals = get_weighted_avg_goals(team_b, fallback_value=float(team_b_data["avg_goals"]))
                
                # 初期状態
                initial_state = {
                    "team_a": team_a,
                    "team_b": team_b,
                    "team_a_base_elo": float(team_a_data["base_elo"]),
                    "team_b_base_elo": float(team_b_data["base_elo"]),
                    "team_a_avg_goals": team_a_weighted_goals,
                    "team_b_avg_goals": team_b_weighted_goals,
                    "team_a_market_value": float(team_a_data.get("market_value", 50.0)),
                    "team_b_market_value": float(team_b_data.get("market_value", 50.0)),
                    "team_a_tactics": team_a_data.get("tactics_style", "balanced"),
                    "team_b_tactics": team_b_data.get("tactics_style", "balanced"),
                    "stadium_name": stadium_name,
                    "stadium_env": stadium_env,
                    "h2h_history": h2h_data,
                    "debate_history": [],
                    "agent_analysis": "",
                    "team_a_modifier": 1.0,
                    "team_b_modifier": 1.0,
                }
                
                # グラフ実行
                graph = create_graph()
                result = graph.invoke(initial_state)
                
                st.success("予想プロセスが完了しました！")
                
                # レイアウト表示: 左右カラム (討論 vs 結果)
                res_col1, res_col2 = st.columns([3, 2])
                
                with res_col1:
                    st.subheader("🎤 番記者による試合前討論 (Debate)")
                    
                    for speech in result.get("debate_history", []):
                        agent_name = speech["agent"]
                        content = speech["content"]
                        
                        # 吹き出し風のスタイル表示
                        is_rebuttal = "再反論" in agent_name or "最後" in agent_name
                        border_color = "#EF4444" if team_b in agent_name else "#3B82F6"
                        bg_color = "#FEF2F2" if team_b in agent_name else "#EFF6FF"
                        
                        st.markdown(f"""
                        <div style="border-radius: 8px; padding: 12px; margin-bottom: 12px; border-left: 5px solid {border_color}; background-color: {bg_color};">
                            <div style="font-weight: bold; color: {border_color}; font-size: 0.95rem; margin-bottom: 4px;">{agent_name}</div>
                            <div style="font-size: 0.95rem; line-height: 1.4; color: #1F2937;">{content}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                with res_col2:
                    st.subheader("📊 予測結果")
                    st.markdown(result["final_summary"])
                    
                    # プログレスバーでの視覚化
                    st.markdown("#### 勝率ビジュアル割合")
                    p_a = result["prob_team_a_win"]
                    p_d = result["prob_draw"]
                    p_b = result["prob_team_b_win"]
                    
                    st.write(f"**{team_a} 勝利**: {p_a:.1%}")
                    st.progress(p_a)
                    st.write(f"**引き分け**: {p_d:.1%}")
                    st.progress(p_d)
                    st.write(f"**{team_b} 勝利**: {p_b:.1%}")
                    st.progress(p_b)
                    
                    # 詳細データの折りたたみ表示
                    with st.expander("🔍 計算パラメーター（内訳）"):
                        st.write(f"**{team_a}** Base Elo: {result['team_a_base_elo']} | 戦術: {result['team_a_tactics'].capitalize()} | 市場価値: {result['team_a_market_value']:.0f}M€ | 加重平均得点: {team_a_weighted_goals:.2f}")
                        st.write(f"**{team_b}** Base Elo: {result['team_b_base_elo']} | 戦術: {result['team_b_tactics'].capitalize()} | 市場価値: {result['team_b_market_value']:.0f}M€ | 加重平均得点: {team_b_weighted_goals:.2f}")
                        st.write(f"**{team_a}** 最終期待得点: {result['expected_goals_a']:.2f} (補正: {result['team_a_modifier']:.2f})")
                        st.write(f"**{team_b}** 最終期待得点: {result['expected_goals_b']:.2f} (補正: {result['team_b_modifier']:.2f})")
                        
                        if h2h_data:
                            st.write("**過去の対戦実績 (H2H):**")
                            for m in h2h_data[:5]:
                                st.write(f"- {m['date']}: {m['home_team']} {m['home_score']} - {m['away_score']} {m['away_team']} ({m['tournament']})")
                        else:
                            st.write("*過去に対戦データはありません。*")

# ----------------------------------------------------
# タブ 2: トーナメントシミュレータ
# ----------------------------------------------------
with tab2:
    st.header("🏆 2026年ワールドカップ モンテカルロ・シミュレータ")
    st.markdown("48チーム全てのElo及びグループ割から、大会全体の行方を1,000回シミュレートして各国の勝ち上がり確率を求めます。")
    
    # データベースが空の場合は警告を表示
    if not all_teams:
        st.warning("⚠️ データベースに48チームが登録されていません。先に `update_db.py` を実行するか、Supabaseで `update_schema.sql` を実行してください。")
    
    sim_button = st.button("シミュレーションを実行する (1,000回)", type="primary", disabled=not all_teams)
    
    # セッション状態の初期化
    if "sim_results" not in st.session_state:
        st.session_state.sim_results = None
        
    if sim_button and all_teams:
        with st.spinner("グループステージから決勝戦までの1,000大会（計104,000試合）を高速シミュレート中..."):
            prob_results = simulate_tournament_monte_carlo(all_teams, num_simulations=1000)
            
            # 結果をDataFrameに変換して集計
            rows = []
            for name, stages in prob_results.items():
                team_info = next((t for t in all_teams if t["name"] == name), None)
                group_name = team_info["group_name"] if team_info else "-"
                elo = team_info["base_elo"] if team_info else 1500
                rows.append({
                    "国名": name,
                    "グループ": group_name,
                    "Elo": int(elo),
                    "決勝T進出 (R32)": stages["r32"],
                    "ベスト16": stages["r16"],
                    "ベスト8": stages["qf"],
                    "ベスト4": stages["sf"],
                    "決勝進出": stages["final"],
                    "優勝確率 🏆": stages["winner"]
                })
                
            df_res = pd.DataFrame(rows)
            st.session_state.sim_results = df_res
            st.success("シミュレーションが完了しました！")
            
    # シミュレーション結果がセッション内にあれば表示
    if st.session_state.sim_results is not None:
        df_res = st.session_state.sim_results
        
        # 優勝確率順にソート
        df_winner_sorted = df_res.sort_values(by="優勝確率 🏆", ascending=False).reset_index(drop=True)
        
        # 1. 優勝本命トップ10のグラフ表示
        st.subheader("🥇 優勝確率ランキング (Top 10)")
        top_10 = df_winner_sorted.head(10)
        st.bar_chart(data=top_10.set_index("国名")["優勝確率 🏆"])
        
        # 2. 全国の進出確率テーブル
        st.subheader("📋 国別の全ステージ勝ち上がり確率一覧")
        
        # 表フォーマットの調整 (パーセンテージ表記)
        formatted_df = df_winner_sorted.copy()
        for col in ["決勝T進出 (R32)", "ベスト16", "ベスト8", "ベスト4", "決勝進出", "優勝確率 🏆"]:
            formatted_df[col] = formatted_df[col].map(lambda x: f"{x:.1%}" if isinstance(x, float) else x)
            
        st.dataframe(formatted_df, use_container_width=True)
        
        # 3. 特定国ピンポイントサーチ
        st.subheader("🔍 特定国のシミュレーション結果詳細")
        search_team = st.selectbox("詳細を見たいチームを選択してください", sorted(df_res["国名"].unique()), key="search_team_selectbox")
        
        team_stats = df_res[df_res["国名"] == search_team].iloc[0]
        
        # カラムで段階表示
        sub_col1, sub_col2, sub_col3, sub_col4, sub_col5, sub_col6 = st.columns(6)
        sub_col1.metric("決勝T進出", f"{team_stats['決勝T進出 (R32)']:.1%}")
        sub_col2.metric("ベスト16", f"{team_stats['ベスト16']:.1%}")
        sub_col3.metric("ベスト8", f"{team_stats['ベスト8']:.1%}")
        sub_col4.metric("ベスト4", f"{team_stats['ベスト4']:.1%}")
        sub_col5.metric("決勝進出", f"{team_stats['決勝進出']:.1%}")
        sub_col6.metric("優勝確率 🏆", f"{team_stats['優勝確率 🏆']:.1%}")
        
        # チャート表示
        progression_data = pd.Series({
            "R32": team_stats["決勝T進出 (R32)"],
            "R16": team_stats["ベスト16"],
            "QF": team_stats["ベスト8"],
            "SF": team_stats["ベスト4"],
            "Final": team_stats["決勝進出"],
            "Champion": team_stats["優勝確率 🏆"]
        })
        st.line_chart(progression_data)
