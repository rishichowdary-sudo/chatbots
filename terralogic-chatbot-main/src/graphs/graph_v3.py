from typing import Literal, Annotated, List

from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import ToolNode, tools_condition
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_cohere import ChatCohere
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import MessagesState
from langgraph.checkpoint.memory import MemorySaver
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from datetime import datetime
import configparser
import yaml
import markdown

import os
import sys
import uuid
from dotenv import load_dotenv

sys.path.append(os.getcwd())
from src.subgraphs.introduction_subgraph import ServiceInformationSubgraph
from src.subgraphs.service_subgraph import FAQLLMSubgraph
from src.subgraphs.careers_subgraph import CareerToolNode

from utils.logger_config import logger
import utils.helper as helper

# Load environment variables
load_dotenv()

class OverallState(MessagesState):
    # messages is implicit
    name: str
    email: str
    score: float
    options: List[str]
    next_node: str
    mode: str
    chatMessageOptions: List[str]
    jobs: List


class Supervisor:
    """central supervising agent that transfers control to other nodes"""

    def __init__(self, llm, all_prompts):
        self.llm = llm
        self.next_node = "fallback_node"
        self.status = ""
        prompt = PromptTemplate(
            template = all_prompts["supervisor_prompt"],
            input_variables=["question", "name", "email"],
        )
        self.chain = prompt | self.llm | StrOutputParser()

    def understand(self, state):

        messages = state['messages']
        question = messages[-1].content
        mode = state.get("mode", None)
        if mode is None:
            return {'messages': messages, "mode": "introducing"}
        elif mode == "answering":
            if question.lower() == "explore services":
                return {'messages': messages, "next_node": "services"}
            if question.lower() == "start a project":
                return {'messages': messages, "next_node": "services"}
            if question.lower() == "looking for a job":
                return {"messages": messages, "next_node": "career_node"}
        return {'messages': messages}
    
    def fallback(self, state):

        fallback_msg = "Sorry I didn't get that. Could you please repeat it?"
        fallback_response = AIMessage(content=fallback_msg)
        logger.info("Supervisor failed to route to services/projects/careers")
        return {'messages':[fallback_response]}

    def get_next_node(self, state):

        if state["mode"] == "introducing":
            return "introduction_node"
        elif state["next_node"] == "services":
            return "service_node"
        elif state["next_node"] == "projects":
            return "project_node"
        elif state["next_node"] == "career_node":
            return "career_node"
        else:
            return "fallback_node"
    

# def stream_graph_updates(user_input: str, config: dict):
#     for event in graph.stream({"messages": [("user", user_input)]}, config):
#         for value in event.values():
#             print("Assistant: ", value["messages"][-1].content)


