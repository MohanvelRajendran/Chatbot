import sqlite3
import os
import sys
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv
from importlib import metadata
from packaging import version

def setup_database(schema_file: str = "schema.sql"):
    """
    Sets up the database and populates it with schema and data.
    This function now reads directly from the schema.sql file.
    """
    con = sqlite3.connect(":memory:") # Use in-memory DB for this script
    print(f"Attempting to read schema from: {os.path.join(os.getcwd(), schema_file)}")
    cur = con.cursor()
    
    try:
        with open(schema_file, 'r') as f:
            # The schema.sql file is now written in native SQLite syntax.
            # We can execute it directly without string replacements.
            sql_script = f.read()
            cur.executescript(sql_script)
    except FileNotFoundError:
        print(f"Error: The schema file '{schema_file}' was not found in the current directory '{os.getcwd()}'.")
        return None
    except sqlite3.Error as e:
        # This is a crucial debugging step. If the script fails, we print the content
        # that caused the failure. This helps diagnose sync issues.
        print("--- ERROR: Database setup failed. ---")
        print(f"An SQLite error occurred: {e}")
        print("The script that caused the error is printed below:")
        print("-------------------------------------------------")
        print(sql_script)
        print("-------------------------------------------------")
        return None

    con.commit()
    return con

def _format_response_naturally(model, question: str, results: list, column_names: list, chat_history: list) -> str:
    """
    Uses the LLM to convert raw database results into a natural language response.
    """
    # If there's only one result with one column, we can often just return it.
    if len(results) == 1 and len(column_names) == 1:
        return f"The answer is: {results[0][0]}"

    # Format the results into a string that the LLM can easily parse.
    data_string = ", ".join(column_names) + "\n"
    for row in results:
        data_string += ", ".join(map(str, row)) + "\n"

    history_str = "\n".join([f"{msg['role']}: {msg['parts'][0]}" for msg in chat_history])

    prompt = f"""
You are a helpful chatbot assistant. Your task is to answer the user's question based on the data provided.
Formulate a friendly, conversational, and natural language response. Do not just repeat the data in a table.

Conversation History:
---
{history_str}
---

User's Original Question: "{question}"

Data from Database:
---
{data_string}
---

Your friendly response:
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def _get_sql_from_llm(model, user_question: str, schema: str, chat_history: list) -> str:
    """Generates a SQL query from a user question using the LLM."""
    history_str = "\n".join([f"{msg['role']}: {msg['parts'][0]}" for msg in chat_history])
    prompt = f"""
You are a Text-to-SQL expert. Your task is to convert a user's question into a valid SQLite query.
You must only output the SQL query and nothing else. Do not add any explanation or markdown.
If the user's question is not a question that can be answered by querying the database (e.g., "hello", "how are you"),
simply respond with the word "NOT_A_QUERY".

Database Schema:
---
{schema}
---

Important Querying Rules:
- **JOINs**: Your default join MUST be a `LEFT JOIN` from `Demography` to `AdverseEvents`. Only use `INNER JOIN` when the user's question is ONLY about the events themselves (e.g., "count all headaches").
- **ALIASES**: You MUST use `dm` for `Demography` and `ae` for `AdverseEvents`.
- **PERCENTAGE QUERIES**: For questions about the "percentage of subjects with events", you MUST use the following query structure. This is non-negotiable.
  - **Example**: `SELECT CAST(COUNT(DISTINCT ae.patient_id) AS REAL) * 100 / COUNT(DISTINCT dm.patient_id) FROM Demography dm LEFT JOIN AdverseEvents ae ON dm.patient_id = ae.patient_id`

Conversation History (for context on follow-up questions):
---
{history_str}
---

User Question:
---
{user_question}
---

SQL Query:
"""
    response = model.generate_content(prompt)
    # Clean up the response to get a pure SQL query
    sql_query = response.text.strip().replace("`", "").replace("sql", "")
    return sql_query

def query_database(model, user_question: str, db_connection, chat_history: list) -> str:
    """
    Uses an LLM to convert a natural language question into a SQL query,
    executes it, and returns a formatted response.
    """
    cursor = db_connection.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
    schema_statements = [row[0] for row in cursor.fetchall()]
    schema = "\n".join(schema_statements)

    try:
        # 1. Generate SQL from the user's question
        sql_query = _get_sql_from_llm(model, user_question, schema, chat_history)
        if "NOT_A_QUERY" in sql_query:
            return "I can only answer questions related to the clinical database. Please ask me about patients or adverse events."

        print(f"🤖 Generated SQL: {sql_query}") # For debugging

        # 2. Execute the generated SQL.
        cursor.execute(sql_query)
        results = cursor.fetchall()

        if not results:
            return "I found no results for your query."

        # 3. Use the LLM to format the results into a natural response
        column_names = [description[0] for description in cursor.description]
        return _format_response_naturally(model, user_question, results, column_names, chat_history)

    except google_exceptions.NotFound as e:
        error_message = str(e)
        if "v1beta" in error_message:
            return f"API Error: The model was not found. This is caused by an old version of the 'google-generativeai' library. Please ensure your virtual environment is active and you have run 'pip install --upgrade google-generativeai'. Details: {e}"
        else:
            return f"Sorry, it seems the AI model I'm trying to use is not available. Please check the model name. Details: {e}"
    except sqlite3.Error as e:
        return f"I couldn't run the query. The database returned an error: {e}\nFaulty SQL was: {sql_query}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

if __name__ == "__main__":
    # 1. Load environment variables and configure API key
    print("--- Chatbot Initializing ---")    
    print(f"Python Executable: {sys.executable}")

    MIN_GG_VERSION = "0.5.0"
    try:
        gg_version = metadata.version("google-generativeai")
        print(f"Google Generative AI Version: {gg_version}")
        if version.parse(gg_version) < version.parse(MIN_GG_VERSION):
            print(f"\nFATAL ERROR: Your google-generativeai version is {gg_version}, which is too old.")
            print(f"This script requires version {MIN_GG_VERSION} or higher.")
            print("Please ensure your virtual environment is active and run: pip install --upgrade google-generativeai")
            sys.exit(1) # Exit with an error code
    except metadata.PackageNotFoundError:
        print("\nFATAL ERROR: 'google-generativeai' library not found in the current Python environment.")
        print("Please ensure your virtual environment is active and run: pip install -r requirements.txt")
        sys.exit(1)

    load_dotenv()
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY not found. Please create a .env file with your key.")
    else:
        try:
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-2.0-flash')
        except Exception as e:
            print(f"Error: Could not configure Gemini or create the model. Please check your API key. Details: {e}")
            model = None

    # 2. Setup the database connection
    db_conn = setup_database()

    if not (db_conn and model):
        sys.exit("Exiting: Database or AI Model could not be initialized.")

    # 3. Start interactive chat loop
    chat_history = []
    MAX_HISTORY_TURNS = 5 # Keep the last 5 pairs of user/model messages
    print("Chatbot is ready! Ask me anything about the clinical data (or type 'quit' to exit).")
    while True:
        user_question = input("\nUser: ")
        if user_question.lower() in ["quit", "exit"]:
            print("Chatbot: Goodbye!")
            break
        response = query_database(model, user_question, db_conn, chat_history)
        print(f"\nChatbot: {response}")
        chat_history.append({'role': 'user', 'parts': [user_question]})
        chat_history.append({'role': 'model', 'parts': [response]})
        # Trim history to the last N turns
        if len(chat_history) > MAX_HISTORY_TURNS * 2:
            chat_history = chat_history[-MAX_HISTORY_TURNS * 2:]

    # 4. Close the connection
    db_conn.close()