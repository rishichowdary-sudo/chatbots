import os
import sys

from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from dotenv import load_dotenv

sys.path.append(os.getcwd())
import utils.helper as helper
# Load environment variables
load_dotenv()

client="terralogic"
client_properties = helper.load_client_properties(client)
ROOT_DIR = client_properties["ROOT_DIR"]
CLIENT_NAME = client_properties["CLIENT_NAME"]
PDF_PATH = os.path.join(ROOT_DIR, CLIENT_NAME, client_properties["PDF_FILE"])
EMBEDDINGS_PATH = os.path.join(ROOT_DIR, CLIENT_NAME, client_properties["EMBEDDINGS_FILE"])
FAQ_JSON_PATH = os.path.join(ROOT_DIR, CLIENT_NAME, client_properties["FAQ_JSON_FILE"])
URL = client_properties["URL"]
DOC_FILE_PATH = os.path.join(ROOT_DIR, CLIENT_NAME, "ai-agent-overview-casestudy.docx")
vectorstore_path = os.path.join(ROOT_DIR, CLIENT_NAME, client_properties["VECTOR_STORE_FILE"])

embed_model = OpenAIEmbeddings(model="text-embedding-ada-002")

# prepare vector store from the document file and then combine with the main vector store

# load text document from file
text_loader = Docx2txtLoader(DOC_FILE_PATH)
text_doc_list = text_loader.load()
# split text 
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=1000, chunk_overlap=100
            )
doc_splits = text_splitter.split_documents(text_doc_list)
print(f"document splits {len(doc_splits)}")
doc_vectorstore = FAISS.from_documents(doc_splits, embed_model)

# merge faw vectorstore with og vectorstore
vectorstore = FAISS.load_local(vectorstore_path, embed_model, allow_dangerous_deserialization=True)
vectorstore.merge_from(doc_vectorstore)

# Save the documents and embeddings
vectorstore.save_local(vectorstore_path)

