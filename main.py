import os
import requests
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pyodbc

# Load environment variables
load_dotenv()
#API_KEY = os.getenv("OPENROUTER_API_KEY")

# Define connection parameters
server = os.getenv('server')  # e.g., 'localhost\\SQLEXPRESS' or '192.168.1.100'
database = os.getenv('database')
username = os.getenv('username')   # if using SQL Authentication
password = os.getenv('password')   # if using SQL Authentication
# If using Windows Authentication, set trusted_connection='yes'

# SQL Server Authentication
conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
)

try:
    # Connect to the database
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    print("Connection successful.")

    '''# Test query: fetch first 5 customers
    cursor.execute("SELECT TOP 5 * FROM dbo.customers")
    for row in cursor.fetchall():
        print(row)

    conn.close()'''

except Exception as e:
    print("Error connecting to database:", e)

import pandas as pd
import openai

# --- CONFIGURATION ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
EXCEL_FILE = "spec_sheet.xlsx"  # Path to your file
MODEL = "openai/gpt-3.5-turbo"  # or try "gpt-4", "claude-3-opus", etc.

#openai.api_key = OPENROUTER_API_KEY
#openai.api_base = "https://openrouter.ai/api/v1"

# --- READ ETL SPEC ---
df = pd.read_excel(EXCEL_FILE)

# --- GROUP BY TABLE ---
grouped = df.groupby("Table Name")

# Define OpenRouter endpoint and headers
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# --- FUNCTION TO GENERATE SQL FOR ONE TABLE ---
def generate_sql_for_table(table_name, table_df):
    schema = table_df["Schema"].iloc[0]
    
    instructions = f"""You are a T-SQL expert.
Based on the following ETL specification, generate a T-SQL script to create a new table named [{schema}].[{table_name}].
The table should contain the columns listed, and you should infer reasonable data types based on the transformation logic.

Use SQL Server syntax and include primary keys if applicable.

Here is the column specification:\n\n"""

    for _, row in table_df.iterrows():
        instructions += f"- Column: {row['Column Name']}\n  Logic: {row['Transformation Rule']}\n\n"

    instructions += f"Generate the T-SQL script, along with the necessary transformations for each column based on Logic: {row['Transformation Rule']}"

    body = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are an expert data engineer who writes clean and optimized T-SQL code."},
            {"role": "user", "content": instructions}
        ]
    }
    # Call OpenRouter API
    response = requests.post(API_URL, headers=HEADERS, json=body)
    response.raise_for_status()
    result = response.json()
    return result['choices'][0]['message']['content']

# --- GENERATE SQL FOR EACH TABLE ---
tsql_lines = []
for table_name, table_df in grouped:
    print(f"\n--- T-SQL for {table_name} ---")
    tsql = generate_sql_for_table(table_name, table_df)
    tsql_lines.append(f"-- Transformation for: {table_name}\n{tsql};\n")
    print(tsql)
# Write to a .sql file
with open("output_generated.sql", "w", encoding="utf-8") as file:
    file.write("\n".join(tsql_lines))
    
# Close the database connection
conn.close()