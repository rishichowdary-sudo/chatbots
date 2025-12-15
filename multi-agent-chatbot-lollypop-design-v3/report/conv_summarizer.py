import sqlite3
import pandas as pd
import msgpack
import pprint
from langchain_openai import ChatOpenAI
import os
from datetime import datetime, timedelta
import json
import yaml
import glob
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig, chain
from langchain_community.tools import TavilySearchResults
from flask import jsonify

import sys
sys.path.append(os.getcwd())
import utils.Log_sql as log_sql
import utils.helper as helper

load_dotenv()

class CompanyInformationExtraction:
    """
    Module to extract company information from a given name and email. Uses email ID to extract the company name and then uses Tavily Tool to prepare
    """
    def __init__(self, llm, max_search_result=5, search_depth="basic"):
        self.llm = llm
        self.tool = TavilySearchResults(max_result = max_search_result, search_depth = search_depth, include_answer=True)
        llm_with_tools = self.llm.bind_tools([self.tool])
        self.prompt = ChatPromptTemplate(
                [
                    ("system", """You are an expert pre-Sales officer who is able to evaluate company's value, company's domain and company worth.
                    You will be given name and email of a person from the company.
                    From the email domain, try to identify the company and gather the company's value and worth from Yahoo Finance and Crunchbase website.
                    From the name given, try to identify the person and their position in the company.
                    Dont use fluff words. Dont ask for followups in your reply.
                    If you cannot confidently determine the company or individual's details, state clearly that additional information is needed. Do not make guesses. Dont write explanation. Dont provide links.

                    Provide the following
                    Person Name:
                    Position:
                    Background:

                    Company Name:
                    industry:
                    Worth and value:
                    Revenue:
                    Employees:
                    """),
                    ("human", "{query}"),
                    ("placeholder", "{messages}"),
                ]
            )
        self.llm_chain = self.prompt | llm_with_tools

    def _evaluate_email_for_public_domain(self, email):
        general_domains = {
            "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
            "icloud.com", "aol.com", "live.com", "msn.com",
            "protonmail.com", "mail.com", "yandex.com", "zoho.com"
        }
        domain = email.split("@")[1]
        return True if domain in general_domains else False


    def _extract_company_details(self, name, email):
        @chain
        def tool_chain(user_input: str, config: RunnableConfig):
            input_ = {"query": user_input}
            ai_msg = self.llm_chain.invoke(input_, config=config)
            tool_msgs = self.tool.batch(ai_msg.tool_calls, config=config)
            return self.llm_chain.invoke({**input_, "messages": [ai_msg, *tool_msgs]}, config=config)
        
        answer = tool_chain.invoke(f"Tell me more about from this details, name is {name} and email is {email}")
        return answer.content

    def get_company_info_from_details(self, name, email):
        if self._evaluate_email_for_public_domain(email):
            company_info = "Public domain email ID"
        else:
            company_info = self._extract_company_details(name, email)
        return company_info
    

# gather all thread_ids from the state_db file
def get_thread_id_from_statedb(conn):
    query = "SELECT DISTINCT thread_id FROM checkpoints;"
    thread_id_list  = pd.read_sql_query(query, conn)
    thread_id_list = {thread: 1 for thread in thread_id_list["thread_id"]}
    return thread_id_list

def get_unprocessed_thread_id_from_logdb(log_db_path, client_id):
    # all the unprocessed thread ids are fetched (with summary flag=0).
    # Get today's date
    # today = datetime.now()
    # Calculate yesterday's date
    # yesterday = today - timedelta(days=0)
    # Format yesterday's date as a string (e.g., 'YYYY-MM-DD')
    # yesterday_date = yesterday.strftime('%Y-%m-%d')

    conn = sqlite3.connect(log_db_path)
    cursor = conn.cursor()

    # Execute the query
    cursor.execute("""
        SELECT DISTINCT session_id
        FROM client_sessions
        WHERE summary = 0 AND client_id = ?
    """, (client_id,))

    # Fetch and print results
    session_ids = cursor.fetchall()

    # Close the connection
    conn.close()
    session_ids = [session_id[0] for session_id in session_ids]
    return session_ids

def filter_last_day_thread_id(conn, log_db_path, client_id):
    thread_id_list = get_thread_id_from_statedb(conn)
    last_day_thread_ids  = get_unprocessed_thread_id_from_logdb(log_db_path, client_id)
    filtered_thread_ids = [thread_id for thread_id in last_day_thread_ids if thread_id in thread_id_list]
    return filtered_thread_ids



# checkpoint data is in byte format. Unpacking to python object
def fetch_unpacked_data_from_thread(conn, thread_id):
    query = f"SELECT checkpoint from checkpoints where thread_id = '{thread_id}' ORDER BY checkpoint_id DESC LIMIT 1;"
    checkpoints_df  = pd.read_sql_query(query, conn)
    checkpoint = checkpoints_df["checkpoint"][0]
    unpacked_data = msgpack.unpackb(checkpoint, raw=False)
    return unpacked_data


# Name, email, message extractor. 
# Conversation with name or email or number of messages less than desired is ignored. 
def get_details_from_unpacked_data(unpacked_data, min_message_number=5):
    time_stamp = unpacked_data["ts"] if "ts" in unpacked_data else None
    unpacked_data = unpacked_data["channel_values"]
    if "name" in unpacked_data and "email" in unpacked_data and "messages" in unpacked_data and unpacked_data["name"] is not None and unpacked_data["email"] is not None and len(unpacked_data["messages"]) > min_message_number :
        name = unpacked_data["name"]
        email = unpacked_data["email"]
        messages = unpacked_data["messages"]
        return (True, [name, email, messages, time_stamp])
    else:
        return (False, [])


