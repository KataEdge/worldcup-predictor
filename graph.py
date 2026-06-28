from langgraph.graph import StateGraph, END
from state import WorldCupState
import scipy.stats as stats
import numpy as np
import os
import random
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field


# 構造化出力のためのPydanticモデル (最終要約用)
class AgentAnalysisOutput(BaseModel):
    agent_analysis: str = Field(
        description="両チームの討論を踏まえた、最終的な戦術分析・解説サマリー"
    )
    team_a_modifier: float = Field(
        description="Team Aの得点力に対する補正係数（0.8〜1.2）"
    )
    team_b_modifier: float = Field(
        description="Team Bの得点力に対する補正係数（0.8〜1.2）"
    )


# ==========================================
# 戦術相性およびスタジアム環境補正ヘルパー
# ==========================================


def get_tactical_modifier(style_a: str, style_b: str) -> tuple:
    """
    戦術スタイルの3すくみによる得点力補正
    ポゼッション ➔ ハイプレス ➔ カウンター ➔ ポゼッション
    """
    if style_a == "possession" and style_b == "press":
        return 1.05, 0.95
    elif style_a == "press" and style_b == "counter":
        return 1.05, 0.95
    elif style_a == "counter" and style_b == "possession":
        return 1.05, 0.95
    elif style_b == "possession" and style_a == "press":
        return 0.95, 1.05
    elif style_b == "press" and style_a == "counter":
        return 0.95, 1.05
    elif style_b == "counter" and style_a == "possession":
        return 0.95, 1.05
    return 1.0, 1.0


def get_stadium_modifier(
    team_name: str, team_tactics: str, stadium_env: str, host_country: str
) -> float:
    """
    スタジアム環境（高地・人工芝・酷暑）とホームアドバンテージによる補正
    """
    modifier = 1.0

    # 1. ホームアドバンテージ (+10%のバフ)
    if team_name == host_country:
        modifier *= 1.10

    # 2. スタジアム環境デバフ/バフ
    if stadium_env == "altitude":
        # 南米勢(CONMEBOL) + メキシコ以外のチームは標高2,200mの高地による酸素薄で得点力-10%の疲労デバフ
        accustomed_teams = {
            "Brazil",
            "Argentina",
            "Uruguay",
            "Colombia",
            "Paraguay",
            "Ecuador",
            "Mexico",
        }
        if team_name not in accustomed_teams:
            modifier *= 0.90

    elif stadium_env == "turf":
        # 人工芝グラウンドはボールが走るため、ポゼッションスタイルに+5%のバフ、それ以外に-5%のデバフ
        if team_tactics == "possession":
            modifier *= 1.05
        else:
            modifier *= 0.95

    elif stadium_env == "heat":
        # 35度を超える酷暑多湿は欧州勢(UEFA) + 東アジア勢(日韓)にスタミナ低下で-5%のデバフ
        heat_sensitive = {
            "Germany",
            "Spain",
            "France",
            "England",
            "Portugal",
            "Netherlands",
            "Belgium",
            "Croatia",
            "Switzerland",
            "Austria",
            "Czechia",
            "Scotland",
            "Norway",
            "Sweden",
            "Bosnia and Herzegovina",
            "Türkiye",
            "Japan",
            "South Korea",
        }
        if team_name in heat_sensitive:
            modifier *= 0.95

    return modifier


# ==========================================
# LangGraphノード関数定義
# ==========================================


def debate_agent_a_node(state: WorldCupState) -> dict:
    """チームA（Home側）を擁護する番記者エージェントの初期主張"""
    team_a = state["team_a"]
    team_b = state["team_b"]
    h2h = state.get("h2h_history", [])

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {
            "debate_history": [
                {
                    "agent": f"{team_a} 担当記者",
                    "content": f"{team_a}は今回の対戦において優位に立っています。",
                }
            ]
        }

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
        prompt = PromptTemplate.from_template(
            "あなたはサッカーの【{team_a}】代表チーム担当の熱心な番記者です。まもなく【{team_b}】との一戦が行われます。\n"
            "チーム情報:\n"
            "- {team_a} (ベースElo: {elo_a}, 平均得点: {goals_a}, 戦術スタイル: {tactics_a})\n"
            "- {team_b} (ベースElo: {elo_b}, 平均得点: {goals_b}, 戦術スタイル: {tactics_b})\n"
            "過去の直接対決(H2H)データ: {h2h}\n\n"
            "あなたの任務は、【{team_a}】が今回勝つべき論理的な理由、チームの強み（Eloや戦術）、相手の弱点、"
            "および過去の対戦相性を踏まえ、【{team_a}】側の視点から説得力のある主張を展開することです。\n"
            "サッカージャーナリストらしく、熱くかつ論理的に1段落（200文字〜300文字程度）で主張を述べてください。"
        )
        chain = prompt | llm
        result = chain.invoke(
            {
                "team_a": team_a,
                "team_b": team_b,
                "elo_a": state["team_a_base_elo"],
                "goals_a": state["team_a_avg_goals"],
                "tactics_a": state.get("team_a_tactics", "balanced"),
                "elo_b": state["team_b_base_elo"],
                "goals_b": state["team_b_avg_goals"],
                "tactics_b": state.get("team_b_tactics", "balanced"),
                "h2h": str(h2h),
            }
        )

        return {
            "debate_history": [
                {"agent": f"{team_a} 担当記者", "content": result.content}
            ]
        }
    except Exception as e:
        print(f"Error in debate_agent_a: {e}")
        return {
            "debate_history": [
                {
                    "agent": f"{team_a} 担当記者",
                    "content": f"エラーのため主張を生成できませんでした: {e}",
                }
            ]
        }


