from typing import Literal, Annotated, List

from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import MessagesState
from langgraph.checkpoint.memory import MemorySaver
# from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from datetime import datetime

import os
import sys
import uuid
from dotenv import load_dotenv

sys.path.append(os.getcwd())
from src.subgraphs.ServiceInformation_subgraph import ServiceInformationSubgraph
from src.subgraphs.faq_llm_career import FAQLLMSubgraph
from utils.logger_config import logger
from utils.helper import load_client_properties, load_application_properties, load_prompts

# Import shared admin API helper for loading model configuration
try:
    from shared_admin_api import load_model_for_provider
except ImportError:
    # Fallback if shared_admin_api is not available
    def load_model_for_provider(root_dir, client_id, provider, default_model="gpt-4o-mini", logger=None):
        return default_model

# Load environment variables
load_dotenv()


class OverallState(MessagesState):
    # messages is implicit
    name: str
    email: str
    score: float
    options: List[str]


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
        name = state.get("name", None)
        email = state.get("email", None)
        self.status = self.chain.invoke({"question":question, "name":name, "email":email})
        self.status = self.status.strip()
        #response_msg = HumanMessage(content=question)
        return {'messages': messages}
    
    def fallback(self, state):

        fallback_msg = "Sorry I didn't get that. Could you please repeat it?"
        fallback_response = AIMessage(content=fallback_msg)
        return {'messages':[fallback_response]}

    def get_next_node(self, state):

        if self.status == "introducing":
            self.next_node = "introduction_node"
        elif self.status == "answering":
            self.next_node = "faq_llm_node"
        else:
            self.next_node = "fallback_node"
        return self.next_node
    

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

        client_properties = load_client_properties(self.client)

        # Load model from API key configuration (defaults to gpt-4o-mini if not set)
        root_dir = client_properties.get("ROOT_DIR", "Data")
        model_name = load_model_for_provider(root_dir, self.client, "openai", default_model="gpt-4o-mini", logger=logger)

        # Initialize LLMs with error handling to allow startup without API keys
        try:
            llm = ChatOpenAI(model=model_name, temperature=0)
            decision_llm = ChatOpenAI(model=model_name, temperature=0)
            embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        except Exception as e:
            logger.warning(f"Failed to initialize LLMs for {client} with model {model_name} - API key may not be configured: {e}")
            # Set to None to allow deferred initialization
            llm = None
            decision_llm = None
            embeddings = None

        # Node creations - only if LLMs initialized successfully
        if load_nodes and llm is not None:
            all_prompts = load_prompts(client_properties)
            self.supervisor_agent = Supervisor(decision_llm, all_prompts)
            self.supervisor_node = self.supervisor_agent.understand

            service_info_subgraph = ServiceInformationSubgraph(llm, decision_llm, all_prompts)
            self.service_info_node = service_info_subgraph.IntroductionNode

            faq_subgraph = FAQLLMSubgraph(llm, decision_llm, embeddings, all_prompts, client_properties)
            self.faq_node = faq_subgraph.faq_llm_career_build_graph()

            self.fallback_node = self.supervisor_agent.fallback
        else:
            # Set placeholder nodes if LLMs not available
            self.supervisor_agent = None
            self.supervisor_node = None
            self.service_info_node = None
            self.faq_node = None
            self.fallback_node = None
        
        app_properties = load_application_properties()
        self.state_db_dir = app_properties['STATE_DB_PATH']     # getting the parent directory of db file
        if not os.path.exists(self.state_db_dir):
            os.makedirs(self.state_db_dir, exist_ok=True)

    def build_graph(self):
        # Skip graph building if nodes weren't initialized (no API key)
        if self.supervisor_node is None:
            logger.warning(f"Cannot build graph for {self.client} - nodes not initialized (API key required)")
            self.graph = None
            return

        graph_builder = StateGraph(OverallState)
        graph_builder.add_node("supervisor_node", self.supervisor_node)
        graph_builder.add_node("introduction_node", self.service_info_node)
        graph_builder.add_node("faq_llm_node", self.faq_node)
        graph_builder.add_node("fallback_node", self.fallback_node)

        graph_builder.add_edge(START, "supervisor_node")
        graph_builder.add_conditional_edges("supervisor_node", self.supervisor_agent.get_next_node)
        graph_builder.add_edge("introduction_node", END)
        graph_builder.add_edge("faq_llm_node", END)
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

            state_db_file = os.path.join(self.state_db_dir, self.client)
            conn = sqlite3.connect(state_db_file, check_same_thread=False)
            memory = SqliteSaver(conn)

        self.graph = graph_builder.compile(checkpointer=memory)
    

    def run_graph(self, user_input, session_id):
        config = {"configurable": {"thread_id": session_id}}
        llm_free_options = []
        chatbot_answer = "Something went wrong on our end. Please try again after a little while. Apologize for the inconvenience."
        inputs = {
            "messages": [
                ("user", user_input),
            ]
        }

        try:
            output = self.graph.invoke(inputs, config)
            chatbot_answer = output['messages'][-1].content
            if 'options' in output:
                llm_free_options = output['options']
        
        except Exception as e:
            logger.exception(f"run_graph() error while invoking main graph {e}")

        return {"chatbot_answer": chatbot_answer, "llm_free_options": llm_free_options}


if __name__ == "__main__":
    multi_graph = MultiTenantGraph(client="terralogic_academy", state_in_memory=False)
    multi_graph.build_graph()
    session_id = str(uuid.uuid4())
    print(session_id)

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        output = multi_graph.run_graph(user_input, session_id = session_id)
        print("AI bot: ", output["chatbot_answer"])
        if 'llm_free_options' in output:
            print("LLM-free options: ", output['llm_free_options'])
        print("***************************")

    # uncomment to view the graph
    # with open("graph_multi_tenant.png", "wb") as png:
    #     png.write(lollypop_design.graph.get_graph(xray=1).draw_mermaid_png())
