# Import all the necessary packages
import os

import json
import re
from bs4 import BeautifulSoup

from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_community.document_loaders import RecursiveUrlLoader

class LLMNode:

    def __init__(self, llm, embeddings, vectorstore_path, url, all_prompts):
        self.llm = llm
        self.embeddings = embeddings
        self.vectorstore_path = vectorstore_path
        self.url = url
        self.retriever = None
        self.all_prompts = all_prompts
        # index the data first
        self.index_data()
        self.rag_agent_init()

    def bs4_extractor(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        return re.sub(r"\n\n+", "\n\n", soup.text).strip()

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
        # self.retriever = vectorstore.as_retriever()
        self.retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={'k': 6, 'lambda_mult': 0.25})

    def rag_agent_init(self):

        template=self.all_prompts["rag_agent_system_template"]

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
                ("system", template),
                MessagesPlaceholder("messages"),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        self.rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    def rag_agent_run(self, state, config) -> list[BaseMessage]:

        # response = self.rag_chain.invoke(state)
        question = state['messages'][-1].content
        response = self.rag_chain.invoke({"input":question, "messages":state['messages'][:-1]})
        return {
            "messages": [
                # HumanMessage(state["input"]),
                AIMessage(response["answer"]),
            ],
            "context": response["context"],
            "answer": response["answer"],
        }

        

if __name__ == "__main__":
    # Gemini models
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    # vectorstore path
    ROOT_DIR = "Data"
    vectorstore_path = f"{ROOT_DIR}/vectorstore.db"
    URL = "https://terralogic.com/"
    llm_obj = LLMNode(llm, embeddings, vectorstore_path, URL)
    