def debate_agent_b_node(state: WorldCupState) -> dict:
    """チームB（Away側）を擁護する番記者エージェントの初期主張＆反論"""
    team_a = state["team_a"]
    team_b = state["team_b"]
    h2h = state.get("h2h_history", [])
    debate_history = state.get("debate_history", [])
    opponent_arg = debate_history[-1]["content"] if debate_history else "特になし"

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {
            "debate_history": debate_history
            + [
                {
                    "agent": f"{team_b} 担当記者",
                    "content": f"{team_b}こそがこの試合を支配するでしょう。",
                }
            ]
        }

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
        prompt = PromptTemplate.from_template(
            "あなたはサッカーの【{team_b}】代表チーム担当の熱心な番記者です。まもなく【{team_a}】との一戦が行われます。\n"
            "チーム情報:\n"
            "- {team_a} (ベースElo: {elo_a}, 平均得点: {goals_a}, 戦術スタイル: {tactics_a})\n"
            "- {team_b} (ベースElo: {elo_b}, 平均得点: {goals_b}, 戦術スタイル: {tactics_b})\n"
            "過去の直接対決(H2H)データ: {h2h}\n\n"
            "相手（{team_a}）の担当記者から以下の主張がなされています：\n"
            "------\n"
            "{opponent_arg}\n"
            "------\n\n"
            "あなたの任務は、相手の主張の矛盾や弱点を指摘して論破しつつ、【{team_b}】が今回勝利する理由、"
            "チームの強み（Eloや戦術）、相手の守備の欠陥などを【{team_b}】側の視点から説得力のある主張として展開することです。\n"
            "論理的かつ情熱的に1段落（200文字〜300文字程度）で述べてください。"
        )
        chain = prompt | llm
        result = chain.invoke(
            {
                "team_a": team_a,
                "team_b": team_b,
                "elo_a": state["team_a_base_elo"],
                "goals_a": state["team_a_avg_goals"],
                "tactics_a": state.get("team_a_tactics", "balanced"),
                "elo_b": state["team_b_base_elo"],
                "goals_b": state["team_b_avg_goals"],
                "tactics_b": state.get("team_b_tactics", "balanced"),
                "h2h": str(h2h),
                "opponent_arg": opponent_arg,
            }
        )

        return {
            "debate_history": debate_history
            + [{"agent": f"{team_b} 担当記者", "content": result.content}]
        }
    except Exception as e:
        print(f"Error in debate_agent_b: {e}")
        return {
            "debate_history": debate_history
            + [
                {
                    "agent": f"{team_b} 担当記者",
                    "content": f"エラーのため主張を生成できませんでした: {e}",
                }
            ]
        }


def debate_rebuttal_a_node(state: WorldCupState) -> dict:
    """チームA担当記者の再反論"""
    team_a = state["team_a"]
    team_b = state["team_b"]
    debate_history = state.get("debate_history", [])
    opponent_arg = (
        debate_history[-1]["content"] if len(debate_history) >= 1 else "特になし"
    )
    my_first_arg = (
        debate_history[-2]["content"] if len(debate_history) >= 2 else "特になし"
    )

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {
            "debate_history": debate_history
            + [
                {
                    "agent": f"{team_a} 担当記者 (再反論)",
                    "content": "私たちの分析が正しいことは試合で証明されます。",
                }
            ]
        }

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
        prompt = PromptTemplate.from_template(
            "あなたはサッカー【{team_a}】担当記者です。相手（{team_b}）の記者から以下の反論を受けました：\n"
            "------\n"
            "{opponent_arg}\n"
            "------\n\n"
            "あなたの最初の主張: {my_first_arg}\n\n"
            "相手記者の反論に再反論（Rebuttal）してください。相手の主張する戦術や強みを打ち消し、"
            "やはり【{team_a}】が優位である理由（最近のスタッツ、相性、精神的な優位性など）をもう一度補強してください。\n"
            "議論をヒートアップさせつつも、スタッツアナリストとしての冷静さを保ちながら1段落（200文字〜300文字程度）で述べてください。"
        )
        chain = prompt | llm
        result = chain.invoke(
            {
                "team_a": team_a,
                "team_b": team_b,
                "opponent_arg": opponent_arg,
                "my_first_arg": my_first_arg,
            }
        )

        return {
            "debate_history": debate_history
            + [{"agent": f"{team_a} 担当記者 (再反論)", "content": result.content}]
        }
    except Exception as e:
        return {
            "debate_history": debate_history
            + [
                {
                    "agent": f"{team_a} 担当記者 (再反論)",
                    "content": f"エラーが発生しました: {e}",
                }
            ]
        }


