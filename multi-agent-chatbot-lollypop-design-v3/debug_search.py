
import os
import sys
import re
import json
import numpy as np
import fitz
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Mock logger
class Logger:
    def info(self, msg): print(f"INFO: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")

logger = Logger()

class SearchNode:
    
    def __init__(self, pdf_path, embeddings_path, faq_json_path, uploads_dir=None) -> None:
        self.embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.pdf_path = pdf_path
        self.embeddings_path = embeddings_path
        self.faq_json_path = faq_json_path
        self.uploads_dir = uploads_dir
        self.faqs = None
        self.faq_embeddings = None
        
    def embed_sentences(self, sentences):
        return self.embed_model.encode(sentences)
    
    def extract_text_from_pdf_pymupdf(self):
        pages = []
        # Load base PDF
        if os.path.exists(self.pdf_path):
            print(f"Reading base PDF: {self.pdf_path}")
            doc = fitz.open(self.pdf_path)
            pages.extend([page.get_text() for page in doc])
        else:
            print(f"Base PDF not found: {self.pdf_path}")

        # Load uploaded PDFs
        if self.uploads_dir and os.path.exists(self.uploads_dir):
            print(f"Scanning uploads dir: {self.uploads_dir}")
            for filename in os.listdir(self.uploads_dir):
                if filename.lower().endswith(".pdf"):
                    file_path = os.path.join(self.uploads_dir, filename)
                    print(f"Reading uploaded PDF: {file_path}")
                    try:
                        doc = fitz.open(file_path)
                        pages.extend([page.get_text() for page in doc])
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
        return pages
    
    def split_pdf_text_into_faqs(self, pdf_text):
        faqs = []
        current_faq = {"question": "", "answer": ""}
        collecting_answer = False

        for page in pdf_text:
            lines = page.split('\n')
            for line in lines:
                line = line.strip()
                if not line or line.isupper() or 'FAQ' in line:
                    continue

                if line.endswith('?'):
                    if current_faq["question"] and current_faq["answer"]:
                        faqs.append(current_faq)
                        current_faq = {"question": "", "answer": ""}

                    line = re.sub(r"^[\d\.\)\s]+", "", line)
                    current_faq["question"] = line
                    collecting_answer = True

                elif collecting_answer:
                    if line.startswith("https"):
                        continue
                    current_faq["answer"] += line + " "

            if current_faq["question"] and current_faq["answer"]:
                faqs.append(current_faq)
                current_faq = {"question": "", "answer": ""}
                collecting_answer = False

        return faqs

    def load_faq_data(self):
        print("Extracting text from PDF...")
        pdf_text = self.extract_text_from_pdf_pymupdf()
        self.faqs = self.split_pdf_text_into_faqs(pdf_text)
        print(f"Found {len(self.faqs)} FAQs")
        # Print first few to verify
        for i, faq in enumerate(self.faqs[-5:]): # Print last 5 which should include new ones
            print(f"FAQ {len(self.faqs)-5+i}: Q: {faq['question']} | A: {faq['answer'][:50]}...")
            
        print("Computing embeddings...")
        faq_questions = [faq["question"] for faq in self.faqs]
        self.faq_embeddings = self.embed_sentences(faq_questions)

    def faq_search(self, user_question, top_n=4):
        user_embedding = self.embed_sentences([user_question])
        similarities = cosine_similarity(user_embedding, self.faq_embeddings)[0]
        top_indices = np.argsort(similarities)[-top_n:][::-1]
        
        results = []
        for i in top_indices:
            results.append({
                "question": self.faqs[i]["question"],
                "answer": self.faqs[i]["answer"],
                "score": similarities[i]
            })
        return results

if __name__ == "__main__":
    # Simulate paths
    ROOT_DIR = r"C:\Users\Rishichowdary-3925\Downloads\multi-agent-chatbot-lollypop-design-v3\Data"
    CLIENT = "lollypop_design"
    PDF_PATH = os.path.join(ROOT_DIR, CLIENT, "faq_data/Lollypop_Updated_FAQs_Jul24.pdf")
    UPLOADS_DIR = os.path.join(ROOT_DIR, CLIENT, "uploads")
    
    # We won't read/write cache files to avoid messing up the actual app, just in-memory test
    searcher = SearchNode(PDF_PATH, "dummy_embed.npz", "dummy_faq.json", UPLOADS_DIR)
    searcher.load_faq_data()
    
    query = "Who is Rishi?"
    print(f"\nQuerying: {query}")
    results = searcher.faq_search(query)
    for res in results:
        print(f"Score: {res['score']:.4f} | Q: {res['question']}")