class MultiTenantGraph:
    def __init__(self, client, state_in_memory=False, load_nodes=True):
        # llm = ChatCohere(model='command-r-plus-08-2024')
        self.client = client
        self.state_in_memory = state_in_memory
        # decision_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
        # embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        try: 
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            decision_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

        
            client_properties = helper.load_client_properties(self.client)
            self.state_db_path = helper.load_application_properties()["STATE_DB_PATH"]
            os.makedirs(os.path.join(self.state_db_path), exist_ok=True)

            # Node creations
            if load_nodes:
                all_prompts = self._load_prompts(client_properties)
                self.supervisor_agent = Supervisor(decision_llm, all_prompts)
                self.supervisor_node = self.supervisor_agent.understand

                service_info_subgraph = ServiceInformationSubgraph(llm, decision_llm, all_prompts)
                self.service_info_node = service_info_subgraph.build_graph()

                service_subgraph = FAQLLMSubgraph(llm, decision_llm, embeddings, all_prompts, client_properties, "services")
                self.service_node = service_subgraph.faq_llm_career_build_graph()

                project_subgraph = FAQLLMSubgraph(llm, decision_llm, embeddings, all_prompts, client_properties, "projects")
                self.project_node = project_subgraph.faq_llm_career_build_graph()

                career_subgraph = CareerToolNode(llm, client_properties, all_prompts)
                self.career_node = career_subgraph.build_graph()

                self.fallback_node = self.supervisor_agent.fallback

        except Exception as e:
            logger.exception(f"LLM initialization failed at MultiTenantGraph")

    
    def _load_prompts(self, client_properties):
        prompts_config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        prompts_file_path = os.path.join(client_properties["ROOT_DIR"], client_properties["CLIENT_NAME"], client_properties["SYSTEM_PROMPTS_FILE"])
        prompts_config.read(prompts_file_path)
        all_prompts = prompts_config["prompts"]
        return all_prompts
    
    def _load_properties(self, client):
        with open("client_properties.yaml") as file:
            client_properties = yaml.safe_load(file)
            client_properties = client_properties[client]
            return client_properties

    def build_graph(self):
        graph_builder = StateGraph(OverallState)
        graph_builder.add_node("supervisor_node", self.supervisor_node)
        graph_builder.add_node("introduction_node", self.service_info_node)
        graph_builder.add_node("service_node", self.service_node)
        graph_builder.add_node("project_node", self.project_node)
        graph_builder.add_node("career_node", self.career_node)
        graph_builder.add_node("fallback_node", self.fallback_node)

        graph_builder.add_edge(START, "supervisor_node")
        graph_builder.add_conditional_edges("supervisor_node", self.supervisor_agent.get_next_node)
        graph_builder.add_edge("introduction_node", END)
        graph_builder.add_edge("service_node", END)
        graph_builder.add_edge("project_node", END)
        graph_builder.add_edge("career_node", END)
        graph_builder.add_edge("fallback_node", END)

        # storing the conversation state either in-memory or in server local storage
        # when off memory- one file is created everytime graph is built
        if self.state_in_memory:
            memory = MemorySaver()
        else:
            # creating file only by date, to avoid multiple files creation in gunicorn 

            # commenting out on Dec 2, 2024 to resolve multiple file creation
            # curr_time = datetime.now().strftime("%Y%m%d")
            # db_file = f"{self.client}_{curr_time}.db"
            ## 
            db_file = f"{self.client}.db"
            db_path = os.path.join(self.state_db_path, db_file)
            conn = sqlite3.connect(db_path, check_same_thread=False)
            memory = SqliteSaver(conn)

        self.graph = graph_builder.compile(checkpointer=memory)
        logger.info("Graph built and compiled")
    

    def _post_processing(self, output):
        llm_free_options = []
        chatMessageOptions = []
        jobs = []

        if 'options' in output and 'next_node' in output and output['next_node'] == 'services':
            llm_free_options = output['options']
        
        if 'chatMessageOptions' in output:
            chatMessageOptions = output['chatMessageOptions']

        if 'jobs' in output:
            jobs = output['jobs']
        
        chatbot_answer = output['messages'][-1].content
        extension_configs = {
            'markdown_link_attr_modifier': {
                'new_tab': 'on',
            },
        }
        chatbot_answer_html = markdown.markdown(chatbot_answer, extensions=['extra', 'mdx_truly_sane_lists','markdown_link_attr_modifier'], extension_configs=extension_configs)
        # print("--------------------------------------------------------------------------------")
        # print("raw text")
        # print(chatbot_answer)
        # print("\n")
        # print("converted text")
        # print(repr(chatbot_answer_html))
        # print("--------------------------------------------------------------------------------")

        return [chatbot_answer_html, llm_free_options, chatMessageOptions, jobs]
    

    def run_graph(self, user_input, session_id):
        config = {"configurable": {"thread_id": session_id}}
        llm_free_options = []
        chatMessageOptions = []
        jobs = []
        chatbot_answer = "Hmm... that one's got me scratching my virtual head! Could you rephrase or give me a bit more detail? I'll do my best to assist you!"
        inputs = {
            "messages": [
                ("user", user_input),
            ]
        }

        try:
            output = self.graph.invoke(inputs, config)
            chatbot_answer, llm_free_options, chatMessageOptions, jobs = self._post_processing(output)

        except Exception as e:
            logger.exception(f"run_graph() error while invoking main graph {e}")

        return {"chatbot_answer": chatbot_answer, "llm_free_options": llm_free_options, "chatMessageOptions": chatMessageOptions, "jobs":jobs}
        


if __name__ == "__main__":
    multi_graph = MultiTenantGraph(client="terralogic", state_in_memory=False)
    multi_graph.build_graph()
    session_id = str(uuid.uuid4())

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        output = multi_graph.run_graph(user_input, session_id = session_id)
        print("AI bot: ", output["chatbot_answer"])
        if 'llm_free_options' in output:
            print("LLM-free options: ", output['llm_free_options'])
        if 'chatMessageOptions' in output:
            print("chatMessageOptions: ", output['chatMessageOptions'])
        if 'jobs' in output:
            print("jobs: ", output['jobs'])
        print("***************************")

    # uncomment to view the graph
    with open("graph_terralogic.png", "wb") as png:
        png.write(multi_graph.graph.get_graph(xray=1).draw_mermaid_png())
