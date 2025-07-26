import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

# Define OpenRouter endpoint and headers
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Function to generate T-SQL from instructions
def generate_tsql(column_name, rule):
    prompt = (
        f"Write a T-SQL expression to transform the column '{column_name}' according to this rule: {rule}. "
        "Only provide the code snippet, not explanations."
    )

    body = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are an expert data engineer who writes clean and optimized T-SQL code."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(API_URL, headers=HEADERS, json=body)
    response.raise_for_status()
    result = response.json()

    return result["choices"][0]["message"]["content"].strip()

# Load your Excel spec sheet
df = pd.read_excel("spec_sheet.xlsx")

# Generate T-SQL statements
tsql_lines = []
for index, row in df.iterrows():
    column = row["Column Name"]
    rule = row["Transformation Rule"]
    tsql = generate_tsql(column, rule)
    tsql_lines.append(f"-- Transformation for: {column}\n{tsql};\n")

# Write to a .sql file
with open("output_generated.sql", "w", encoding="utf-8") as file:
    file.write("\n".join(tsql_lines))

print("✅ T-SQL generation complete! Output saved to 'output_generated.sql'.")
