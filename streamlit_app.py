import streamlit as st
import sqlite3
import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

# --- Configuration and Initialization ---
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Clinical Data Chatbot",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Clinical Data AI Assistant")

DATABASE_PATH = 'c:/Mohan_AI/samplerepo/Chatbot/clinical_data.db'

# --- AI Model and Database Setup ---
@st.cache_resource
def get_model():
    """Initializes and returns the Gemini AI model."""
    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Could not configure Gemini. Check GEMINI_API_KEY. Details: {e}")
        return None

model = get_model()

def get_db_connection():
    """Connects to the persistent file-based database."""
    if not os.path.exists(DATABASE_PATH):
        st.error(f"Database file not found at {DATABASE_PATH}. Please run `Get-Content schema.sql | sqlite3 clinical_data.db`")
        return None
    try:
        return sqlite3.connect(DATABASE_PATH)
    except sqlite3.Error as e:
        st.error(f"Database connection error: {e}")
        return None

# --- LLM Helper Functions ---
def get_sql_from_llm(user_question: str, schema: str) -> str:
    """Generates a SQL query from a user question using the LLM."""
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
    - You MUST use the table aliases `dm` for the demography table, `ae` for the adverse events table, and `vs` for the vitals table.

    User Question: "{user_question}"
    SQL Query:
    """
    response = model.generate_content(prompt)
    return response.text.strip().replace("`", "").replace("sql", "")

def format_response_naturally(question: str, results: list, column_names: list) -> str:
    """Uses the LLM to convert raw database results into a natural language response."""
    if not results:
        return "I found no results for your query."

    data_string = ", ".join(column_names) + "\n" + "\n".join([", ".join(map(str, row)) for row in results])
    prompt = f"""
    You are a helpful chatbot assistant. Your task is to answer the user's question based on the data provided.
    Formulate a friendly, conversational, and natural language response. Do not just repeat the data in a table.

    User's Original Question: "{question}"
    Data from Database:
    ---
    {data_string}
    ---
    Your friendly response:
    """
    response = model.generate_content(prompt)
    return response.text.strip()

# --- Main Chat Interface Logic ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am an AI clinical data assistant. How can I help you?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about the clinical data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            db_connection = get_db_connection()
            if not db_connection or not model:
                st.error("Cannot proceed due to connection or model initialization errors.")
            else:
                try:
                    cursor = db_connection.cursor()
                    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
                    schema = "\n".join([row[0] for row in cursor.fetchall()])

                    sql_query = get_sql_from_llm(prompt, schema)
                    
                    if "NOT_A_QUERY" in sql_query:
                        response = model.generate_content(f"You are a helpful chatbot. The user said: '{prompt}'. Respond conversationally.")
                        response_text = response.text
                    else:
                        st.code(sql_query, language="sql") # Display the generated SQL
                        cursor.execute(sql_query)
                        results = cursor.fetchall()
                        column_names = [desc[0] for desc in cursor.description] if cursor.description else []
                        response_text = format_response_naturally(prompt, results, column_names)

                except Exception as e:
                    response_text = f"An error occurred: {e}"
                finally:
                    if db_connection:
                        db_connection.close()
            
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})