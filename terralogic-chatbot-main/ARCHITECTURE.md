# Terralogic Chatbot - Simple Architecture Guide

## What Is This Project?

This is an **AI-powered chatbot** for the Terralogic company website. When visitors come to the website, they can chat with this bot to:
- Learn about Terralogic's services
- Get answers to frequently asked questions
- Search for job openings
- Submit project inquiries

Think of it like a smart receptionist that works 24/7 on the website!

---

## How Does It Work? (The Big Picture)

Imagine you walk into a company office:

1. **Receptionist greets you** → Introduction Agent
2. **You ask about services** → Service Agent answers your questions
3. **You ask about jobs** → Career Agent helps you find openings
4. **Manager coordinates everything** → Supervisor Agent decides who should help you

This chatbot works the same way, but online!

```
You → Chatbot Interface → Supervisor (decides) → Correct Agent → Answer Back to You
```

---

## Table of Contents

1. [What's Inside? (Project Structure)](#whats-inside-project-structure)
2. [The Main Players (Key Components)](#the-main-players-key-components)
3. [How a Conversation Works (Step-by-Step)](#how-a-conversation-works-step-by-step)
4. [The Brain of the Bot (AI Components)](#the-brain-of-the-bot-ai-components)
5. [Where Information is Stored (Databases & Files)](#where-information-is-stored-databases--files)
6. [Extra Features (Cool Stuff)](#extra-features-cool-stuff)
7. [How to Run It (Setup Guide)](#how-to-run-it-setup-guide)
8. [Technologies Used (Simple Explanation)](#technologies-used-simple-explanation)

---

## What's Inside? (Project Structure)

Let's look at the folder structure like organizing a filing cabinet:

```
terralogic-chatbot-main/
│
├── 📄 app.py                    # The main program - starts everything
├── 📄 requirements.txt          # List of software needed
├── 📄 Dockerfile                # Instructions to run in a container
│
├── ⚙️ Configuration Files        # Settings and preferences
│   ├── application_properties.yaml
│   └── client_properties.yaml
│
├── 📚 Data/                     # The chatbot's knowledge base
│   └── terralogic/
│       ├── system_prompts.ini           # Instructions for the AI
│       ├── faq_data/                    # FAQ documents
│       └── vectorstore.db/              # Searchable database of info
│
├── 🧠 src/                      # The chatbot's brain (main logic)
│   ├── graphs/                  # Conversation flow manager
│   ├── nodes/                   # Individual task handlers
│   ├── subgraphs/               # Specialized agents
│   └── tools/                   # External integrations (email, etc.)
│
├── 🛠️ utils/                    # Helper functions
│   ├── helper.py                # Common utilities
│   ├── Log_sql.py               # Saves conversation history
│   └── data_backup_runner.py    # Backs up data automatically
│
├── 📊 report/                   # Analytics dashboard
│   ├── Report.py                # Shows conversation statistics
│   └── conv_summarizer.py       # Summarizes conversations
│
├── 🎨 templates/                # Website pages (HTML)
│   └── index.html               # The chatbot interface
│
└── 🎨 static/                   # Images, styles, JavaScript
    ├── chatbot.js               # Chatbot UI behavior
    └── styles.css               # How it looks
```

---

## The Main Players (Key Components)

### 1. **app.py - The Control Center**

This is like the power switch that turns everything on.

**What it does:**
- Starts the web server
- Creates the chatbot brain (graph)
- Sets up scheduled tasks (backups, reports)
- Handles incoming messages from users

**Think of it as:** The main office manager who opens the building every morning.

---

### 2. **The Supervisor (Brain's Manager)**

Located in: `src/graphs/graph_v3.py`

**What it does:**
- Reads your message
- Decides which agent should respond
- Routes you to the right agent

**Example:**
- You say: "Hi" → Routes to **Introduction Agent**
- You say: "Tell me about your services" → Routes to **Service Agent**
- You say: "Are you hiring?" → Routes to **Career Agent**

**Think of it as:** A smart receptionist who knows exactly who can help you.

---

### 3. **The Three Agents (Specialists)**

#### A. Introduction Agent (`src/subgraphs/introduction_subgraph.py`)

**Job:** Greet visitors and collect basic info

**Conversation flow:**
```
Bot: "Hello! What's your name?"
You: "John"
Bot: "Nice to meet you, John! What's your email?"
You: "john@email.com"
Bot: "Great! How can I help you today?"
    [Explore Services] [Start a Project] [Looking for a Job]
```

---

#### B. Service Agent (`src/subgraphs/service_subgraph.py`)

**Job:** Answer questions about Terralogic's services

**How it answers your questions:**

**Method 1: Quick Match (2 seconds)**
- Looks through pre-written FAQs
- If your question matches → Instant answer!
- Example: "What is cloud computing?" → Matches FAQ → Quick answer

**Method 2: Smart Search (5 seconds)**
- If no FAQ match found
- Searches through company website data
- Uses AI to create a custom answer
- Example: "How can you help with AI projects?" → Custom answer using website info

**Think of it as:** A help desk with a quick reference guide AND the ability to research deeper questions.

---

#### C. Career Agent (`src/subgraphs/careers_subgraph.py`)

**Job:** Help job seekers

**What it can do:**
- Shows current job openings
- Filters jobs by keyword (e.g., "Python developer")
- Accepts job applications
- Sends your resume via email

**Example conversation:**
```
You: "Show me developer jobs"
Bot: [Lists 5 developer positions]
You: "I want to apply for Software Engineer"
Bot: "Please share your resume"
You: [Uploads resume]
Bot: "Application submitted! We'll contact you soon."
```

---

### 4. **Search Tools (The Library)**

Located in: `src/nodes/search.py` and `src/nodes/llm_driven.py`

#### **FAQ Search (Fast Path)**
- Like a cheat sheet with common questions
- Uses "embeddings" (math magic) to find similar questions
- Super fast: 0.1 seconds

#### **AI Search (Smart Path)**
- Like having an expert research assistant
- Searches through all company documents
- Creates custom answers
- Takes 2-5 seconds

**Visual:**
```
Your Question
    ↓
Is it in the FAQ?
    ↓ YES → Fast Answer (0.1s)
    ↓ NO
Search website data → AI creates answer (2-5s)
```

---

### 5. **Email Tools (The Mailroom)**

Located in: `src/tools/`

**What they do:**
- Validate email addresses (check if they're real)
- Send emails through Gmail
- Forward project inquiries
- Send job applications

**Files:**
- `email_Validator.py` - Checks if email format is correct
- `gmail.py` - Connects to Gmail
- `mail_sender.py` - Composes and sends emails

---

### 6. **Database (The Filing System)**

Located in: `application_db/`

**Three databases:**

1. **state_db** - Remembers conversations
   - "What did this user say 5 minutes ago?"
   - Allows context-aware responses

2. **log_db** - Tracks all interactions
   - Who used the chatbot?
   - What questions were asked?
   - Used for analytics

3. **report_app_db** - Analytics data
   - How many conversations today?
   - Most common questions?
   - Conversation summaries

**Think of it as:** Three filing cabinets - one for ongoing chats, one for history, one for statistics.

---

## How a Conversation Works (Step-by-Step)

Let's follow a real conversation:

### **Step 1: User Opens Chat**

```
User opens: https://terralogic.com/chatbot
→ Browser loads index.html
→ chatbot.js starts running
→ Ready to chat!
```

---

### **Step 2: User Sends First Message**

```
User types: "Hi"
↓
Browser sends to: /getresponses (API endpoint)
↓
Flask receives the message
↓
Passes to: terralogic_graph (the brain)
```

---

### **Step 3: Supervisor Analyzes**

```python
Supervisor reads: "Hi"
Checks mode: First message (mode = "introducing")
Decision: Send to Introduction Agent
```

---

### **Step 4: Introduction Agent Responds**

```
Introduction Agent:
- Sees this is a greeting
- Responds: "Hello! I'm here to help. What's your name?"
- Waits for name input
```

---

### **Step 5: User Provides Name**

```
User types: "Alex"
↓
Introduction Agent:
- Saves name: "Alex"
- Asks: "Nice to meet you, Alex! What's your email?"
```

---

### **Step 6: User Provides Email**

```
User types: "alex@example.com"
↓
email_Validator.py checks format ✓
↓
Introduction Agent:
- Saves email
- Shows options:
  [Explore Services] [Start a Project] [Looking for a Job]
- Changes mode to: "answering"
```

---

### **Step 7: User Clicks "Explore Services"**

```
User clicks: "Explore Services"
↓
Supervisor sees: next_node = "services"
↓
Routes to: Service Agent
```

---

### **Step 8: User Asks a Question**

```
User types: "What is cloud migration?"
↓
Service Agent:

  Step 8a: Try Fast Path
  ├─ search.py looks in FAQ database
  ├─ Finds match with 92% similarity
  └─ Returns FAQ answer (0.1 seconds) ✓

  OR (if no match)

  Step 8b: Use Smart Path
  ├─ llm_driven.py searches vectorstore
  ├─ Finds 5 relevant documents about cloud
  ├─ Sends to OpenAI GPT-4 with context
  └─ GPT creates custom answer (2 seconds)
```

---

### **Step 9: Response Sent Back**

```
Service Agent packages response:
{
  "chatbot_answer": "Cloud migration is...",
  "options": ["Learn More", "Start a Project", "Back to Menu"],
  "chatMessageOptions": [...]
}
↓
Flask sends to browser
↓
chatbot.js displays the message
↓
User sees the answer!
```

---

### **Step 10: Conversation Logged**

```
Log_sql.py saves to database:
- Session ID: "abc123"
- User: "Alex (alex@example.com)"
- Question: "What is cloud migration?"
- Answer: "Cloud migration is..."
- Timestamp: "2024-11-24 10:30:15"
```

---

## The Brain of the Bot (AI Components)

### **What is AI doing here?**

The chatbot uses two types of intelligence:

---

### **1. Pattern Matching (No AI Needed - Super Fast)**

**How it works:**
- Pre-written questions and answers stored in FAQ
- Uses math to find similar questions
- Like matching fingerprints

**Example:**
```
User asks: "What's your pricing?"
System converts to numbers: [0.2, 0.8, 0.3, 0.9, ...]
Compares with FAQ questions
Finds match: "How much do you charge?" (95% similar)
Returns pre-written answer
```

**Why it's good:** Super fast, no cost, consistent answers

---

### **2. AI Generation (Smart - Slower)**

**How it works:**
- Searches company documents (website, PDFs)
- Finds relevant information
- Sends to GPT-4 (OpenAI's AI)
- GPT creates a custom answer

**Example:**
```
User asks: "Can you help with AI integration in healthcare?"

Step 1: Search documents
- Found: "We work with healthcare clients"
- Found: "AI integration services include..."
- Found: "Case study: Hospital AI project"

Step 2: Send to GPT-4
"Based on these documents, answer: Can you help with AI integration in healthcare?"

Step 3: GPT responds
"Yes! Terralogic specializes in AI integration for healthcare..."
```

**Why it's good:** Can answer ANY question, very flexible, sounds natural

---

### **Visual: Two-Path Strategy**

```
                    Your Question
                         ↓
              ┌──────────┴──────────┐
              ↓                     ↓
         [Fast Path]            [Smart Path]
              ↓                     ↓
      Check FAQ Match        Search Documents
         (0.1 sec)               (1 sec)
              ↓                     ↓
        Match > 85%?          Send to GPT-4
              ↓                   (2 sec)
        YES → Return                ↓
              ↓               Custom Answer
      NO → Go to Smart Path        ↓
                              Return Answer
```

**Result:** 60% of questions use Fast Path = Faster responses + Lower costs!

---

## Where Information is Stored (Databases & Files)

### **1. Knowledge Base (Data/terralogic/)**

This is what the chatbot "knows":

#### **A. FAQ Document**
- File: `faq_data/Terralogic_FAQ_July24.pdf`
- Contains: Common questions and answers
- Example: "What services do you offer?"

#### **B. FAQ Embeddings**
- File: `faq_data/faq_embeddings.npz`
- Contains: Math representations of questions
- Used for: Fast matching

#### **C. Website Data (Vector Store)**
- Folder: `vectorstore.db/`
- Contains: All text from terralogic.com
- Searchable: AI can find relevant info quickly

---

### **2. Conversation Databases**

#### **A. State Database** (`application_db/state_db/`)

Stores: Active conversations

```
Session: abc123
Messages:
  - User: "Hi"
  - Bot: "Hello! What's your name?"
  - User: "Alex"
  - Bot: "Nice to meet you, Alex!"

Current State:
  - name: "Alex"
  - email: "pending"
  - mode: "introducing"
```

**Why?** So the bot remembers what you said 2 minutes ago!

---

#### **B. Log Database** (`application_db/log_db/`)

Stores: All interactions (forever)

```
| Session | Name | Email          | Question          | Answer          | Time      |
|---------|------|----------------|-------------------|-----------------|-----------|
| abc123  | Alex | alex@email.com | What is cloud?    | Cloud is...     | 10:30:15  |
| abc123  | Alex | alex@email.com | Your pricing?     | Our pricing...  | 10:31:22  |
| xyz789  | Sara | sara@email.com | Job openings?     | Here are 5...   | 11:15:03  |
```

**Why?** For analytics and improving the bot!

---

#### **C. Report Database** (`application_db/report_app_db/`)

Stores: Summary statistics

```
Today's Stats:
- Total conversations: 47
- Average messages per chat: 8.3
- Most asked topic: "Cloud Services"
- Conversion rate: 12% (users who submitted inquiries)
```

**Why?** To track performance and user behavior!

---

### **3. Configuration Files (The Settings)**

#### **client_properties.yaml** - Chatbot personality

```yaml
terralogic:
  URL: "https://terralogic.com/"
  FAQ_SEARCH_THRESH: 0.85        # 85% match required for FAQ
  CAREER_URL: "https://terralogic.com/careers/"
```

**Translation:** "Only use FAQ answer if 85% sure it matches"

---

#### **application_properties.yaml** - Where to save things

```yaml
STATE_DB_PATH: 'application_db/state_db'
LOG_DB_PATH: 'application_db/log_db'
```

**Translation:** "Save conversations in these folders"

---

#### **.env** - Secret keys (not in code)

```
OPENAI_API_KEY=sk-xxxxx        # To use GPT-4
App_SCREAT_KEY=secret123       # Security key
ALLOWED_IP=127.0.0.1:5000      # Who can access
```

**Translation:** Sensitive information kept separately

---

## Extra Features (Cool Stuff)

### **1. Automated Backups**

**What happens:** Every 24 hours automatically

```
Backup Runner starts
↓
Copies all databases
↓
Uploads to cloud:
  - Google Cloud Storage
  - Amazon S3
  - Akamai Storage
↓
"Backup successful!"
```

**Why?** So data is never lost, even if server crashes!

---

### **2. Report Generation**

**What happens:** Every 3 hours automatically

```
Report Generator starts
↓
Reads all recent conversations
↓
AI summarizes patterns:
  - Common questions
  - User satisfaction
  - Topics discussed
↓
Saves to report database
↓
Viewable at: /report dashboard
```

**Why?** To understand what users need and improve the bot!

---

### **3. Security Features**

#### **A. Input Sanitization**
```python
User input: "<script>alert('hack')</script>"
After sanitization: "scriptalert('hack')/script"
```
**Why?** Prevents hackers from injecting malicious code!

---

#### **B. IP Whitelisting**
```python
Only allow traffic from: 127.0.0.1:5000
Block everyone else
```
**Why?** Only trusted sources can access!

---

#### **C. Email Validation**
```python
Check format: user@domain.com ✓
Check DNS: domain.com exists ✓
```
**Why?** Ensures email addresses are real!

---

## How to Run It (Setup Guide)

### **Step 1: Install Python**

Make sure Python 3.12 is installed on your computer.

```bash
python --version
# Should show: Python 3.12.x
```

---

### **Step 2: Download the Code**

```bash
cd C:\Users\Rishichowdary-3925\Downloads\terralogic-chatbot-main
```

---

### **Step 3: Create Virtual Environment**

Think of this as a clean workspace just for this project.

```bash
python -m venv venv
venv\Scripts\activate    # Windows
```

You'll see `(venv)` appear in your terminal.

---

### **Step 4: Install Requirements**

This installs all the software the chatbot needs.

```bash
pip install -r requirements.txt
```

Takes 2-5 minutes. Installs things like:
- Flask (web server)
- OpenAI library (for GPT)
- LangChain (AI framework)

---

### **Step 5: Create .env File**

Create a file named `.env` with your API keys:

```
OPENAI_API_KEY=your-key-here
App_SCREAT_KEY=any-random-secret
ALLOWED_IP=127.0.0.1:5000
ALLOWED_DOMAIN=terralogic
```

---

### **Step 6: Setup Knowledge Base**

This creates the FAQ database and website search index.

```bash
python src/setup.py -n terralogic
```

What it does:
- Reads FAQ PDF
- Creates embeddings
- Crawls terralogic.com
- Builds searchable database

Takes 5-10 minutes.

---

### **Step 7: Run the Chatbot**

```bash
python app.py
```

You'll see:
```
* Running on http://127.0.0.1:5000/
* Press CTRL+C to quit
```

---

### **Step 8: Open in Browser**

Go to: `http://127.0.0.1:5000/terralogic`

You should see the chatbot interface!

---

### **For Docker (Advanced)**

If you want to run in a container:

```bash
docker build -t terralogic-chatbot .
docker run -p 8002:8002 --env-file .env terralogic-chatbot
```

Access at: `http://localhost:8002/terralogic`

---

## Technologies Used (Simple Explanation)

### **Backend (Server-side)**

| Technology | What it does | Real-world analogy |
|------------|--------------|-------------------|
| **Flask** | Web server that handles requests | Restaurant kitchen |
| **Gunicorn** | Makes Flask faster for many users | More cooks in the kitchen |
| **Python** | Programming language | The language we write instructions in |

---

### **AI/Machine Learning**

| Technology | What it does | Real-world analogy |
|------------|--------------|-------------------|
| **OpenAI GPT-4** | AI that generates human-like text | Expert writer |
| **LangChain** | Framework for building AI apps | Toolbox for AI projects |
| **LangGraph** | Manages conversation flow | Traffic controller |
| **Sentence Transformers** | Converts text to numbers | Translator |
| **FAISS** | Super-fast search | Google for your data |

---

### **Data Storage**

| Technology | What it does | Real-world analogy |
|------------|--------------|-------------------|
| **SQLite** | Database for conversations | Filing cabinet |
| **Google Cloud Storage** | Cloud backup | Safe deposit box |
| **FAISS Vector Store** | Searchable knowledge base | Library index system |

---

### **Web Scraping**

| Technology | What it does | Real-world analogy |
|------------|--------------|-------------------|
| **BeautifulSoup** | Reads website content | Web page reader |
| **PyMuPDF** | Reads PDF files | PDF reader |

---

### **Utilities**

| Technology | What it does | Real-world analogy |
|------------|--------------|-------------------|
| **APScheduler** | Runs tasks automatically | Alarm clock |
| **Bleach** | Cleans dangerous input | Security guard |
| **Pandas** | Analyzes data | Spreadsheet |

---

## Common Questions (Troubleshooting)

### **Q: "The bot gives wrong answers!"**

**Solution:**
1. Check if FAQ is up to date: `Data/terralogic/faq_data/`
2. Re-run setup: `python src/setup.py -n terralogic`
3. Check logs: `application_logs/`

---

### **Q: "Error: OpenAI API key not found"**

**Solution:**
1. Check `.env` file exists
2. Verify `OPENAI_API_KEY=sk-xxxxx` is present
3. Make sure no spaces around `=`

---

### **Q: "Bot is very slow"**

**Possible causes:**
- Internet connection slow (GPT-4 needs internet)
- FAQ threshold too low (change to 0.90 in client_properties.yaml)
- Too many users at once (use more Gunicorn workers)

---

### **Q: "How do I add new FAQs?"**

**Steps:**
1. Update PDF: `Data/terralogic/faq_data/Terralogic_FAQ_July24.pdf`
2. Re-run: `python src/setup.py -n terralogic`
3. Restart: `python app.py`

---

### **Q: "Where are the logs?"**

**Locations:**
- Application logs: `application_logs/`
- Conversation history: `application_db/log_db/Log.db`
- Current sessions: `application_db/state_db/`

---

### **Q: "How do I add a new client?"**

**Steps:**
1. Add to `client_properties.yaml`:
```yaml
newcompany:
  URL: "https://newcompany.com/"
  CLIENT_NAME: "newcompany"
  ...
```
2. Create folder: `Data/newcompany/`
3. Run setup: `python src/setup.py -n newcompany`
4. Update `app.py` to handle new client_id

---

## Performance Tips

### **Make it Faster:**

1. **Increase FAQ threshold**
   - Change `FAQ_SEARCH_THRESH: 0.85` to `0.90`
   - More questions use fast path

2. **Use smaller AI model**
   - Change `gpt-4o-mini` instead of `gpt-4`
   - Faster responses, lower cost

3. **Pre-compute more answers**
   - Add more FAQs to the PDF
   - Less AI generation needed

4. **Add more server workers**
   - Edit Dockerfile: `gunicorn --workers=4`
   - Handles more users simultaneously

---

## Visual Summary: How Everything Connects

```
┌─────────────────────────────────────────────────────┐
│                   USER'S BROWSER                    │
│              (Sees chatbot interface)               │
└──────────────────────┬──────────────────────────────┘
                       │
                  [Internet]
                       │
┌──────────────────────▼──────────────────────────────┐
│                    FLASK APP                        │
│                   (app.py)                          │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                  SUPERVISOR                         │
│           (Decides who handles request)             │
└──────┬────────────────┬─────────────────┬───────────┘
       │                │                 │
   ┌───▼────┐     ┌────▼─────┐     ┌─────▼────┐
   │ Intro  │     │ Service  │     │  Career  │
   │ Agent  │     │  Agent   │     │  Agent   │
   └───┬────┘     └────┬─────┘     └─────┬────┘
       │                │                 │
       └────────────────┼─────────────────┘
                        │
       ┌────────────────┼────────────────┐
       │                │                │
   ┌───▼────┐     ┌────▼─────┐     ┌───▼────┐
   │  FAQ   │     │   AI     │     │ Email  │
   │ Search │     │  (GPT)   │     │  Tool  │
   └───┬────┘     └────┬─────┘     └───┬────┘
       │                │                │
   ┌───▼────────────────▼────────────────▼────┐
   │             DATA STORAGE                  │
   │  - Conversation Database                  │
   │  - Knowledge Base (FAQs, Website)         │
   │  - Log Database                           │
   └───────────────────────────────────────────┘
```

---

## Final Notes

### **What Makes This Chatbot Special?**

1. **Smart Routing**: Knows which agent to use automatically
2. **Two-Speed Answers**: Fast for common questions, smart for complex ones
3. **Memory**: Remembers your conversation context
4. **Multi-Purpose**: Handles services, careers, and inquiries
5. **Self-Managing**: Auto-backups and reporting
6. **Secure**: Multiple security layers

### **Where to Learn More**

- **LangChain Docs**: https://python.langchain.com/
- **OpenAI API**: https://platform.openai.com/docs
- **Flask Tutorial**: https://flask.palletsprojects.com/

### **Need Help?**

- Check logs: `application_logs/`
- Read error messages carefully
- Update FAQ if questions are wrong
- Reach out to the development team

---

**Document Created:** 2024-11-24
**Version:** 2.0 (Simplified Edition)
**Made Easy to Understand!** ✓

---

## Quick Reference Card

### **Start the Bot**
```bash
cd terralogic-chatbot-main
venv\Scripts\activate
python app.py
```

### **View Logs**
```bash
cd application_logs
notepad chatbot.log
```

### **Update Knowledge Base**
```bash
python src/setup.py -n terralogic
```

### **Backup Data**
```bash
python utils/data_backup_runner.py
```

### **View Reports**
Go to: `http://127.0.0.1:5000/report`

---

That's it! You now understand the entire architecture! 🎉
