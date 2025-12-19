#!/usr/bin/env python3
# Setup script for indexing website and PDFs - Academy version
import os
import sys
sys.path.append(os.getcwd())
import re
import argparse
import yaml
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

from langchain_community.document_loaders import RecursiveUrlLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_experimental.text_splitter import SemanticChunker

from src.nodes.search import SearchNode
from utils.logger_config import logger
from shared_admin_api import load_api_key_for_provider

parser = argparse.ArgumentParser(description="Parse company name from terminal.")
parser.add_argument('-n', '--name', type=str, required=True, help='Name of the company')
parser.add_argument('-w', '--website', action='store_true', help='Index website only (skip PDFs)')
parser.add_argument('-p', '--pdf', action='store_true', help='Index PDFs only (skip website)')
parser.add_argument('-u', '--urls', type=str, help='Comma-separated list of URLs to index')
parser.add_argument('-s', '--sitemap', type=str, help='Sitemap XML URL to extract and index URLs from')
parser.add_argument('-f', '--filenames', type=str, help='Comma-separated list of filenames to index (PDF mode only)')
args = parser.parse_args()
client = args.name
index_website_only = args.website
index_pdf_only = args.pdf
custom_urls = args.urls.split(',') if args.urls else None
sitemap_url = args.sitemap
filter_filenames = [f.strip().lower() for f in args.filenames.split(',')] if args.filenames else None

print(f"Client: {client}, Website Only: {index_website_only}, PDF Only: {index_pdf_only}, Custom URLs: {custom_urls}, Sitemap: {sitemap_url}, Filter Filenames: {filter_filenames}")

# Load properties from YAML file
properties_file = os.path.join(os.getcwd(), "client_properties.yaml")
with open(properties_file, "r", encoding="utf-8") as f:
    all_properties = yaml.safe_load(f)
    client_properties = all_properties.get(client, {})

ROOT_DIR = client_properties["ROOT_DIR"]
CLIENT_NAME = client_properties["CLIENT_NAME"]
PDF_FILE = client_properties["PDF_FILE"]
EMBEDDINGS_FILE = client_properties["EMBEDDINGS_FILE"]
FAQ_JSON_FILE = client_properties["FAQ_JSON_FILE"]
# Use custom URLs if provided, otherwise default to config URL
# Convert single config URL to list for consistent handling
# If sitemap is provided, extract URLs from sitemap
if sitemap_url:
    URLS = []  # Will be populated from sitemap
    INDEX_MODE = "sitemap"
elif custom_urls:
    URLS = custom_urls
    INDEX_MODE = "custom_urls"
else:
    URLS = [client_properties["URL"]]
    INDEX_MODE = "default"
vectorstore_path = os.path.join(ROOT_DIR, CLIENT_NAME, client_properties["VECTOR_STORE_FILE"])
uploads_dir = os.path.join(ROOT_DIR, CLIENT_NAME, "uploads")

# Load BYOK secrets (e.g., OpenAI) so embeddings work without .env edits
load_api_key_for_provider(ROOT_DIR, CLIENT_NAME, provider="openai", logger=logger)

embed_model = OpenAIEmbeddings(model="text-embedding-ada-002")

# create the folder if not present
os.makedirs(vectorstore_path, exist_ok=True)
os.makedirs(uploads_dir, exist_ok=True)


def load_pdf_documents(primary_pdf_path: str, uploads_directory: str, filter_names: list = None):
    """Load the base FAQ PDF and any additional PDFs uploaded via the Admin Portal."""
    import time
    documents = []

    def load_pdf(path: str, retry_count=3):
        """Load PDF with retry logic for file locking issues"""
        if not (os.path.exists(path) and path.lower().endswith(".pdf")):
            return []

        for attempt in range(retry_count):
            try:
                loader = PyMuPDFLoader(path)
                docs = loader.load()
                # Explicitly close file handles if possible
                if hasattr(loader, 'close'):
                    loader.close()
                return docs
            except (PermissionError, OSError) as e:
                if attempt < retry_count - 1:
                    print(f"[WARNING] File locked: {path}, retrying in 2 seconds... (attempt {attempt + 1}/{retry_count})")
                    time.sleep(2)
                else:
                    print(f"[ERROR] Failed to load {path} after {retry_count} attempts: {e}")
                    return []
        return []

    # Only load primary PDF if no filter is applied (full re-index) OR if explicitly requested?
    # For now: If filter is applied, ONLY load the filtered files from uploads. Skip primary PDF.
    if not filter_names:
        documents.extend(load_pdf(primary_pdf_path))

    if os.path.isdir(uploads_directory):
        for filename in os.listdir(uploads_directory):
            # Apply filter if provided
            if filter_names:
                # Check if current filename contains any of the filter names
                # (Simple substring match since filenames on disk have UUID prefix)
                # e.g. filter="marvel.pdf", on disk="uuid_marvel.pdf" -> match
                is_match = False
                current_lower = filename.lower()
                for name in filter_names:
                    if name in current_lower:
                        is_match = True
                        break
                
                if not is_match:
                    continue  # Skip this file if it doesn't match filter

            file_path = os.path.join(uploads_directory, filename)
            loaded_docs = load_pdf(file_path)
            if loaded_docs:  # Only extend if we successfully loaded docs
                documents.extend(loaded_docs)

    return documents