def debate_rebuttal_b_node(state: WorldCupState) -> dict:
    """チームB担当記者の最後の反論"""
    team_a = state["team_a"]
    team_b = state["team_b"]
    debate_history = state.get("debate_history", [])
    opponent_arg = (
        debate_history[-1]["content"] if len(debate_history) >= 1 else "特になし"
    )
    my_first_arg = (
        debate_history[-2]["content"] if len(debate_history) >= 2 else "特になし"
    )

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {
            "debate_history": debate_history
            + [
                {
                    "agent": f"{team_b} 担当記者 (最後)",
                    "content": "私たちの勝利は揺るぎません。",
                }
            ]
        }

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
        prompt = PromptTemplate.from_template(
            "あなたはサッカー【{team_b}】担当記者です。相手（{team_a}）の記者から以下の再反論を受けました：\n"
            "------\n"
            "{opponent_arg}\n"
            "------\n\n"
            "あなたの最初の主張: {my_first_arg}\n\n"
            "相手記者の再反論に対して、最後の反論を展開してください。相手の言い分を退け、"
            "いかに【{team_b}】の戦術がこの試合で噛み合うかを決定づけるポイント（戦術的ディテール、交代枠の影響など）を交えて結論づけてください。\n"
            "1段落（200文字〜300文字程度）で述べてください。"
        )
        chain = prompt | llm
        result = chain.invoke(
            {
                "team_a": team_a,
                "team_b": team_b,
                "opponent_arg": opponent_arg,
                "my_first_arg": my_first_arg,
            }
        )

        return {
            "debate_history": debate_history
            + [{"agent": f"{team_b} 担当記者 (最後)", "content": result.content}]
        }
    except Exception as e:
        return {
            "debate_history": debate_history
            + [
                {
                    "agent": f"{team_b} 担当記者 (最後)",
                    "content": f"エラーが発生しました: {e}",
                }
            ]
        }


def debate_synthesizer_node(state: WorldCupState) -> dict:
    """討論の全プロセスと試合環境を読み、中立的なアナリストとして最終判定を下す"""
    team_a = state["team_a"]
    team_b = state["team_b"]
    debate_history = state.get("debate_history", [])
    stadium_name = state.get("stadium_name", "MetLife Stadium")
    stadium_env = state.get("stadium_env", "standard")

    # 討論履歴を一つのテキストにまとめる
    debate_transcript = ""
    for speech in debate_history:
        debate_transcript += f"### {speech['agent']}:\n{speech['content']}\n\n"

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {
            "agent_analysis": "APIキー未設定のため、討論の要約は行われませんでした。",
            "team_a_modifier": 1.0,
            "team_b_modifier": 1.0,
        }

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
        structured_llm = llm.with_structured_output(AgentAnalysisOutput)

        prompt = PromptTemplate.from_template(
            "あなたはFIFA認定の中立的なチーフサッカースタッツアナリストです。\n"
            "まもなく行われる【{team_a}】対【{team_b}】の試合について、両チームの担当記者による激しい討論が行われました。\n\n"
            "開催スタジアム: {stadium_name} (環境特性: {stadium_env})\n\n"
            "以下が討論の書き起こし（トランスクリプト）です：\n"
            "=======\n"
            "{transcript}\n"
            "=======\n\n"
            "あなたの仕事は、この討論の要点、戦術的な対立点、両チームの真の強み・弱みを客観的に整理し、要約解説を作成することです。\n"
            "開催スタジアムの環境（高地、人工芝、酷暑など）が戦術に及ぼす影響にも言及してください。\n"
            "また、その分析結果に基づき、両チームの標準得点力に対する「得点力補正係数 (modifier)」（0.8〜1.2の範囲）を決定してください。\n"
            "- 1.0：戦術やコンディションが通常通り機能する\n"
            "- 1.1〜1.2：相手の弱点や戦術的相性の良さにより得点期待値が高まる（バフ）\n"
            "- 0.8〜0.9：相手の守備の堅さや戦術的相性の悪さにより得点期待値が下がる（デバフ）"
        )

        chain = prompt | structured_llm
        result: AgentAnalysisOutput = chain.invoke(
            {
                "team_a": team_a,
                "team_b": team_b,
                "stadium_name": stadium_name,
                "stadium_env": stadium_env,
                "transcript": debate_transcript,
            }
        )

        return {
            "agent_analysis": result.agent_analysis,
            "team_a_modifier": result.team_a_modifier,
            "team_b_modifier": result.team_b_modifier,
        }
    except Exception as e:
        print(f"Error in debate_synthesizer: {e}")
        return {
            "agent_analysis": f"討論の集約中にエラーが発生しました: {e}",
            "team_a_modifier": 1.0,
            "team_b_modifier": 1.0,
        }


