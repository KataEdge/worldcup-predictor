---
name: configure_langsmith
description: Configure and enable LangSmith tracing to monitor, trace, and evaluate LangGraph node logic and LLM outputs.
---

# Skill: Configure and Use LangSmith Tracing

Use this skill when you want to enable observability, tracing, and debugging for the LangGraph tournament predictors and reporter debate nodes.

## Tracing Setup

1. **LangSmith APIキーの取得方法**:
   - [LangSmith](https://smith.langchain.com/) にアクセスし、ログインまたは無料アカウントを作成します。
   - 画面左下の設定アイコン（歯車マーク）をクリックします。
   - 「API Keys」セクションから、**Create API Key** ボタンをクリックして新しいキーを生成します。
   - 生成されたキー（通常 `lsv2_...` で始まる文字列）をコピーします。
2. プロジェクトのルートにある `.env` ファイルを開きます。
3. 以下の変数を編集してトレーシングを有効化します：
   - `LANGCHAIN_TRACING_V2=true` に設定
   - コピーしたキーを貼り付け：`LANGCHAIN_API_KEY="lsv2_pt_..."`
4. これで LangChain/LangGraph が実行トレースを自動キャプチャするようになります。

## Viewing Traces

Once tracing is enabled, all runs are logged to your LangSmith project Dashboard:
- **Project URL**: `https://smith.langchain.com/projects`
- Look for the project name configured in `LANGCHAIN_PROJECT` (default: `worldcup-predictor`).
- Inside the project, you will see a detailed visual trace diagram showing the state passing between nodes (`Debate_Agent_A` ➔ `Debate_Agent_B` ➔ `Debate_Rebuttal_A` ➔ `Debate_Rebuttal_B` ➔ `Debate_Synthesizer` ➔ `Calc_Node` ➔ `Summary_Node`).
- Clicking on each node will show:
  - Input state dictionary (ELO values, tactical settings, H2H statistics).
  - Outgoing LLM prompt strings and system messages.
  - LLM raw response outputs (including token counts and response latency).
  - Calculated output state dictionary.

## Evaluating Prompts

When you want to evaluate changes to debate prompts or tactical summaries:
1. Create a Dataset in LangSmith using past match predictions.
2. Write evaluation asserts using `pytest` to compare expected score outcomes or verify semantic completeness of summaries.