# Beautiful soup plain text extractor function
def bs4_extractor(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    return re.sub(r"\n\n+", "\n\n", soup.text).strip()

def extract_urls_from_sitemap(sitemap_url: str) -> list:
    """
    Extract all URLs from a sitemap XML file.

    Args:
        sitemap_url: URL of the sitemap XML file

    Returns:
        List of URLs extracted from the sitemap
    """
    try:
        print(f"Fetching sitemap from: {sitemap_url}")
        response = requests.get(sitemap_url, timeout=30)
        response.raise_for_status()

        # Parse XML
        root = ET.fromstring(response.content)

        # Handle namespace
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        # Extract URLs
        urls = []
        for url_elem in root.findall('.//ns:url/ns:loc', namespace):
            url = url_elem.text.strip()
            if url:
                urls.append(url)

        print(f"Extracted {len(urls)} URLs from sitemap")
        return urls
    except Exception as e:
        print(f"Error extracting URLs from sitemap: {e}")
        logger.error(f"Sitemap parsing error: {e}")
        return []

def load_documents_from_urls(urls: list, extractor=None) -> list:
    """
    Load documents from a list of URLs (non-recursive, direct fetch).

    Args:
        urls: List of URLs to fetch
        extractor: Optional text extractor function

    Returns:
        List of Document objects
    """
    from langchain_community.document_loaders import WebBaseLoader

    documents = []
    total = len(urls)

    print(f"Loading {total} custom URLs (non-recursive)...")

    for idx, url in enumerate(urls, 1):
        try:
            if idx % 10 == 0:  # Progress update every 10 URLs
                print(f"Progress: {idx}/{total} URLs loaded")

            loader = WebBaseLoader(url)
            docs = loader.load()

            # Apply text extraction if provided
            if extractor and docs:
                for doc in docs:
                    doc.page_content = extractor(doc.page_content)

            documents.extend(docs)
        except Exception as e:
            print(f"Failed to load {url}: {e}")
            logger.warning(f"Failed to load URL {url}: {e}")
            continue

    print(f"Successfully loaded {len(documents)} documents from {total} URLs")
    return documents

def create_vectorstore(mode=None, depth=100, website_only=False, pdf_only=False, use_sitemap=False, filter_filenames=None):
    """
    if block: if no vectorstore present, creates vectorstore with both urlloader and faq document
    else block: if vectorstore present, loads from disk and merges faw vectorstore with it

    website_only: If True, only index website content (skip PDFs)
    pdf_only: If True, only index PDFs (skip website)
    use_sitemap: If True, load URLs from sitemap instead of recursive crawling
    filter_filenames: List of filenames to filter by (PDF mode only)
    """

    # Create Vectorstore for RAG agent
    if not os.path.exists(vectorstore_path) or len(os.listdir(vectorstore_path)) == 0:
        docs_list = []

        # If PDF-only mode, skip all website indexing
        if pdf_only:
            print("PDF-only mode: Skipping website indexing")
            text_docs_list = []
        elif use_sitemap:
            # Sitemap mode: Load all URLs from sitemap directly
            total_urls = len(URLS)
            BATCH_SIZE = 50

            if total_urls > BATCH_SIZE:
                print(f"Sitemap mode: Processing {total_urls} URLs in batches of {BATCH_SIZE}")
                docs_list = []  # Will accumulate from all batches

                for i in range(0, total_urls, BATCH_SIZE):
                    batch_num = (i // BATCH_SIZE) + 1
                    total_batches = (total_urls + BATCH_SIZE - 1) // BATCH_SIZE
                    batch_urls = URLS[i:i+BATCH_SIZE]

                    print(f"Batch {batch_num}/{total_batches}: Loading {len(batch_urls)} URLs...")
                    batch_docs = load_documents_from_urls(batch_urls)

                    # Process batch immediately to avoid memory issues
                    batch_splits = text_splitter.split_documents(batch_docs)
                    print(f"Batch {batch_num}/{total_batches}: Split into {len(batch_splits)} chunks")

                    if 'vectorstore' not in locals():
                        # First batch - create initial vectorstore
                        vectorstore = FAISS.from_documents(batch_splits, embed_model)
                        print(f"Batch {batch_num}/{total_batches}: Created initial vectorstore with {len(batch_splits)} chunks")
                    else:
                        # Subsequent batches - create and merge
                        batch_vectorstore = FAISS.from_documents(batch_splits, embed_model)
                        vectorstore.merge_from(batch_vectorstore)
                        print(f"Batch {batch_num}/{total_batches}: Merged {len(batch_splits)} chunks into main vectorstore")

                print(f"✅ Sitemap batch processing complete! Processed {total_urls} URLs in {total_batches} batches")
                sitemap_batch_processed = True  # Flag to indicate vectorstore already created
                docs_list = []  # All processing done, no need for further processing

            else:
                # Small sitemap - process normally
                print(f"Sitemap mode: Loading {total_urls} URLs (small batch)")
                docs_list = load_documents_from_urls(URLS)
        elif INDEX_MODE == "custom_urls":
            # Custom URLs mode: Load ONLY the specified URLs (no recursive crawling)
            print(f"Custom URLs mode: Loading {len(URLS)} specific URLs (no recursive crawling)")
            docs_list = load_documents_from_urls(URLS, extractor=bs4_extractor)
        else:
            # Full website mode: Recursive crawling from homepage
            print(f"Full website mode: Recursive crawling with depth={depth}")
            for url in URLS:
                url = url.strip()
                if not url: continue
                print(f"Loading URL: {url}")
                loader = RecursiveUrlLoader(url, max_depth=depth, extractor=bs4_extractor, timeout=None,  continue_on_failure=False)
                docs_list.extend(loader.load())

        if mode is None:
            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=500, chunk_overlap=100
            )
        elif mode == "semantic":
            text_splitter = SemanticChunker(embed_model, breakpoint_threshold_type="gradient")

        # Filter HTML documents only if using recursive crawling
        # For custom URLs and sitemap, content is already clean
        if use_sitemap or INDEX_MODE == "custom_urls":
            text_docs_list = docs_list
        else:
            # filter out rubbish files from recursive crawling
            text_docs_list = [doc for doc in docs_list if 'text/html' in doc.metadata['content_type']]

        # Conditionally load PDFs and website based on flags
        if pdf_only:
            # PDF-only mode: Load PDFs, no website
            print("PDF-only mode: Loading PDFs, skipping website")
            pdf_path = os.path.join(ROOT_DIR, CLIENT_NAME, PDF_FILE)
            pdf_docs_list = load_pdf_documents(pdf_path, uploads_dir, filter_names=filter_filenames)
            total_docs_list = pdf_docs_list
        elif website_only:
            # Website-only mode: Load website, no PDFs
            print("Website-only mode: Loading website, skipping PDFs")
            total_docs_list = text_docs_list
        else:
            # Default mode: Load both website and PDFs
            print("Full mode: Loading both website and PDFs")
            pdf_path = os.path.join(ROOT_DIR, CLIENT_NAME, PDF_FILE)
            pdf_docs_list = load_pdf_documents(pdf_path, uploads_dir, filter_names=filter_filenames)
            total_docs_list = text_docs_list + pdf_docs_list

        # Check if sitemap batching already created vectorstore
        if 'sitemap_batch_processed' in locals() and sitemap_batch_processed:
            print("Sitemap batching already completed - skipping further processing")
        else:
            doc_splits = text_splitter.split_documents(total_docs_list)

            # BATCH PROCESSING: Split into smaller batches to avoid token limits
            BATCH_SIZE = 30  # Process 30 URLs worth of content at a time
            total_splits = len(doc_splits)

            if total_splits > BATCH_SIZE:
                print(f"Processing {total_splits} document chunks in batches of {BATCH_SIZE}...")

                # Create first batch
                first_batch = doc_splits[:BATCH_SIZE]
                vectorstore = FAISS.from_documents(first_batch, embed_model)
                print(f"Batch 1/{(total_splits + BATCH_SIZE - 1) // BATCH_SIZE}: Created initial vectorstore with {len(first_batch)} chunks")

                # Process remaining batches and merge
                for i in range(BATCH_SIZE, total_splits, BATCH_SIZE):
                    batch_num = (i // BATCH_SIZE) + 1
                    total_batches = (total_splits + BATCH_SIZE - 1) // BATCH_SIZE
                    batch = doc_splits[i:i+BATCH_SIZE]

                    print(f"Batch {batch_num}/{total_batches}: Processing {len(batch)} chunks...")
                    batch_vectorstore = FAISS.from_documents(batch, embed_model)

                    vectorstore.merge_from(batch_vectorstore)
                    print(f"Batch {batch_num}/{total_batches}: Merged into main vectorstore")

                print(f"✅ All {total_batches} batches processed and merged successfully!")
            else:
                # If small enough, process all at once
                print(f"Processing {total_splits} document chunks (small batch, no splitting needed)...")
                vectorstore = FAISS.from_documents(doc_splits, embed_model)

            # Save the documents and embeddings
            vectorstore.save_local(vectorstore_path)

    else:
        if website_only:
            # Website-only mode: Re-index website and overwrite existing vectorstore
            print("Website-only mode: Re-indexing website content only")

            docs_list = []
            if use_sitemap:
                # Sitemap mode: Load all URLs from sitemap directly
                print("Sitemap mode: Loading URLs from sitemap")
                docs_list = load_documents_from_urls(URLS)
            elif INDEX_MODE == "custom_urls":
                # Custom URLs mode: Load ONLY the specified URLs (no recursive crawling)
                print(f"Custom URLs mode: Loading {len(URLS)} specific URLs (no recursive crawling)")
                docs_list = load_documents_from_urls(URLS, extractor=bs4_extractor)
            else:
                # Full website mode: Recursive crawling from homepage
                print(f"Full website mode: Recursive crawling with depth={depth}")
                for url in URLS:
                    url = url.strip()
                    if not url: continue
                    print(f"Loading URL: {url}")
                    loader = RecursiveUrlLoader(url, max_depth=depth, extractor=bs4_extractor, timeout=None,  continue_on_failure=False)
                    docs_list.extend(loader.load())

            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=500, chunk_overlap=100
            )

            # Filter HTML documents only if using recursive crawling
            # For custom URLs and sitemap, content is already clean
            if use_sitemap or INDEX_MODE == "custom_urls":
                text_docs_list = docs_list
            else:
                # filter out rubbish files from recursive crawling
                text_docs_list = [doc for doc in docs_list if 'text/html' in doc.metadata['content_type']]

            doc_splits = text_splitter.split_documents(text_docs_list)

            # BATCH PROCESSING: Split into smaller batches to avoid token limits
            BATCH_SIZE = 30  # Process 30 URLs worth of content at a time
            total_splits = len(doc_splits)

            if total_splits > BATCH_SIZE:
                print(f"Re-indexing: Processing {total_splits} document chunks in batches of {BATCH_SIZE}...")

                # Create first batch
                first_batch = doc_splits[:BATCH_SIZE]
                vectorstore = FAISS.from_documents(first_batch, embed_model)
                print(f"Batch 1/{(total_splits + BATCH_SIZE - 1) // BATCH_SIZE}: Created initial vectorstore with {len(first_batch)} chunks")

                # Process remaining batches and merge
                for i in range(BATCH_SIZE, total_splits, BATCH_SIZE):
                    batch_num = (i // BATCH_SIZE) + 1
                    total_batches = (total_splits + BATCH_SIZE - 1) // BATCH_SIZE
                    batch = doc_splits[i:i+BATCH_SIZE]

                    print(f"Batch {batch_num}/{total_batches}: Processing {len(batch)} chunks...")
                    batch_vectorstore = FAISS.from_documents(batch, embed_model)

                    vectorstore.merge_from(batch_vectorstore)
                    print(f"Batch {batch_num}/{total_batches}: Merged into main vectorstore")

                print(f"✅ All {total_batches} batches processed and merged successfully!")
            else:
                # If small enough, process all at once
                print(f"Re-indexing: Processing {total_splits} document chunks (small batch, no splitting needed)...")
                vectorstore = FAISS.from_documents(doc_splits, embed_model)

            vectorstore.save_local(vectorstore_path)
        else:
            # PDF mode: Load existing vectorstore and merge PDFs
            print("PDF mode: Loading existing vectorstore and adding PDFs")
            
            if filter_filenames:
                print(f"Partially indexing specific files: {filter_filenames}")
            
            vectorstore = FAISS.load_local(vectorstore_path, embed_model, allow_dangerous_deserialization=True)

            # load faq document(s)
            pdf_path = os.path.join(ROOT_DIR, CLIENT_NAME, PDF_FILE)
            pdf_docs_list = load_pdf_documents(pdf_path, uploads_dir, filter_names=filter_filenames)
            print(f"Loaded {len(pdf_docs_list)} PDF documents (pages)")

            if len(pdf_docs_list) > 0:
                # Use smaller chunk size to preserve granular content
                text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                        chunk_size=500, chunk_overlap=100
                    )
                doc_splits = text_splitter.split_documents(pdf_docs_list)
                print(f"Split into {len(doc_splits)} chunks")

                if len(doc_splits) > 0:
                    # Create a FAQ vectorstore
                    faq_vectorstore = FAISS.from_documents(doc_splits, embed_model)
                    print(f"Created new vectorstore with {len(doc_splits)} chunks")

                    # merge faq vectorstore with og vectorstore
                    vectorstore.merge_from(faq_vectorstore)
                    print("Merged PDF vectorstore with existing vectorstore")

                    # Save the documents and embeddings
                    vectorstore.save_local(vectorstore_path)
                    print(f"Saved updated vectorstore to {vectorstore_path}")
                else:
                    print("No chunks to add - skipping merge")
            else:
                print("No PDF documents found - skipping merge")


if __name__ == "__main__":
    # Extract URLs from sitemap if sitemap mode is enabled
    use_sitemap_mode = False
    if sitemap_url:
        print(f"Extracting URLs from sitemap: {sitemap_url}")
        sitemap_urls = extract_urls_from_sitemap(sitemap_url)
        if sitemap_urls:
            URLS = sitemap_urls
            use_sitemap_mode = True
            print(f"Will index {len(URLS)} URLs from sitemap")
        else:
            print("Failed to extract URLs from sitemap, aborting...")
            sys.exit(1)

    # Load FAQ data on startup (skip if website-only mode)
    if not index_website_only:
        # Construct paths
        pdf_path = os.path.join(ROOT_DIR, CLIENT_NAME, PDF_FILE)
        embeddings_path = os.path.join(ROOT_DIR, CLIENT_NAME, EMBEDDINGS_FILE)
        faq_json_path = os.path.join(ROOT_DIR, CLIENT_NAME, FAQ_JSON_FILE)
        
        # Force regeneration of FAQ data to include new uploads
        if os.path.exists(faq_json_path):
            os.remove(faq_json_path)
            print(f"Removed existing FAQ JSON: {faq_json_path}")
        if os.path.exists(embeddings_path):
            os.remove(embeddings_path)
            print(f"Removed existing Embeddings: {embeddings_path}")

        search_obj = SearchNode(pdf_path, embeddings_path, faq_json_path, uploads_dir)
        search_obj.load_faq_data()
        print("Created FAQ Embeddings for LLM-free journey ---------------------")

    # create vectorstore for RAG
    create_vectorstore(depth=1, website_only=index_website_only, pdf_only=index_pdf_only, use_sitemap=use_sitemap_mode, filter_filenames=filter_filenames)

    if use_sitemap_mode:
        print("Created Vectorstore from sitemap URLs ----------------")
        logger.info("Setup complete - Indexed content from sitemap")
    elif index_website_only:
        print("Created Vectorstore for website content only ----------------")
        logger.info("Setup complete - Re-indexed website content")
    else:
        if filter_filenames:
            print(f"Updated Vectorstore with {len(filter_filenames)} specific files ----------------")
            logger.info(f"Setup complete - Indexed {len(filter_filenames)} specific files")
        else:
            print("Created Vectorstore for RAG agent (PDFs + Website) ----------------")
            logger.info("Setup complete - Created Knowledge store with FAQs and Website data")
