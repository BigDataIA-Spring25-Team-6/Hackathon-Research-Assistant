import os
import json
import re
import pandas as pd
from openai import OpenAI
from e2b_code_interpreter import Sandbox
from dotenv import load_dotenv
from utils.snowflake_connector import get_snowflake_connection

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TABLE_NAME = "ON_SITE_SEARCH"

def extract_json_block(text: str) -> str:
    """
    Extract the first JSON object from a markdown code block or fallback to first JSON object.
    """
    print("\n[DEBUG] Raw GPT Output:\n", text)

    # Proper raw string pattern — note the r prefix
    match = re.search(r"```json\s*({.*?})\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback: match any top-level {...}
    match = re.search(r"({.*})", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    raise ValueError("No valid JSON object found in the response.")


def generate_sql(query: str, platform: str, date_start: str = None, date_end: str = None) -> dict:
    system_prompt = f"""
You are a Snowflake SQL expert.
Generate a SQL query that can be run on the table `{TABLE_NAME}`.
Only use these columns: DATE, OSS_KEYWORD, SITE_RULE, CALIBRATED_VISITS, CALIBRATED_USERS, COUNTRY.

ALWAYS filter to:
- COUNTRY = 840
- SITE_RULE ILIKE '%{platform}%'
- DATE between '{date_start}' and '{date_end}'

Return raw JSON with:
- "sql": SQL query
- "explanation": explanation of the query
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0
    )
    content = response.choices[0].message.content.strip()
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

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt}
        ],
        temperature=0
    )

    code_block = response.choices[0].message.content.strip()

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