def calc_node(state: WorldCupState) -> dict:
    """定量計算（ポアソン分布）"""
    team_a = state["team_a"]
    team_b = state["team_b"]

    # 1. 選手総市場価値の比率による補正
    mv_ratio = (state["team_a_market_value"] / state["team_b_market_value"]) ** 0.1

    # 2. 戦術相性による補正
    tactics_mod_a, tactics_mod_b = get_tactical_modifier(
        state["team_a_tactics"], state["team_b_tactics"]
    )

    # 3. スタジアム環境による補正
    stadium_env = state.get("stadium_env", "standard")
    stadium_name = state.get("stadium_name", "MetLife Stadium")

    host_country = ""
    if "Azteca" in stadium_name:
        host_country = "Mexico"
    elif "BC Place" in stadium_name:
        host_country = "Canada"
    elif (
        "Hard Rock" in stadium_name
        or "MetLife" in stadium_name
        or "NRG Stadium" in stadium_name
    ):
        host_country = "United States"

    stadium_mod_a = get_stadium_modifier(
        team_a, state["team_a_tactics"], stadium_env, host_country
    )
    stadium_mod_b = get_stadium_modifier(
        team_b, state["team_b_tactics"], stadium_env, host_country
    )

    # 期待得点の最終算出
    expected_goals_a = (
        state["team_a_avg_goals"]
        * state.get("team_a_modifier", 1.0)
        * mv_ratio
        * tactics_mod_a
        * stadium_mod_a
    )
    expected_goals_b = (
        state["team_b_avg_goals"]
        * state.get("team_b_modifier", 1.0)
        / mv_ratio
        * tactics_mod_b
        * stadium_mod_b
    )

    # 4. 休養日数による補正（中何日デバフ）
    rest_days_a = state.get("team_a_rest_days")
    rest_days_b = state.get("team_b_rest_days")
    if rest_days_a is not None and rest_days_b is not None:
        if rest_days_a < rest_days_b:
            expected_goals_a *= 0.95
        elif rest_days_b < rest_days_a:
            expected_goals_b *= 0.95

    max_goals = 10
    prob_a_win = 0.0
    prob_b_win = 0.0
    prob_draw = 0.0

    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            prob = stats.poisson.pmf(i, expected_goals_a) * stats.poisson.pmf(
                j, expected_goals_b
            )
            if i > j:
                prob_a_win += prob
            elif i < j:
                prob_b_win += prob
            else:
                prob_draw += prob

    total = prob_a_win + prob_b_win + prob_draw

    return {
        "prob_team_a_win": prob_a_win / total,
        "prob_team_b_win": prob_b_win / total,
        "prob_draw": prob_draw / total,
        "expected_goals_a": expected_goals_a,
        "expected_goals_b": expected_goals_b,
    }


def summary_node(state: WorldCupState) -> dict:
    """サマリーテキストの生成"""
    team_a = state["team_a"]
    team_b = state["team_b"]

    summary = "### 📊 最終勝敗予想結果\n\n"
    summary += "| チーム | 勝利確率 | 期待得点（補正後） | 戦術スタイル | 市場価値 |\n"
    summary += "| :--- | :---: | :---: | :---: | :---: |\n"
    summary += f"| **{team_a}** | **{state['prob_team_a_win']:.1%}** | {state['expected_goals_a']:.2f} 点 | {state['team_a_tactics'].capitalize()} | {state['team_a_market_value']:.0f}M€ |\n"
    summary += f"| **{team_b}** | **{state['prob_team_b_win']:.1%}** | {state['expected_goals_b']:.2f} 点 | {state['team_b_tactics'].capitalize()} | {state['team_b_market_value']:.0f}M€ |\n"
    summary += f"| **引き分け** | **{state['prob_draw']:.1%}** | - | - | - |\n\n"

    # PK戦期待値の計算と追加
    pk_a = state.get("team_a_pk_rating", 3)
    pk_b = state.get("team_b_pk_rating", 3)
    p_pk_a = 0.5 + 0.05 * (pk_a - pk_b)
    p_pk_a = max(0.1, min(0.9, p_pk_a))
    p_pk_b = 1.0 - p_pk_a
    summary += f"ℹ️ **PK戦期待値 (ノックアウト想定)**: 引き分け時の勝率: **{team_a}** {p_pk_a:.0%} (PKレート: {pk_a}) vs **{team_b}** {p_pk_b:.0%} (PKレート: {pk_b})\n\n"

    summary += f"🏟️ **開催地**: {state.get('stadium_name', 'MetLife Stadium')} (環境特性: {state.get('stadium_env', 'standard').capitalize()})\n\n"
    summary += f"### 🧠 アナリスト総合戦術分析\n{state['agent_analysis']}"

    return {"final_summary": summary}


