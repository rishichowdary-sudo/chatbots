import sys
import os
sys.path.append(os.getcwd())
import pprint
import uuid

from langgraph.graph import START, MessagesState, StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import Annotated, Sequence, List
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from src.nodes.search import SearchNode
from src.nodes.llm_driven import LLMNode
import configparser
import yaml

from utils.logger_config import logger

load_dotenv()

# Directory initializations
# ROOT_DIR = "Data"
# PDF_PATH = f'{ROOT_DIR}/faq_data/Lollypop_Design_FAQS.pdf'
# EMBEDDINGS_PATH = f'{ROOT_DIR}/faq_data/faq_embeddings.npz'
# FAQ_JSON_PATH = f'{ROOT_DIR}/faq_data/faqs_from_pdf.json'
# vectorstore_path = f"{ROOT_DIR}/vectorstore.db"

# Website for indexing
# URL = "https://lollypop.design/"
# career_page_url = "https://lollypop.design/careers/"
# FAQ_SEARCH_THRESH = 0.85


# state definition
class AgentState(TypedDict):
    # The add_messages function defines how an update should be processed
    # Default is to replace. add_messages says "append"
    messages: Annotated[Sequence[BaseMessage], add_messages]
    score: float
    options: List[str]
    chatMessageOptions: List[str]
    # input: str
    context: str
    answer: str
    jobs : List

class FAQLLMSubgraph:
    def __init__(self, llm, decision_llm, embeddings, all_prompts, client_properties, type='projects'):
        self.llm = llm
        self.decision_llm = decision_llm
        self.embeddings = embeddings
        self.all_prompts = all_prompts
        self.type = type

        # setting up properties
        ROOT_DIR = client_properties["ROOT_DIR"]
        CLIENT_NAME = client_properties["CLIENT_NAME"]
        PDF_PATH = os.path.join(ROOT_DIR, CLIENT_NAME, client_properties["PDF_FILE"])
        EMBEDDINGS_PATH = os.path.join(ROOT_DIR, CLIENT_NAME, client_properties["EMBEDDINGS_FILE"])
        FAQ_JSON_PATH = os.path.join(ROOT_DIR, CLIENT_NAME, client_properties["FAQ_JSON_FILE"])
        vectorstore_path = os.path.join(ROOT_DIR, CLIENT_NAME, client_properties["VECTOR_STORE_FILE"])

        URL = client_properties["URL"]
        # properties values are stored as string
        self.FAQ_SEARCH_THRESH = float(client_properties["FAQ_SEARCH_THRESH"]) 


        # initialize LLM, search, career nodes
        self.llm_obj = LLMNode(self.llm, self.embeddings, vectorstore_path, URL, all_prompts, self.type)

        # only services flow requires llm_free. 
        if self.type == "services":
            self.search_obj = SearchNode(PDF_PATH, EMBEDDINGS_PATH, FAQ_JSON_PATH)
            self.search_obj.load_faq_data()      # load the faq data on startup

    # condition and routing functions
    def llm_free(self, state):

        top_n = 7
        messages = state['messages']
        question = messages[-1].content
        top_faqs, top_scores = self.search_obj.faq_search(question, top_n=top_n, mode='cosine')
        options = []                    # consists top 4 QAs. Top 1 is given as answer, rest 3 questions as options
        for faq in top_faqs:
            options.append(faq['question'])

        top_score = float(top_scores[0])

        top_n = top_n if len(options) >= top_n else len(options)    # acconting for options less than top_n

        if top_score < self.FAQ_SEARCH_THRESH:
            return {'score':top_score, 'options':options[:top_n - 1], "chatMessageOptions": [], 'jobs':[]}
        ai_response = AIMessage(content=top_faqs[0]['answer'])
        return {'messages': [ai_response], 'score':top_score, 'options':options[1:top_n], "chatMessageOptions": [], 'jobs': []}

    def route_to_llm(self, state):

        top_score = state['score']
        if top_score < self.FAQ_SEARCH_THRESH:
            return "yes"
        return "no"



    def faq_llm_career_build_graph(self):
        workflow = StateGraph(AgentState)

        # add llm_agent. This is needed for both services and projects
        workflow.add_node('llm_agent', self.llm_obj.rag_agent_run)

        if self.type == "projects":
            # flow: START -> llm_agent -> END         
            # add edges
            workflow.add_edge(START, "llm_agent")


        if self.type == "services":
            # flow: START -> llm_free -> llm_agent -> END
            #                         -> END
            # Add llm_free node, which is additional for services subgraph
            workflow.add_node('llm_free', self.llm_free)

            # Add edges
            workflow.add_edge(START, "llm_free")
            workflow.add_conditional_edges(
                "llm_free",
                self.route_to_llm,
                {
                    "yes": "llm_agent",
                    "no": END,
                },
            )

        workflow.add_edge("llm_agent", END)

        memory = MemorySaver()
        graph = workflow.compile(checkpointer=memory)
        logger.info("FAQ LLM SubGraph built and compiled")
        return graph


if __name__ == "__main__":

    def _load_prompts(client_properties):
        prompts_config = configparser.ConfigParser()
        prompts_file_path = os.path.join(client_properties["ROOT_DIR"], client_properties["CLIENT_NAME"], client_properties["SYSTEM_PROMPTS_FILE"])
        prompts_config.read(prompts_file_path)
        all_prompts = prompts_config["prompts"]
        return all_prompts
    
    def _load_properties(client):
        with open("client_properties.yaml") as file:
            client_properties = yaml.safe_load(file)
            client_properties = client_properties[client]
            return client_properties
        
    # LLM and Embed models
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    decision_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Compile
    client = "terralogic"
    client_properties = _load_properties(client)
    all_prompts = _load_prompts(client_properties)
    faq_career_node = FAQLLMSubgraph(llm, decision_llm, embeddings, all_prompts, client_properties)
    graph = faq_career_node.faq_llm_career_build_graph()
    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}
    # testing the graph
    while True:
        print("***************************")
        user_input = input("Human Message:")
        if  user_input.lower() in ["quit", "exit", "q"]:
            print('Thank you for contacting TL. Have a nice day!')
            break
        inputs = {
            # "input": user_input, 
            "messages": [
                ("user", user_input),
            ]
        }
        output = graph.invoke(inputs, config)
        print("AI message: ", output['messages'][-1].content)
        if 'options' in output:
            print("LLM-free options: ", output['options'])
        print("***************************")
