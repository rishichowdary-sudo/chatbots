import sys
import os
sys.path.append(os.getcwd())
import pprint

from langgraph.graph import START, MessagesState, StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import Annotated, Sequence, List
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from src.nodes.search import SearchNode
from src.nodes.llm_driven import LLMNode
from utils.helper import load_client_properties, load_prompts

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
    # input: str
    context: str
    answer: str

class FAQLLMSubgraph:
    def __init__(self, llm, decision_llm, embeddings, all_prompts, client_properties):
        self.llm = llm
        self.decision_llm = decision_llm
        self.embeddings = embeddings

        # setting up properties
        ROOT_DIR = client_properties["ROOT_DIR"]
        CLIENT_NAME = client_properties["CLIENT_NAME"]
        PDF_PATH = os.path.join(ROOT_DIR, CLIENT_NAME, client_properties["PDF_FILE"])
        EMBEDDINGS_PATH = os.path.join(ROOT_DIR, CLIENT_NAME, client_properties["EMBEDDINGS_FILE"])
        FAQ_JSON_PATH = os.path.join(ROOT_DIR, CLIENT_NAME, client_properties["FAQ_JSON_FILE"])
        uploads_dir = os.path.join(ROOT_DIR, CLIENT_NAME, "uploads")
        vectorstore_path = os.path.join(ROOT_DIR, CLIENT_NAME, client_properties["VECTOR_STORE_FILE"])

        URL = client_properties["URL"]
        # properties values are stored as string
        self.FAQ_SEARCH_THRESH = float(client_properties["FAQ_SEARCH_THRESH"]) 


        # initialize LLM, search, career nodes
        self.llm_obj = LLMNode(self.llm, self.embeddings, vectorstore_path, URL, all_prompts)
        self.search_obj = SearchNode(PDF_PATH, EMBEDDINGS_PATH, FAQ_JSON_PATH, uploads_dir)
        self.search_obj.load_faq_data()      # load the faq data on startup
        self.all_prompts = all_prompts

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
        if top_score < self.FAQ_SEARCH_THRESH:
            return {'score':top_score, 'options':options[:top_n - 1]}
        ai_response = AIMessage(content=top_faqs[0]['answer'])
        return {'messages': [ai_response], 'score':top_score, 'options':options[1:top_n]}

    def route_to_llm(self, state):

        top_score = state['score']
        if top_score < self.FAQ_SEARCH_THRESH:
            return "yes"
        return "no"

    def tool_condition(self, state):

        prompt = PromptTemplate(
            template=self.all_prompts["job_intent_template"],
            input_variables=["question"],
        )

        rag_chain = prompt | self.decision_llm | StrOutputParser()
        messages = state['messages']
        question = messages[-1].content
        output = rag_chain.invoke({"question": question})
        output = output.strip()

        return output


    def faq_llm_career_build_graph(self):
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node('llm_agent', self.llm_obj.rag_agent_run)
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
        return graph


if __name__ == "__main__":
        
    # LLM and Embed models
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    decision_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Compile
    client = "terralogic_academy"
    client_properties = load_client_properties(client)
    all_prompts = load_prompts(client_properties)
    faq_career_node = FAQLLMSubgraph(llm, decision_llm, embeddings, all_prompts, client_properties)
    graph = faq_career_node.faq_llm_career_build_graph()
    id = "abc123"
    config = {"configurable": {"thread_id": id}}
    # testing the graph
    while True:
        print("***************************")
        user_input = input("Human Message:")
        if 'bye' in user_input:
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