def create_graph() -> StateGraph:
    workflow = StateGraph(WorldCupState)

    # 討論ノードの追加
    workflow.add_node("Debate_Agent_A", debate_agent_a_node)
    workflow.add_node("Debate_Agent_B", debate_agent_b_node)
    workflow.add_node("Debate_Rebuttal_A", debate_rebuttal_a_node)
    workflow.add_node("Debate_Rebuttal_B", debate_rebuttal_b_node)
    workflow.add_node("Debate_Synthesizer", debate_synthesizer_node)
    workflow.add_node("Calc_Node", calc_node)
    workflow.add_node("Summary_Node", summary_node)

    # エッジの接続
    workflow.set_entry_point("Debate_Agent_A")
    workflow.add_edge("Debate_Agent_A", "Debate_Agent_B")
    workflow.add_edge("Debate_Agent_B", "Debate_Rebuttal_A")
    workflow.add_edge("Debate_Rebuttal_A", "Debate_Rebuttal_B")
    workflow.add_edge("Debate_Rebuttal_B", "Debate_Synthesizer")
    workflow.add_edge("Debate_Synthesizer", "Calc_Node")
    workflow.add_edge("Calc_Node", "Summary_Node")
    workflow.add_edge("Summary_Node", END)

    return workflow.compile()


# ==========================================
# 2026年大会 モンテカルロ・シミュレーションロジック
# ==========================================


def get_group_stadium_info(group_name: str) -> tuple:
    """
    グループ別に開催スタジアムを地域分散（2026年大会仕様）させる
    """
    if group_name in ["A", "E", "I"]:
        return "Estadio Azteca (Mexico City)", "altitude", "Mexico"
    elif group_name in ["B", "F", "J"]:
        return "BC Place (Vancouver)", "turf", "Canada"
    elif group_name in ["C", "G", "K"]:
        return "Hard Rock Stadium (Miami)", "heat", "United States"
    elif group_name in ["D", "L"]:
        return "MetLife Stadium (New York/New Jersey)", "standard", "United States"
    else:  # Group H
        return "NRG Stadium (Houston)", "standard", "United States"


def get_random_stadium_info() -> tuple:
    stadiums = [
        ("Estadio Azteca (Mexico City)", "altitude", "Mexico"),
        ("BC Place (Vancouver)", "turf", "Canada"),
        ("Hard Rock Stadium (Miami)", "heat", "United States"),
        ("MetLife Stadium (New York/New Jersey)", "standard", "United States"),
        ("NRG Stadium (Houston)", "standard", "United States"),
    ]
    return random.choice(stadiums)


def simulate_match(
    team_a: dict,
    team_b: dict,
    is_knockout: bool = False,
    stadium_env: str = "standard",
    host_country: str = "",
    rest_days_a: int = None,
    rest_days_b: int = None,
) -> tuple:
    """
    2チーム間の試合をシミュレートする（統計モデル）。
    返り値: (score_a, score_b, winner)
    """
    elo_a = team_a["base_elo"]
    elo_b = team_b["base_elo"]
    mv_a = team_a.get("market_value", 50.0)
    mv_b = team_b.get("market_value", 50.0)
    style_a = team_a.get("tactics_style", "balanced")
    style_b = team_b.get("tactics_style", "balanced")

    diff = elo_a - elo_b
    mv_ratio = (mv_a / mv_b) ** 0.1

    # 1. 戦術相性
    tactics_mod_a, tactics_mod_b = get_tactical_modifier(style_a, style_b)

    # 2. スタジアム環境
    stadium_mod_a = get_stadium_modifier(
        team_a["name"], style_a, stadium_env, host_country
    )
    stadium_mod_b = get_stadium_modifier(
        team_b["name"], style_b, stadium_env, host_country
    )

    # Elo差(1.08倍スケールに変更して安定化)と市場価値比、戦術、スタジアムによる得点力の補正
    expected_goals_a = max(
        0.1,
        team_a["avg_goals"]
        * (1.08 ** (diff / 100))
        * mv_ratio
        * tactics_mod_a
        * stadium_mod_a,
    )
    expected_goals_b = max(
        0.1,
        team_b["avg_goals"]
        * (1.08 ** (-diff / 100))
        / mv_ratio
        * tactics_mod_b
        * stadium_mod_b,
    )

    # 3. 休養日数による補正（中何日デバフ）
    if rest_days_a is not None and rest_days_b is not None:
        if rest_days_a < rest_days_b:
            expected_goals_a *= 0.95
        elif rest_days_b < rest_days_a:
            expected_goals_b *= 0.95

    score_a = np.random.poisson(expected_goals_a)
    score_b = np.random.poisson(expected_goals_b)

    if score_a > score_b:
        return score_a, score_b, team_a["name"]
    elif score_a < score_b:
        return score_a, score_b, team_b["name"]
    else:
        # 引き分け
        if is_knockout:
            pk_a = team_a.get("pk_rating", 3)
            pk_b = team_b.get("pk_rating", 3)
            p_a = 0.5 + 0.05 * (pk_a - pk_b)
            p_a = max(0.1, min(0.9, p_a))  # 安全のための範囲制限
            winner = team_a["name"] if random.random() < p_a else team_b["name"]
            return score_a, score_b, winner
        return score_a, score_b, None


