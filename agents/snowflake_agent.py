import os
import json
import re
import pandas as pd
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from e2b_code_interpreter import Sandbox
from dotenv import load_dotenv
from utils.snowflake_connector import get_snowflake_connection

load_dotenv()

llm = ChatOllama(model="llama3", temperature=0)
TABLE_NAME = "ON_SITE_SEARCH"

def extract_json_block(text: str) -> str:
    """
    Try to extract a JSON object from the response, even if malformed.
    """
    print("\n[DEBUG] Raw GPT Output:\n", text)

    # Try direct parse
    try:
        return json.dumps(json.loads(text.strip()))
    except Exception as e:
        print("[DEBUG] Direct JSON parsing failed:", e)

    # Try code block
    match = re.search(r"```json\s*({.*?})\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Try fallback {...}
    match = re.search(r"({.*})", text, re.DOTALL)
    if match:
        try:
            return json.dumps(json.loads(match.group(1).strip()))
        except:
            pass

    # Manual patch: append closing brace if missing
    if text.strip().startswith("{") and not text.strip().endswith("}"):
        try:
            patched = text.strip() + "}"
            return json.dumps(json.loads(patched))
        except:
            pass

    raise ValueError("No valid JSON object found in the response.")

def generate_sql(query: str, platform: str, date_start: str = None, date_end: str = None) -> dict:
    system_prompt = f"""
You are a Snowflake SQL expert.

Your task is to ONLY return a JSON object containing two fields:
- "sql": A valid Snowflake SQL query using the `{TABLE_NAME}` table
- "explanation": A concise explanation of the query

Use only the following columns: DATE, OSS_KEYWORD, SITE_RULE, CALIBRATED_VISITS, CALIBRATED_USERS, COUNTRY.

ALWAYS apply these filters in the WHERE clause:
- COUNTRY = 840
- SITE_RULE ILIKE '%{platform}%'
- DATE BETWEEN '{date_start}' AND '{date_end}'

NEVER include explanations outside the JSON. Do not use code blocks or markdown.
Only return raw JSON.
"""
    response = llm.invoke([
    SystemMessage(content=system_prompt),
    HumanMessage(content=query)
    ])
    content = response.content.strip()
    json_text = extract_json_block(content)
    return json.loads(json_text)


def run_e2b_chart_generator(df: pd.DataFrame, query: str) -> str:
    col_names = ", ".join(df.columns)
    csv_data = df.to_csv(index=False)

    prompt = f"""
You are a data visualization expert.
Given the following CSV data from a Snowflake query and a user request:

User Request:
{query}

The DataFrame has the following columns: {col_names}

Generate Python code using matplotlib to create a relevant chart.
Your code must load the data from 'data.csv', Use only columns that exist in the DataFrame. 
Do not invent columns like 'year', 'product', or 'sales' unless they exist, 
create an insightful chart based on the user's request, and save the chart as 'chart.png'.
Ensure the chart has a clear title, axis labels, and tight layout.
Only return the code. Do not include explanations or comments.
"""
    response = llm.invoke([
    SystemMessage(content=prompt),
    HumanMessage(content=query)
])

    code_block = response.content.strip()

    if code_block.startswith("```python"):
        code_block = code_block.replace("```python", "").replace("```", "").strip()

    with Sandbox(api_key=os.getenv("E2B_API_KEY")) as sandbox:
        sandbox.files.write("data.csv", csv_data)

        script = f"""
import pandas as pd
import matplotlib.pyplot as plt
import base64

df = pd.read_csv("data.csv")
print("DataFrame Head:", df.head())

# LLM-Generated Code
{code_block}

print("Top Products Index:", top_products.index.tolist())
print("X Tick Labels:", [label.get_text() for label in plt.gca().get_xticklabels()])

plt.tight_layout()
plt.savefig("chart.png")
with open("chart.png", "rb") as f:
    encoded = base64.b64encode(f.read()).decode()
print(encoded)
"""
        try:
            result = sandbox.run_code(script)
            for line in result.logs.stdout:
                print(line)
        except Exception as e:
            print("Sandbox error:", e)
            return None

    return result.logs.stdout[-1]


def snowflake_tool(query: str, platform: str, date_start: str = None, date_end: str = None) -> dict:
    try:
        print(f"Received query: {query}")
        parsed = generate_sql(query, platform, date_start, date_end)
        sql = parsed.get("sql")
        print(f"Generated SQL: {sql}")
        explanation = parsed.get("explanation")
    except Exception as e:
        return {"error": f"Failed to generate SQL: {e}"}

    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        cursor.close()
        conn.close()
    except Exception as e:
        return {"error": f"Snowflake query failed: {e}", "sql": sql}

    if df.empty:
        return {"summary": "Query executed but returned no data."}

    try:
        chart_base64 = run_e2b_chart_generator(df, query)
    except Exception as e:
        chart_base64 = None

    return {
        "summary": explanation,
        "data_preview": df.head(5).to_dict(orient="records"),
        "chart_base64": chart_base64,
        "sql": sql
    }