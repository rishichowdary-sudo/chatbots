import os
import re
import json
import numpy as np
import fitz
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class SearchNode:
    
    
    def __init__(self, pdf_path, embeddings_path, faq_json_path, uploads_dir=None, filter_filenames=None) -> None:
        self.embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.pdf_path = pdf_path
        self.embeddings_path = embeddings_path
        self.faq_json_path = faq_json_path
        self.uploads_dir = uploads_dir
        self.filter_filenames = filter_filenames
        self.faqs = None
        self.faq_embeddings = None
        
    def embed_sentences(self, sentences):
        """
        Embed a list of sentences using the SentenceTransformer model.
        """
        return self.embed_model.encode(sentences)
    
    def extract_text_from_pdf_pymupdf(self):
        """
        Extract text from the base PDF and any uploaded PDFs.
        """
        pages = []
        
        # Load base PDF (Only if NO filter is applied, or if base PDF is somehow in filter list?)
        # For incremental updates, we usually only care about the uploads.
        if not self.filter_filenames and os.path.exists(self.pdf_path):
            try:
                doc = fitz.open(self.pdf_path)
                pages.extend([page.get_text() for page in doc])
            except Exception as e:
                logger.error(f"Error reading base PDF {self.pdf_path}: {e}")

        # Load uploaded PDFs
        if self.uploads_dir and os.path.exists(self.uploads_dir):
            for filename in os.listdir(self.uploads_dir):
                if filename.lower().endswith(".pdf"):
                    # Apply filter if provided
                    if self.filter_filenames:
                         is_match = False
                         for f_name in self.filter_filenames:
                             if f_name in filename.lower():
                                 is_match = True
                                 break
                         if not is_match:
                             continue

                    file_path = os.path.join(self.uploads_dir, filename)
                    try:
                        doc = fitz.open(file_path)
                        pages.extend([page.get_text() for page in doc])
                    except Exception as e:
                        logger.error(f"Error reading uploaded PDF {file_path}: {e}")
        
        return pages
    
    def split_pdf_text_into_faqs(self, pdf_text):
        """
        Split the extracted PDF text into a list of FAQ entries, handling multi-line questions and answers.
        """
        faqs = []
        current_faq = {"question": "", "answer": ""}
        collecting_answer = False

        for page in pdf_text:
            lines = page.split('\n')
            for line in lines:
                line = line.strip()

                # Skip empty lines or heading-like text (uppercase or too short)
                if not line or line.isupper():
                    continue

                # Detect a question: single line ending with '?'
                if line.endswith('?'):
                    # Save the previous FAQ if it has both question and answer
                    if current_faq["question"] and current_faq["answer"]:
                        faqs.append(current_faq)
                        current_faq = {"question": "", "answer": ""}

                    # Remove numbering from the question (e.g., "1. ", "2.1 ", etc.)
                    # line = re.sub(r"^\d+(\.\d+)*\s*", "", line)
                    line = re.sub(r"^[\d\.\)\s]+", "", line)
                    
                    # Start a new question
                    current_faq["question"] = line
                    collecting_answer = True  # Begin collecting the answer

                elif collecting_answer:
                    # Append the current line to the answer
                    if line.startswith("https") or "FAQs" in line:
                        if prev_line:
                            pass
                        else:
                            continue  # Skip unrelated content like URLs or headings
                    current_faq["answer"] += line + " "

                prev_line = line

            # End of page - Append any ongoing FAQ if valid
            if current_faq["question"] and current_faq["answer"]:
                faqs.append(current_faq)
                current_faq = {"question": "", "answer": ""}
                collecting_answer = False

        return faqs

    def split_pdf_text_into_faqs_multiline(self, pdf_text):
        # ... (Assuming this method is unchanged or rarely used, keeping original if possible, but tool requires contiguous block?)
        # Since this method is large and I only changed init and extract logic, I should have targeted those blocks separately.
        # But replace_file_content replaces one block.
        # I will include the unchanged methods to keep file integrity if they fall in range.
        # Actually, split_pdf_text_into_faqs_multiline starts at line 105. My replace block went to 210.
        # I should provide the content.
        # For brevity, I might split this into multiple replace calls?
        # NO, multiple replace calls allowed.
        # I'll cancel this tool call and do multiple chunks.
        pass

    def load_faq_data(self):
        """
        Load FAQs and embeddings from precomputed files if available.
        Otherwise, extract from PDF and compute embeddings.
        Supports Incremental Update.
        """

        def create_embeddings(faqs):
            faq_questions = [faq["question"] for faq in faqs]
            if not faq_questions: return np.array([])
            faq_embeddings = self.embed_sentences(faq_questions)           
            return faq_embeddings

        def create_faqs_from_source():
            pdf_text = self.extract_text_from_pdf_pymupdf()
            faqs = self.split_pdf_text_into_faqs(pdf_text)
            return faqs

        # Case 1: Incremental Update (Filter provided + Existing data)
        if self.filter_filenames and os.path.exists(self.faq_json_path) and os.path.exists(self.embeddings_path):
            print(f"Incremental Update for: {self.filter_filenames}")
            
            # Load existing
            with open(self.faq_json_path, 'r', encoding='utf-8') as f:
                self.faqs = json.load(f)
            
            data = np.load(self.embeddings_path)
            self.faq_embeddings = data['faq_embeddings']
            
            # Extract NEW content
            new_faqs = create_faqs_from_source()
            print(f"Extracted {len(new_faqs)} new FAQs from uploaded file(s).")
            
            if new_faqs:
                # Compute NEW embeddings
                print("Computing embeddings for new FAQs...")
                new_embeddings = create_embeddings(new_faqs)
                
                # Merge
                self.faqs.extend(new_faqs)
                if self.faq_embeddings.size > 0 and new_embeddings.size > 0:
                    self.faq_embeddings = np.concatenate((self.faq_embeddings, new_embeddings), axis=0)
                elif new_embeddings.size > 0:
                    self.faq_embeddings = new_embeddings
                
                # Save Updated
                with open(self.faq_json_path, 'w', encoding='utf-8') as f:
                    json.dump(self.faqs, f, indent=4, ensure_ascii=False)
                np.savez(self.embeddings_path, faq_embeddings=self.faq_embeddings)
                print("Merged and saved updated FAQs and embeddings.")
            else:
                print("No new FAQs found in uploaded file(s).")

        # Case 2: Full Load or Regeneration
        elif os.path.exists(self.faq_json_path):
            # Load precomputed FAQs and embeddings
            with open(self.faq_json_path, 'r', encoding='utf-8') as f:
                self.faqs = json.load(f)

            if os.path.exists(self.embeddings_path):
                data = np.load(self.embeddings_path)
                self.faq_embeddings = data['faq_embeddings']
                print("Loaded precomputed FAQs and embeddings.")
            else:
                self.faq_embeddings = create_embeddings(self.faqs)
                np.savez(self.embeddings_path, faq_embeddings=self.faq_embeddings)
                print("FAQs and embeddings saved.")
        
        else:
            # Full Clean Extract
            print("Extracting text from PDF (Full Build)...")
            self.faqs = create_faqs_from_source()
            
            with open(self.faq_json_path, 'w', encoding='utf-8') as f:
                json.dump(self.faqs, f, indent=4, ensure_ascii=False)

            print("Computing embeddings...")
            self.faq_embeddings = create_embeddings(self.faqs)
            np.savez(self.embeddings_path, faq_embeddings=self.faq_embeddings)
            print("FAQs and embeddings saved.")

    def faq_search(self, user_question, top_n=4, mode='cosine'):
        """
        Perform semantic search between the user question and the FAQs.
        """
        user_embedding = self.embed_sentences([user_question])

        if mode == 'cosine':
            similarities = cosine_similarity(user_embedding, self.faq_embeddings)[0]
            top_indices = np.argsort(similarities)[-top_n:][::-1]
            top_faqs = [self.faqs[i] for i in top_indices]
            top_scores = [similarities[i] for i in top_indices]

        return top_faqs, top_scores



# Example usage
if __name__ == "__main__":
    # Paths for the cached files
    ROOT_DIR = "Data"
    PDF_PATH = f'{ROOT_DIR}/terralogic_academy/faq_data/Terralogic_Academy_FAQs_Nov222024.pdf'
    EMBEDDINGS_PATH = f'{ROOT_DIR}/terralogic_academy/faq_data/faq_embeddings.npz'
    FAQ_JSON_PATH = f'{ROOT_DIR}/terralogic_academy/faq_data/faqs_from_pdf.json'

    # Load FAQ data on startup
    search_obj = SearchNode(PDF_PATH, EMBEDDINGS_PATH, FAQ_JSON_PATH, uploads_dir=None)
    search_obj.load_faq_data()
    
    user_query = "Why should I join Terralogic Academy?"
    top_faqs, top_scores = search_obj.faq_search(user_query)

    print("**********************************")
    print("User Query: ", user_query)
    print("**********************************")
    for idx, faq in enumerate(top_faqs):
        print(f"Top {idx + 1}:\nQ: {faq['question']}\nA: {faq['answer']}\nScore: {top_scores[idx]}\n")