# extract Human and AI messages from message list. Takes care of duplicate Human message for old state_db
def parse_conversation_from_state_messages(messages):
    user_questions = []
    chatbot_answers = []
    for message in messages:  
        unpacked_messages =  msgpack.unpackb(message.data, raw=False)
        message_type = unpacked_messages[1]
        message_content = unpacked_messages[2]["content"]

        if message_type == "HumanMessage":
            if len(user_questions) < 1 or message_content != user_questions[-1]:
                user_questions.append(message_content)
        elif message_type == "AIMessage" and message_content != "":
              chatbot_answers.append(message_content)
    return user_questions, chatbot_answers


# conversation summarizer
def write_conversation_summary(llm, user_questions, chatbot_answers):
    summarizer_template = """
      You are an experienced customer facing Sales expert. Your task is to list of messages of a conversation and provide a concise summary that captures the main points, themes, and any important details discussed.

      **Instructions:**

      1. **Input Format:** You will receive a list of messages the user asked and a list of messages that were answered by the chatbot.

      2. **Output Requirements:**
        - Provide a clear, concise and short summary of the conversation, 75 words or lesser.
        - Focus more on the converation than on introduction details.
        - Focus more on the user questions.
        - Avoid providing all specifics of chatbot answer. Provide a very concise summary of chatbot part of conversation.
        - Highlight key topics and any conclusions or decisions made.
        - Avoid providing header.
        - **Additionally, classify this conversation into one of the following categories: Project enquiry, Explore, Career.**
        - **Return both summary and category in JSON format with keys 'summary' and 'category'.**

      3. **Considerations:**
        - Pay attention to the tone and context of the messages to accurately reflect the conversation's dynamics.
        - If there are any questions raised or unresolved issues, mention them in the summary.

      Below is the list of messages:
      user_questions: {user_questions} 
      chatbot_answers: {chatbot_answers}

    """
    summary = llm.invoke(summarizer_template.format(user_questions = user_questions, chatbot_answers = chatbot_answers))
    try:
        result = json.loads(summary.content)
        summary_text = result.get("summary", "")
        conversation_category = result.get("category", "Uncategorized")
    except:
        # fallback in case LLM doesn't return valid JSON
        summary_text = summary.content
        conversation_category = "Uncategorized"

    return summary_text, conversation_category


# json file writer
def write_into_json_file(data, file_path):
    with open(file_path, 'a') as json_file:
        # json.dump(data, json_file, indent=4)
        json_file.write(json.dumps(data) + '\n')


# Extract conversation details, summary for each conversation from dsqlite file
def conversation_summary_from_db(llm, db_path, log_db_path):
    """
    Generate conversation details, including name, email, conversation summary of interaction with the chatbot. Extracts from the SQLite database.

    Args:
        llm: language model to process the conversation summary.
        db_path: path to the SQLite database file. 
        log_db_path: path to the log database.
    Returns:
        A dictionary with status, reason, and processed conversations as JSON.
    """

    if not os.path.exists(db_path):
        return {"status": 204, "reason": "db file not found"}

    # Get client_id from the file name
    file_name = os.path.basename(db_path)
    client_id = os.path.splitext(file_name)[0]

    # Initialize a list to store all processed conversations
    conversations = []

    # Get company details
    company_info_extractor = CompanyInformationExtraction(llm, max_search_result=5, search_depth="basic")

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Get unique thread IDs available in the database
            thread_id_list = filter_last_day_thread_id(conn, log_db_path, client_id)

            print(f"Total conversations in the file: {len(thread_id_list)}")
            #print(thread_id_list)

            rejected_chat_count = 0

            conversations = {}  # Use a dictionary instead of a list
            for thread_id in thread_id_list:
                try:
                    # Get Python object from the byte object
                    unpacked_data = fetch_unpacked_data_from_thread(conn, thread_id)

                    # Extract data from the Python object
                    status, extracted_data = get_details_from_unpacked_data(unpacked_data)
                    if status:
                        name, email, messages, time_stamp = extracted_data
                    else:
                        rejected_chat_count += 1
                        continue

                    # Prepare user questions and chatbot answers
                    user_questions, chatbot_answers = parse_conversation_from_state_messages(messages)

                    # Generate a conversation summary using the LLM
                    conversation_summary,conversation_category = write_conversation_summary(llm, user_questions, chatbot_answers)

                    # Evaluate whether the given name and email need to be processed for company details
                    company_information = company_info_extractor.get_company_info_from_details(name, email)

                    # Add the conversation details to the dictionary
                    conversations[thread_id] = {
                        "client_id": client_id,
                        "time_stamp": time_stamp,
                        "name": name,
                        "email": email,
                        "user_questions": user_questions,
                        "chatbot_answers": chatbot_answers,
                        "conversation_summary": conversation_summary,
                        "conversation_category": conversation_category,
                        "company_information": company_information,
                    }
                    log_sql.update_session_summary(thread_id,1)

                except sqlite3.Error as e:
                    return {"status": 500, "reason": "Database connection error"}

    except sqlite3.Error as e:
        print(e)
        print({"status": 500, "reason": "Database connection error"})
        return {"status": 500, "reason": "Database connection error"}

    print(f"Total rejected conversations: {rejected_chat_count}")

    # Return all processed conversations as a JSON object
    return conversations, len(thread_id_list), rejected_chat_count

# if __name__ == "__main__":
    # client_id = "lollypop_design"
    # client_properties = helper.load_properties(client_id)
    # report_db_path = client_properties["REPORT_DB_PATH"]
    # state_db_path = client_properties["STATE_DB_PATH"]
    # log_db_path = client_properties["LOG_DB_PATH"]
    # log_db_file = os.path.join(log_db_path, "Log.db")

    # llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # result = conversation_summary_from_db(llm, db_path, log_db_path)
    # print(result)
    

   