def simulate_group_stage(teams: list, last_match_days: dict) -> dict:
    """
    全12グループ(A-L)のグループステージをシミュレートし、勝ち上がり32チームを決定する。
    """
    groups = {}
    for team in teams:
        g = team["group_name"]
        if g not in groups:
            groups[g] = []
        groups[g].append(team)

    qualified_1st_2nd = []  # 各組上位2チーム
    third_place_teams = []  # 3位チームのプール

    for g_name, g_teams in groups.items():
        stadium_name, stadium_env, host_country = get_group_stadium_info(g_name)

        standings = {
            t["name"]: {"team": t, "points": 0, "gd": 0, "gf": 0} for t in g_teams
        }
        group_matches = []

        # 総当たり戦 (6試合を3つの節に分けて日程に沿ってシミュレート)
        t0, t1, t2, t3 = g_teams[0], g_teams[1], g_teams[2], g_teams[3]
        g_index = ord(g_name) - ord("A")
        base_day = (g_index // 2) * 1 + 1

        # 3節分のマッチアップと試合日
        fixtures = [
            # 第1節
            (t0, t1, base_day),
            (t2, t3, base_day),
            # 第2節
            (t0, t2, base_day + 4),
            (t1, t3, base_day + 4),
            # 第3節
            (t0, t3, base_day + 8),
            (t1, t2, base_day + 8),
        ]

        for t_a, t_b, match_day in fixtures:
            # 前回の試合日からの休養日数を算出
            rest_a = (
                match_day - last_match_days[t_a["name"]] - 1
                if last_match_days[t_a["name"]] is not None
                else None
            )
            rest_b = (
                match_day - last_match_days[t_b["name"]] - 1
                if last_match_days[t_b["name"]] is not None
                else None
            )

            goals_a, goals_b, winner = simulate_match(
                t_a,
                t_b,
                is_knockout=False,
                stadium_env=stadium_env,
                host_country=host_country,
                rest_days_a=rest_a,
                rest_days_b=rest_b,
            )

            # last_match_dayを更新
            last_match_days[t_a["name"]] = match_day
            last_match_days[t_b["name"]] = match_day

            group_matches.append(
                {
                    "home": t_a["name"],
                    "away": t_b["name"],
                    "home_goals": goals_a,
                    "away_goals": goals_b,
                }
            )

            standings[t_a["name"]]["gd"] += goals_a - goals_b
            standings[t_b["name"]]["gd"] += goals_b - goals_a
            standings[t_a["name"]]["gf"] += goals_a
            standings[t_b["name"]]["gf"] += goals_b

            if winner == t_a["name"]:
                standings[t_a["name"]]["points"] += 3
            elif winner == t_b["name"]:
                standings[t_b["name"]]["points"] += 3
            else:
                standings[t_a["name"]]["points"] += 1
                standings[t_b["name"]]["points"] += 1

        # 1次ソート: (勝ち点, 得失点差, 総得点) で仮ソート
        pre_sorted = sorted(
            standings.values(),
            key=lambda x: (x["points"], x["gd"], x["gf"], random.random()),
            reverse=True,
        )

        # 2次ソート: FIFA公式タイブレークの適用 (H2H判定)
        final_sorted = []
        i = 0
        while i < 4:
            tied_subset = [pre_sorted[i]]
            j = i + 1
            while (
                j < 4
                and pre_sorted[j]["points"] == pre_sorted[i]["points"]
                and pre_sorted[j]["gd"] == pre_sorted[i]["gd"]
                and pre_sorted[j]["gf"] == pre_sorted[i]["gf"]
            ):
                tied_subset.append(pre_sorted[j])
                j += 1

            if len(tied_subset) == 2:
                # 2チームが完全に同一成績: 直接対決をチェック
                t1 = tied_subset[0]["team"]["name"]
                t2 = tied_subset[1]["team"]["name"]
                h2h_match = next(
                    (
                        m
                        for m in group_matches
                        if (m["home"] == t1 and m["away"] == t2)
                        or (m["home"] == t2 and m["away"] == t1)
                    ),
                    None,
                )
                if h2h_match:
                    goals_1 = (
                        h2h_match["home_goals"]
                        if h2h_match["home"] == t1
                        else h2h_match["away_goals"]
                    )
                    goals_2 = (
                        h2h_match["away_goals"]
                        if h2h_match["home"] == t1
                        else h2h_match["home_goals"]
                    )
                    if goals_1 < goals_2:
                        tied_subset = [tied_subset[1], tied_subset[0]]

            elif len(tied_subset) == 3:
                # 3チームが完全に同一成績: 3チーム間だけの対戦成績(ミニテーブル)を作成
                mini_names = {x["team"]["name"] for x in tied_subset}
                mini_standings = {
                    name: {"team_name": name, "points": 0, "gd": 0, "gf": 0}
                    for name in mini_names
                }

                for m in group_matches:
                    if m["home"] in mini_names and m["away"] in mini_names:
                        h = m["home"]
                        a = m["away"]
                        hg = m["home_goals"]
                        ag = m["away_goals"]
                        mini_standings[h]["gd"] += hg - ag
                        mini_standings[a]["gd"] += ag - hg
                        mini_standings[h]["gf"] += hg
                        mini_standings[a]["gf"] += ag
                        if hg > ag:
                            mini_standings[h]["points"] += 3
                        elif hg < ag:
                            mini_standings[a]["points"] += 3
                        else:
                            mini_standings[h]["points"] += 1
                            mini_standings[a]["points"] += 1

                # ミニテーブルの結果でソート
                mini_sorted = sorted(
                    mini_standings.values(),
                    key=lambda x: (x["points"], x["gd"], x["gf"], random.random()),
                    reverse=True,
                )

                # ミニテーブルの順位通りにtied_subsetを並び替え
                name_to_standing = {x["team"]["name"]: x for x in tied_subset}
                tied_subset = [name_to_standing[m["team_name"]] for m in mini_sorted]

            final_sorted.extend(tied_subset)
            i = j

        qualified_1st_2nd.append(final_sorted[0]["team"])
        qualified_1st_2nd.append(final_sorted[1]["team"])

        third_place = final_sorted[2]
        third_place_teams.append(
            {
                "team": third_place["team"],
                "points": third_place["points"],
                "gd": third_place["gd"],
                "gf": third_place["gf"],
            }
        )

    # 3位チームのうち上位8チームを決定
    sorted_thirds = sorted(
        third_place_teams,
        key=lambda x: (x["points"], x["gd"], x["gf"], random.random()),
        reverse=True,
    )

    qualified_thirds = [x["team"] for x in sorted_thirds[:8]]
    all_qualified = qualified_1st_2nd + qualified_thirds
    return {
        "all_qualified": all_qualified,
        "group_winners": qualified_1st_2nd[::2],
        "group_runners": qualified_1st_2nd[1::2],
        "best_thirds": qualified_thirds,
    }


def simulate_tournament_monte_carlo(teams: list, num_simulations: int = 1000) -> dict:
    """
    トーナメント全体をモンテカルロ法でシミュレートする（ラウンド32から直接シミュレート）。
    """

    def find_team(name: str) -> dict:
        t = next((x for x in teams if x["name"] == name), None)
        if t is not None:
            return t
        # フォールバック
        return {
            "name": name,
            "base_elo": 1700.0,
            "avg_goals": 1.3,
            "group_name": "-",
            "market_value": 100.0,
            "tactics_style": "balanced",
            "pk_rating": 3,
        }

    r32_pairings = [
        ("South Africa", "Canada"),  # Match 73
        ("Germany", "Paraguay"),  # Match 74
        ("Netherlands", "Morocco"),  # Match 75
        ("Brazil", "Japan"),  # Match 76
        ("France", "Sweden"),  # Match 77
        ("Côte d'Ivoire", "Norway"),  # Match 78
        ("Mexico", "Ecuador"),  # Match 79
        ("England", "DR Congo"),  # Match 80
        ("United States", "Bosnia and Herzegovina"),  # Match 81
        ("Belgium", "Senegal"),  # Match 82
        ("Portugal", "Croatia"),  # Match 83
        ("Spain", "Austria"),  # Match 84
        ("Switzerland", "Algeria"),  # Match 85
        ("Argentina", "Cabo Verde"),  # Match 86
        ("Colombia", "Ghana"),  # Match 87
        ("Australia", "Egypt"),  # Match 88
    ]

    stats_data = {
        t["name"]: {"r32": 0, "r16": 0, "qf": 0, "sf": 0, "final": 0, "winner": 0}
        for t in teams
    }

    for _ in range(num_simulations):
        last_match_days = {t["name"]: None for t in teams}
        winners = {}  # match_number -> team dict

        # 1. ラウンド32
        for idx, (name_a, name_b) in enumerate(r32_pairings):
            match_num = 73 + idx
            t_a = find_team(name_a)
            t_b = find_team(name_b)

            # 全員R32には進出している
            stats_data[t_a["name"]]["r32"] += 1
            stats_data[t_b["name"]]["r32"] += 1

            # 日程と休養日数
            match_day = 16 + (idx // 4)
            rest_a = (
                match_day - last_match_days[t_a["name"]] - 1
                if last_match_days[t_a["name"]] is not None
                else None
            )
            rest_b = (
                match_day - last_match_days[t_b["name"]] - 1
                if last_match_days[t_b["name"]] is not None
                else None
            )

            stadium_name, env, host = get_random_stadium_info()
            _, _, w_name = simulate_match(
                t_a,
                t_b,
                is_knockout=True,
                stadium_env=env,
                host_country=host,
                rest_days_a=rest_a,
                rest_days_b=rest_b,
            )
            winner_team = t_a if w_name == t_a["name"] else t_b
            winners[match_num] = winner_team
            last_match_days[winner_team["name"]] = match_day

        # 2. ラウンド16 (Matches 89〜96)
        r16_matchups = [
            (89, 73, 75, 21),
            (90, 74, 77, 21),
            (91, 76, 78, 22),
            (92, 79, 80, 22),
            (93, 83, 84, 23),
            (94, 81, 82, 23),
            (95, 86, 88, 23),
            (96, 85, 87, 23),
        ]

        for r16_num, m_a, m_b, match_day in r16_matchups:
            t_a = winners[m_a]
            t_b = winners[m_b]

            stats_data[t_a["name"]]["r16"] += 1
            stats_data[t_b["name"]]["r16"] += 1

            rest_a = (
                match_day - last_match_days[t_a["name"]] - 1
                if last_match_days[t_a["name"]] is not None
                else None
            )
            rest_b = (
                match_day - last_match_days[t_b["name"]] - 1
                if last_match_days[t_b["name"]] is not None
                else None
            )

            stadium_name, env, host = get_random_stadium_info()
            _, _, w_name = simulate_match(
                t_a,
                t_b,
                is_knockout=True,
                stadium_env=env,
                host_country=host,
                rest_days_a=rest_a,
                rest_days_b=rest_b,
            )
            winner_team = t_a if w_name == t_a["name"] else t_b
            winners[r16_num] = winner_team
            last_match_days[winner_team["name"]] = match_day

        # 3. 準々決勝 (Matches 97〜100)
        qf_matchups = [
            (97, 89, 90, 25),
            (98, 93, 94, 25),
            (99, 91, 92, 26),
            (100, 95, 96, 26),
        ]

        for qf_num, m_a, m_b, match_day in qf_matchups:
            t_a = winners[m_a]
            t_b = winners[m_b]

            stats_data[t_a["name"]]["qf"] += 1
            stats_data[t_b["name"]]["qf"] += 1

            rest_a = (
                match_day - last_match_days[t_a["name"]] - 1
                if last_match_days[t_a["name"]] is not None
                else None
            )
            rest_b = (
                match_day - last_match_days[t_b["name"]] - 1
                if last_match_days[t_b["name"]] is not None
                else None
            )

            stadium_name, env, host = get_random_stadium_info()
            _, _, w_name = simulate_match(
                t_a,
                t_b,
                is_knockout=True,
                stadium_env=env,
                host_country=host,
                rest_days_a=rest_a,
                rest_days_b=rest_b,
            )
            winner_team = t_a if w_name == t_a["name"] else t_b
            winners[qf_num] = winner_team
            last_match_days[winner_team["name"]] = match_day

        # 4. 準決勝 (Matches 101〜102)
        sf_matchups = [(101, 97, 98, 28), (102, 99, 100, 29)]

        for sf_num, m_a, m_b, match_day in sf_matchups:
            t_a = winners[m_a]
            t_b = winners[m_b]

            stats_data[t_a["name"]]["sf"] += 1
            stats_data[t_b["name"]]["sf"] += 1

            rest_a = (
                match_day - last_match_days[t_a["name"]] - 1
                if last_match_days[t_a["name"]] is not None
                else None
            )
            rest_b = (
                match_day - last_match_days[t_b["name"]] - 1
                if last_match_days[t_b["name"]] is not None
                else None
            )

            stadium_name, env, host = get_random_stadium_info()
            _, _, w_name = simulate_match(
                t_a,
                t_b,
                is_knockout=True,
                stadium_env=env,
                host_country=host,
                rest_days_a=rest_a,
                rest_days_b=rest_b,
            )
            winner_team = t_a if w_name == t_a["name"] else t_b
            winners[sf_num] = winner_team
            last_match_days[winner_team["name"]] = match_day

        # 5. 決勝 (Match 103)
        t_a = winners[101]
        t_b = winners[102]
        match_day = 32

        stats_data[t_a["name"]]["final"] += 1
        stats_data[t_b["name"]]["final"] += 1

        rest_a = (
            match_day - last_match_days[t_a["name"]] - 1
            if last_match_days[t_a["name"]] is not None
            else None
        )
        rest_b = (
            match_day - last_match_days[t_b["name"]] - 1
            if last_match_days[t_b["name"]] is not None
            else None
        )

        stadium_name, env, host = get_random_stadium_info()
        _, _, w_name = simulate_match(
            t_a,
            t_b,
            is_knockout=True,
            stadium_env=env,
            host_country=host,
            rest_days_a=rest_a,
            rest_days_b=rest_b,
        )
        winner_team = t_a if w_name == t_a["name"] else t_b
        stats_data[winner_team["name"]]["winner"] += 1

    prob_results = {}
    for name, counts in stats_data.items():
        prob_results[name] = {
            stage: count / num_simulations for stage, count in counts.items()
        }

    return prob_results
