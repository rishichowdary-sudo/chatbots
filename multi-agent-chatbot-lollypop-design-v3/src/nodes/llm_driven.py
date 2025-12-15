# Import all the necessary packages
import os

import sys
sys.path.append(os.getcwd())
import re
from bs4 import BeautifulSoup
from collections import defaultdict

from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain_core.messages import BaseMessage
from langchain_community.document_loaders import RecursiveUrlLoader
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import AIMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser

from utils.logger_config import logger

class LLMNode:

    def __init__(self, llm, embeddings, vectorstore_path, url, all_prompts, type):
        self.llm = llm
        self.embeddings = embeddings
        self.vectorstore_path = vectorstore_path
        self.url = url
        self.retriever = None
        self.all_prompts = all_prompts
        self.type = type
        # index the data first
        self.index_data()
        self.rag_agent_init()
        self.source_validator()

    def bs4_extractor(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        return re.sub(r"\n\n+", "\n\n", soup.text).strip()

    def source_validator(self):
        prompt = PromptTemplate(
                    template = self.all_prompts["source_validator_template"],
                    input_variables=["sources", "question"],
                )
        self.source_valid_chain = prompt | self.llm | JsonOutputParser()

    def index_data(self):

        # crete index for the first time
        if len(os.listdir(self.vectorstore_path)) == 0:
            loader = RecursiveUrlLoader(self.url, extractor=self.bs4_extractor)
            docs_list = loader.load()
            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=100, chunk_overlap=50
            )
            doc_splits = text_splitter.split_documents(docs_list)
            # Create a vectorstore
            vectorstore = FAISS.from_documents(doc_splits, self.embeddings)
            # Save the documents and embeddings
            vectorstore.save_local(self.vectorstore_path)
        else:
            # load saved index
            vectorstore = FAISS.load_local(self.vectorstore_path, self.embeddings, allow_dangerous_deserialization=True)

        # Create retriever
        self.retriever = vectorstore.as_retriever()

        # All sources
        self.sources = defaultdict(list)
        for key in vectorstore.docstore._dict.keys():
            doc = vectorstore.docstore._dict[key]
            source = doc.metadata.get('source')
            if self.type in source:
            # if doc.metadata.get('source') not in sources:
                self.sources[source].append(doc)

        logger.info("Vectorstore Loaded")

    def rag_agent_init(self):

        if "services" in self.type:
            template=self.all_prompts["rag_agent_system_template"]
        elif "projects" in self.type:
            template=self.all_prompts["rag_agent_project_template"]

        ### Contextualize question ###
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("messages"),
                ("human", "{input}"),
            ]
        )

        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_q_prompt
        )
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", template + "\n\n " + " {context_2}"),
                MessagesPlaceholder("messages"),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        self.rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        logger.info("RAG agent initialized")

    def rag_agent_run(self, state, config) -> list[BaseMessage]:

        answer, context = self.rag_agent_project_run(state)

        # options key is by default an empty list. Applicable when type is projects or when there is no option key.
        options = []
        # only when type is services and options is already available in the state, it is retained.
        if self.type == "services" and 'options' in state:
            options = state['options']

        return {
            "messages": [
                answer,
            ],
            "context": context,
            "answer": answer,
            "chatMessageOptions": [],
            "jobs":[],
            "options": options
        }

    def rag_agent_project_run(self, state) -> list[BaseMessage]:

        question = state['messages'][-1].content
        if self.type == "services":
            query_relevant_docs = []
            query_relevant_context = ""
        else:
            query_relevant_sources_dict = self.source_valid_chain.invoke({"question":question.lower(), "sources":list(self.sources.keys())})
            query_relevant_sources = list(query_relevant_sources_dict.values())
            # query_relevant_docs = [doc for source in query_relevant_sources for doc in self.sources[source]]
            query_relevant_docs = list(self.sources[query_relevant_sources[0]])
            query_relevant_context = "\n\n".join(doc.page_content for doc in query_relevant_docs)
        response = self.rag_chain.invoke({"input":question, "context_2":query_relevant_docs, "messages":state['messages'][:-1]})
        return AIMessage(response["answer"]), query_relevant_context



if __name__ == "__main__":
    # Gemini models
    # llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
    # embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

    # vectorstore path
    ROOT_DIR = "Data"
    vectorstore_path = f"{ROOT_DIR}/vectorstore.db"
    URL = "https://terralogic.com/"
    llm_obj = LLMNode(llm, embeddings, vectorstore_path, URL)
