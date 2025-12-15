# Admin Portal - Technical Architecture Overview

This document explains **what** we'll build and **how** the pieces fit together, without diving into code details.

**Updated Based on Management Feedback:**
- ✅ Production-ready database (PostgreSQL)
- ✅ Modern async framework (FastAPI))
- ✅ Unified identity management across multiple user sources
- ✅ Bring Your Own API Key (BYOK) with encryption

---

## Executive Summary

**What We're Building:**
A web-based control panel to manage all chatbots from one place.

**Technology Used:**
- **Frontend:** React (modern UI framework, component-based)
- **Backend:** FastAPI (modern, fast, production-ready)
- **Database:** PostgreSQL (enterprise-grade, scalable)
- **Identity:** Unified user management (supports multiple sources)
- **Security:** BYOK with AES-256 encryption

**Timeline:**
8-10 weeks for full version, or 3-4 weeks for basic version.

---

## System Architecture

### Current Setup (Before Admin Portal)

```
You manage 4 separate chatbots:

┌────────────────┐   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
│   Lollypop     │   │   Lollypop     │   │  Terralogic    │   │  Terralogic    │
│    Design      │   │   Academy      │   │                │   │   Academy      │
│   Chatbot      │   │   Chatbot      │   │   Chatbot      │   │   Chatbot      │
└────────────────┘   └────────────────┘   └────────────────┘   └────────────────┘

To manage each one:
- Open terminal
- Run commands manually
- Edit files individually
- Check logs separately
```

**Problem:** Managing 4 chatbots = 4x the work!

---

### New Setup (With Admin Portal)

```
                    ┌──────────────────────────┐
                    │   ADMIN PORTAL           │
                    │   (Web Interface)        │
                    │   One place to control   │
                    └────────────┬─────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
    ┌───────▼────────┐   ┌──────▼──────┐   ┌────────▼──────┐
    │  Lollypop      │   │ Terralogic  │   │   Lollypop    │
    │   Design       │   │             │   │   Academy     │
    │   Chatbot      │   │  Chatbot    │   │   Chatbot     │
    └────────────────┘   └─────────────┘   └───────────────┘
```

**Solution:** One web interface controls everything!

---

## Technology Stack (What We're Using)

### 1. Programming Languages

| Language | Purpose | Already Used? |
|----------|---------|---------------|
| **Python** | Backend API logic | ✅ Yes (current chatbots use it) |
| **JavaScript (React)** | Frontend UI framework | ⚠️ Partial (basic JS used in chatbot) |
| **JSX** | React component syntax | ❌ New (for admin portal) |
| **CSS** | Styling | ✅ Yes (chatbot interface uses it) |
| **SQL** | Database queries | ✅ Yes (for conversations) |
| **TypeScript** | Optional type safety | ❌ Optional (can add later) |



---

### 2. Frameworks & Libraries (UPDATED)

**Backend:**

| Framework | Purpose | Why We Use It |
|-----------|---------|---------------|
| **FastAPI** | Backend framework | Modern, fast, async support built-in |
| **PostgreSQL** | Database | Production-ready, scales well |
| **SQLAlchemy** | ORM | Database models and queries |
| **APScheduler** | Background tasks | Simple, no Redis needed |
| **Cryptography** | Encryption | AES-256 for API key storage |
| **PyJWT** | Authentication | JWT token generation/validation |
| **Uvicorn** | ASGI server | High-performance async server |

**Frontend:**

| Framework | Purpose | Why We Use It |
|-----------|---------|---------------|
| **React** | UI framework | Component-based, fast, popular |
| **Redux Toolkit** | State management | Centralized state, predictable updates |
| **React Router** | Routing | Client-side navigation |
| **Axios** | HTTP client | API requests with interceptors |
| **Material-UI** | UI components | Professional, accessible components |
| **Chart.js** | Data visualization | Dashboard charts and graphs |
| **React Query** | Data fetching | Caching, real-time updates |

---

### 3. Infrastructure (UPDATED)

| Component | What It Does | Cost |
|-----------|--------------|------|
| **Same Server** | Runs admin portal + chatbots | No additional cost |
| **PostgreSQL** | Production database | Free (open source) |



---

## System Components (UPDATED)

### Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     ADMIN PORTAL SYSTEM                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐         ┌─────────────────────┐       │
│  │  FRONTEND (React)   │         │  BACKEND (FastAPI)  │       │
│  │  Port: 3000         │◄───────►│  Port: 8000         │       │
│  │                     │  REST   │                     │       │
│  │ - React Components  │  API    │ - API Routes        │       │
│  │ - Redux State       │  (JSON) │ - Business Logic    │       │
│  │ - React Router      │         │ - Auth (JWT)        │       │
│  │ - Axios Client      │         │ - BYOK Service      │       │
│  │ - Material-UI       │         │ - Identity Resolver │       │
│  │ - Real-time Updates │         │ - Async Tasks       │       │
│  └─────────────────────┘         └──────────┬──────────┘       │
│                                              │                  │
│                                              │ SQL              │
│                                              ▼                  │
│                                   ┌──────────────────┐         │
│                                   │  PostgreSQL DB   │         │
│                                   │                  │         │
│                                   │ - Users          │         │
│                                   │ - Identities     │         │
│                                   │ - Keys (AES-256) │         │
│                                   │ - Audit logs     │         │
│                                   │ - Chatbot config │         │
│                                   └──────────────────┘         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Controls
                                    ▼
                ┌───────────────────────────────────┐
                │    EXISTING CHATBOT SYSTEM         │
                │    (Flask - Port: 5000)           │
                │    (No changes to current code)   │
                └───────────────────────────────────┘
```

---

## File Structure (What Gets Created)

### New Folders: `admin_portal_backend/` + `admin_portal_frontend/`

This structure properly separates frontend (React) from backend (FastAPI):

```
terralogic-chatbot-main/          ← Your existing project
│
├── app.py                         ← Existing (tiny modification)
├── src/                           ← Existing (no changes)
├── Data/                          ← Existing (no changes)
│
├── admin_portal_backend/          ← NEW: BACKEND FOLDER (FastAPI)
│   │
│   ├── main.py                    ← FastAPI entry point
│   │
│   ├── api/                       ← API routes (REST endpoints)
│   │   ├── __init__.py
│   │   ├── auth.py                   • POST /api/auth/login, /logout, /sso
│   │   ├── dashboard.py              • GET /api/dashboard/stats
│   │   ├── clients.py                • GET/POST/PUT/DELETE /api/clients
│   │   ├── documents.py              • POST /api/documents/upload
│   │   ├── indexing.py               • POST /api/indexing/start
│   │   ├── keys.py                   • GET/POST/DELETE /api/keys (BYOK)
│   │   ├── identity.py               • GET/POST /api/identity/link
│   │   └── testing.py                • POST /api/tests/run
│   │
│   ├── models/                    ← Database models (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── user.py                   • User table model
│   │   ├── identity.py               • Identity mappings model
│   │   ├── client.py                 • Chatbot clients model
│   │   └── encryption.py             • Encrypted keys model
│   │
│   ├── core/                      ← Core business logic
│   │   ├── __init__.py
│   │   ├── identity_resolver.py      • Merge multiple user sources
│   │   ├── encryption_service.py     • AES-256 encryption/decryption
│   │   ├── auth_service.py           • JWT token management
│   │   └── indexing_service.py       • Background indexing tasks
│   │
│   ├── config/                    ← Configuration
│   │   ├── __init__.py
│   │   ├── database.py               • PostgreSQL connection pool
│   │   └── settings.py               • Environment variables
│   │
│   ├── middleware/                ← Request/response handling
│   │   ├── __init__.py
│   │   ├── cors.py                   • CORS configuration
│   │   └── auth.py                   • JWT verification
│   │
│   ├── requirements.txt           ← Python dependencies
│   └── .env.example               ← Environment variables template
│
│
└── admin_portal_frontend/         ← NEW: FRONTEND FOLDER (React)
    │
    ├── public/                    ← Static assets
    │   ├── index.html                • Main HTML template
    │   ├── favicon.ico
    │   └── logo.png
    │
    ├── src/                       ← React source code
    │   │
    │   ├── components/            ← Reusable UI components
    │   │   ├── Layout/
    │   │   │   ├── Header.jsx        • Top navigation bar
    │   │   │   ├── Sidebar.jsx       • Side menu
    │   │   │   └── Layout.jsx        • Main layout wrapper
    │   │   │
    │   │   ├── Auth/
    │   │   │   ├── LoginForm.jsx     • Login form component
    │   │   │   ├── SSOButton.jsx     • SSO login buttons
    │   │   │   └── ProtectedRoute.jsx • Auth guard
    │   │   │
    │   │   ├── Dashboard/
    │   │   │   ├── StatsCard.jsx     • Statistics display
    │   │   │   ├── ActivityChart.jsx • Usage charts
    │   │   │   └── QuickActions.jsx  • Action buttons
    │   │   │
    │   │   ├── Clients/
    │   │   │   ├── ClientList.jsx    • Chatbot list table
    │   │   │   ├── ClientCard.jsx    • Individual chatbot card
    │   │   │   └── ClientForm.jsx    • Add/edit chatbot form
    │   │   │
    │   │   ├── Documents/
    │   │   │   ├── FileUpload.jsx    • Drag-drop upload
    │   │   │   ├── FileList.jsx      • Document list
    │   │   │   └── UploadProgress.jsx • Upload progress bar
    │   │   │
    │   │   ├── Keys/
    │   │   │   ├── KeyList.jsx       • API keys list (BYOK)
    │   │   │   ├── AddKeyForm.jsx    • Add new key form
    │   │   │   └── KeyCard.jsx       • Key display (masked)
    │   │   │
    │   │   ├── Indexing/
    │   │   │   ├── IndexingStatus.jsx • Real-time status
    │   │   │   ├── ProgressBar.jsx   • Indexing progress
    │   │   │   └── IndexingLogs.jsx  • Log viewer
    │   │   │
    │   │   ├── Testing/
    │   │   │   ├── TestRunner.jsx    • Test execution UI
    │   │   │   ├── TestResults.jsx   • Results display
    │   │   │   └── TestCase.jsx      • Individual test case
    │   │   │
    │   │   └── Common/
    │   │       ├── Button.jsx        • Styled button
    │   │       ├── Input.jsx         • Form input
    │   │       ├── Modal.jsx         • Modal dialog
    │   │       ├── Table.jsx         • Data table
    │   │       └── Loader.jsx        • Loading spinner
    │   │
    │   ├── pages/                 ← Page components (routes)
    │   │   ├── LoginPage.jsx         • /login
    │   │   ├── DashboardPage.jsx     • /dashboard
    │   │   ├── ClientsPage.jsx       • /clients
    │   │   ├── DocumentsPage.jsx     • /documents
    │   │   ├── KeysPage.jsx          • /keys
    │   │   ├── IndexingPage.jsx      • /indexing
    │   │   ├── TestingPage.jsx       • /testing
    │   │   └── NotFoundPage.jsx      • 404 page
    │   │
    │   ├── services/              ← API client services
    │   │   ├── api.js                • Axios instance with interceptors
    │   │   ├── authService.js        • Login, logout, token refresh
    │   │   ├── clientService.js      • Chatbot CRUD operations
    │   │   ├── documentService.js    • File upload operations
    │   │   ├── indexingService.js    • Indexing operations
    │   │   ├── keyService.js         • API key operations (BYOK)
    │   │   └── testService.js        • Test operations
    │   │
    │   ├── store/                 ← State management (Redux/Context)
    │   │   ├── authSlice.js          • Auth state
    │   │   ├── clientsSlice.js       • Clients state
    │   │   ├── dashboardSlice.js     • Dashboard state
    │   │   └── store.js              • Redux store configuration
    │   │
    │   ├── hooks/                 ← Custom React hooks
    │   │   ├── useAuth.js            • Authentication hook
    │   │   ├── useClients.js         • Clients data hook
    │   │   ├── useWebSocket.js       • Real-time updates hook
    │   │   └── useFileUpload.js      • File upload hook
    │   │
    │   ├── utils/                 ← Utility functions
    │   │   ├── constants.js          • App constants
    │   │   ├── validators.js         • Form validation
    │   │   ├── formatters.js         • Data formatting
    │   │   └── helpers.js            • Helper functions
    │   │
    │   ├── styles/                ← Global styles
    │   │   ├── global.css            • Global CSS
    │   │   ├── variables.css         • CSS variables (colors, fonts)
    │   │   └── theme.js              • Theme configuration
    │   │
    │   ├── App.jsx                ← Main App component
    │   ├── index.js               ← React entry point
    │   └── routes.js              ← Route configuration
    │
    ├── package.json               ← Node dependencies
    ├── .env.example               ← Frontend env variables template
    ├── .gitignore
    └── README.md                  ← Frontend setup instructions
```

**Total New Files:** ~65 files (30 backend + 35 frontend)




**Impact on Existing Code:** Minimal (1 file modified: app.py)

---

## Database Design (UPDATED TO POSTGRESQL)

### New Database: `admin_portal` (PostgreSQL)

**Why PostgreSQL?**
- Production-ready (used by Instagram, Uber, Netflix)
- Handles millions of records easily
- Better for multi-user access
- ACID compliant (no data loss)
- Better performance than SQLite

**Tables Created:**

| Table Name | Purpose | Example Data |
|------------|---------|--------------|
| **users** | Primary user accounts | john@company.com (active) |
| **user_identities** | Multiple identity mappings | john@company.com = john_ldap = john_oauth |
| **identity_providers** | Where users come from | LDAP, OAuth, Local, SSO |
| **user_api_keys** | Each user's own keys (encrypted) | John's OpenAI key (encrypted) |
| **clients** | List of chatbots | Lollypop Design (active) |
| **indexing_jobs** | Track indexing | Job #123 (75% complete) |
| **document_uploads** | File history | FAQ_v2.pdf (uploaded by John) |
| **test_cases** | Automated tests | Test greeting (passed) |
| **test_results** | Test outcomes | 15/17 tests passed |
| **audit_log** | Who did what | John uploaded file at 2pm |


**New Tables Explained:**

**1. user_identities** - The Identity Merger
```
Problem: John has 3 identities:
- john@company.com (local account)
- john.doe (LDAP username)
- john_oauth (Google SSO)

Solution: Link them all to ONE user
```

**2. identity_providers** - Where Users Come From
```
Supported sources:
- Local (database)
- LDAP (Active Directory)
- OAuth (Google, Microsoft)
- SAML (SSO)
```

**3. user_api_keys** - Bring Your Own Key (BYOK)
```
Old way: Everyone shares one OpenAI key
Problem: Can't track who uses what, security risk

New way: Each user brings their own key
Benefits:
- Personal usage tracking
- No shared credentials
- User controls their own costs
```

**Database Size:** Starts at ~50 MB, grows to 1-2 GB with usage

---

## Key New Features Based on Feedback

### Feature 1: Production-Ready Database (PostgreSQL)

**Why It Matters:**

**Scenario: 10 Admins Using Portal Simultaneously**


---

### Feature 2: FastAPI Instead of Flask + Celery + Redis



---

### Feature 3: Unified Identity Management

**What Is This?**

  company might have users in multiple systems:
- Active Directory (LDAP)
- Google Workspace (OAuth)
- Local database
- SSO provider

**Problem:**
Same person = different usernames in different systems

**Example:**
```
John Smith works at your company:
- LDAP username: jsmith
- Email: john.smith@company.com
- Google OAuth: john.s@company.com
- Local account: john_admin

Question: Are these 4 different people or 1 person?
Answer: 1 person with 4 identities!
```

**Solution: Identity Resolver**

**How It Works:**

**Step 1: User Logs In**
```
John logs in with Google OAuth
↓
System gets: john.s@company.com
↓
Checks identity_mappings table
↓
Finds: john.s@company.com → User ID: 42
↓
Loads user: John Smith (ID: 42)
```

**Step 2: Link New Identity**
```
John also has LDAP account: jsmith
↓
System detects: Same email domain
↓
Admin confirms: Link to John Smith?
↓
Creates mapping: jsmith → User ID: 42
↓
Now John can login with LDAP too!
```

**Benefits:**
- Single user profile (not duplicates)
- Login with any identity
- Centralized permissions
- Better audit trails

**Database Structure:**

```sql
users table:
- id: 42
- primary_email: john.smith@company.com
- name: John Smith
- role: admin

user_identities table:
- user_id: 42, identity: "john.smith@company.com", provider: "local"
- user_id: 42, identity: "john.s@company.com", provider: "google_oauth"
- user_id: 42, identity: "jsmith", provider: "ldap"
- user_id: 42, identity: "john_admin", provider: "local"

All 4 identities → Same user (ID: 42)
```

---

### Feature 4: Bring Your Own API Key (BYOK)

**What Changed:**
- **Old:** One shared OpenAI key for everyone
- **New:** Each user brings their own API keys

**Why This Matters:**

**Old Way (Shared Key):**
```
Company OpenAI Account:
- API Key: sk-shared-key-123
- Used by: Everyone
- Cost: $500/month
- Problem: Who used how much? Can't tell!

Security Risk:
- One person leaks key → Everyone's access compromised
- Can't revoke individual access
- No accountability
```

**New Way (BYOK):**
```
John's Keys:
- OpenAI: sk-john-key-456 (encrypted in DB)
- LangChain: lc-john-key-789 (encrypted in DB)
- Used by: Only John
- Cost: John's own account
- Benefit: Personal usage tracking!

Sarah's Keys:
- OpenAI: sk-sarah-key-101 (encrypted in DB)
- LangChain: lc-sarah-key-202 (encrypted in DB)
- Used by: Only Sarah
- Cost: Sarah's own account
```

**How It Works:**

**Step 1: User Adds Key**
```
1. John logs into admin portal
2. Goes to "My API Keys"
3. Clicks "Add Key"
4. Enters: OpenAI API Key = sk-john-secret-key
5. System encrypts: AES-256 encryption
6. Stores encrypted version in database
7. Shows: sk-****-key (masked)
```

**Step 2: System Uses Key**
```
1. John triggers indexing for Lollypop chatbot
2. System retrieves John's encrypted OpenAI key
3. Decrypts in memory (never saved decrypted)
4. Uses for indexing
5. Clears from memory
6. Logs: "John used OpenAI key at 2pm"
```

**Step 3: Key Security**
```
Database stores:
encrypted_key = "gAAAAABh3xK9..." (unreadable)

To decrypt, need:
- Encryption master key (stored in environment variable)
- User's record (can't decrypt others' keys)
- Valid session (must be logged in)

If database is stolen:
- Keys are encrypted (useless without master key)
- Master key not in database (stored separately)
- Attacker can't use the keys
```

**Encryption Implementation:**

**Algorithm:** AES-256-GCM (industry standard)

**How Strong?**
- Used by: US Government, banks, military
- Strength: Would take billions of years to crack
- Standard: NIST approved

**Key Storage:**
```
User's API Key (plaintext): sk-john-secret-key
↓
Encrypt with master key
↓
Database stores: gAAAAABh3xK9rL8vQ... (gibberish)
↓
Even if database stolen, keys are safe
```

**Master Key Location:**
- NOT in database
- NOT in code
- Stored in: Environment variable or Key Management Service (KMS)
- Only admin portal has access

**Benefits:**
- **Security:** Each user controls their own keys
- **Accountability:** Track who uses what
- **Cost control:** Users manage their own API costs
- **Revocation:** Easy to remove one user's access
- **Compliance:** Better audit trails

---

## Architecture Layers (UPDATED)

### 3-Tier Architecture

```
┌───────────────────────────────────────────────────────┐
│         PRESENTATION LAYER (REACT)                     │
│         (What users see)                              │
│                                                       │
│  • React Components (JSX)                             │
│  • Material-UI (Professional styling)                 │
│  • Redux Store (State management)                     │
│  • React Router (Client-side routing)                 │
│  • Charts.js (Data visualization)                     │
│  • Axios (HTTP client)                                │
│  • WebSocket (Real-time updates)                      │
└────────────────────────┬──────────────────────────────┘
                         │
                         │ REST API (JSON)
                         │ HTTPS + JWT Bearer Token
                         │ WebSocket for real-time
                         │
┌────────────────────────▼──────────────────────────────┐
│         APPLICATION LAYER (FASTAPI)                    │
│         (Business logic)                              │
│                                                       │
│  • FastAPI web server (async)                         │
│  • REST API endpoints (/api/*)                        │
│  • Identity resolver (multi-source)                   │
│  • Encryption service (BYOK with AES-256)             │
│  • Background tasks (APScheduler)                     │
│  • JWT authentication middleware                      │
│  • CORS middleware (React ↔ FastAPI)                  │
│  • OpenAPI documentation (auto-generated)             │
└────────────────────────┬──────────────────────────────┘
                         │
                         │ SQL Queries + Connection Pool
                         │ SQLAlchemy ORM
                         │
┌────────────────────────▼──────────────────────────────┐
│         DATA LAYER (POSTGRESQL)                        │
│         (Storage)                                     │
│                                                       │
│  • PostgreSQL database (production-grade)             │
│  • Encrypted API keys (AES-256-GCM)                   │
│  • Identity mappings (unified users)                  │
│  • Audit logs (compliance tracking)                   │
│  • Chatbot configurations                             │
│  • Document upload history                            │
│  • Test results and metrics                           │
└───────────────────────────────────────────────────────┘
```

---

## Security Architecture (ENHANCED)

### Multi-Layer Security

```
Layer 1: ACCESS CONTROL
├─ Multiple identity providers (LDAP, OAuth, Local)
├─ Unified identity management
├─ Session timeout (1 hour)
└─ IP whitelist (optional)

Layer 2: AUTHORIZATION
├─ Role-based permissions (RBAC)
│  ├─ Super Admin (can do everything)
│  ├─ Client Admin (manage specific chatbot)
│  └─ Viewer (can only see, not edit)
└─ Resource-level permissions

Layer 3: DATA PROTECTION (ENHANCED)
├─ BYOK - Each user's own API keys
├─ AES-256-GCM encryption (military grade)
├─ Master key stored separately (not in DB)
├─ Keys decrypted only in memory
├─ Passwords hashed (bcrypt)
├─ HTTPS for all traffic
└─ SQL injection prevention (FastAPI auto-escapes)

Layer 4: AUDIT
├─ Log every action with user identity
├─ Track which identity provider used
├─ API key usage tracking (who, when, which key)
├─ Cannot be deleted
└─ Available for compliance
```

**New Security Features:**

1. **BYOK Security Flow:**
```
User adds key → Encrypt → Store → Use → Decrypt in RAM → Use → Clear RAM
                                     ↑
                              Never saved decrypted
```

2. **Identity Security:**
```
Multiple logins → Identity resolver → Single user profile
                                            ↓
                                     Same permissions
                                     Same audit trail
```

---

## Integration with Existing System

### How It Connects

**Current Chatbot Files:**
- ✅ No changes to `src/` folder
- ✅ No changes to `Data/` folder
- ✅ No changes to existing routes
- ✅ One small addition to `app.py`

**What Changes:**

**File:** `app.py` (3 lines added)
```
Before:
• Creates chatbot graph
• Starts Flask server

After:
• Creates chatbot graph
• ADDS: Starts FastAPI backend ← NEW
• Starts Flask server (chatbots)
```

**All Services Run Together:**
```
Port 3000: React Frontend (development) or Nginx static (production)
Port 8000: FastAPI Backend (admin portal API)
Port 5000: Flask (existing chatbots)
```

**Communication Flow:**
```
User's Browser (React App)
         ↓
    HTTP Requests
         ↓
FastAPI Backend (Port 8000)
         ↓
    PostgreSQL Database
         ↓
Existing Chatbot System (Port 5000)
```

That's it! Everything else is in the new `admin_portal_backend/` and `admin_portal_frontend/` folders.

---

## Frontend-Backend Communication

### API Architecture

**REST API Structure:**

All frontend requests go to the backend via REST API endpoints:

```
AUTHENTICATION:
POST   /api/auth/login          • User login (returns JWT token)
POST   /api/auth/logout         • Logout and invalidate token
POST   /api/auth/sso            • SSO authentication
POST   /api/auth/refresh        • Refresh JWT token

DASHBOARD:
GET    /api/dashboard/stats     • Get overview statistics
GET    /api/dashboard/activity  • Recent activity logs

CLIENTS (CHATBOTS):
GET    /api/clients             • List all chatbots
GET    /api/clients/:id         • Get specific chatbot details
POST   /api/clients             • Create new chatbot
PUT    /api/clients/:id         • Update chatbot configuration
DELETE /api/clients/:id         • Delete chatbot

DOCUMENTS:
POST   /api/documents/upload    • Upload files (multipart/form-data)
GET    /api/documents           • List uploaded documents
DELETE /api/documents/:id       • Delete document

INDEXING:
POST   /api/indexing/start      • Start indexing job
GET    /api/indexing/status/:id • Get indexing progress
GET    /api/indexing/jobs       • List all indexing jobs

API KEYS (BYOK):
GET    /api/keys                • List user's API keys (masked)
POST   /api/keys                • Add new API key
DELETE /api/keys/:id            • Delete API key

IDENTITY:
GET    /api/identity            • Get user's linked identities
POST   /api/identity/link       • Link new identity to account

TESTING:
POST   /api/tests/run           • Execute test cases
GET    /api/tests/results       • Get test results
```

### Authentication Flow

```
┌─────────────────────────────────────────────────────────┐
│  STEP 1: USER LOGS IN                                   │
│                                                         │
│  React Login Form                                       │
│       ↓                                                 │
│  POST /api/auth/login                                   │
│  Body: { email, password }                              │
│       ↓                                                 │
│  FastAPI validates credentials                          │
│       ↓                                                 │
│  Returns: { token: "jwt-token-here", user: {...} }     │
│       ↓                                                 │
│  React stores token in localStorage                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  STEP 2: SUBSEQUENT REQUESTS                            │
│                                                         │
│  React makes API call                                   │
│       ↓                                                 │
│  Axios interceptor adds header:                         │
│  Authorization: Bearer jwt-token-here                   │
│       ↓                                                 │
│  FastAPI middleware verifies JWT                        │
│       ↓                                                 │
│  If valid → Process request                             │
│  If invalid → Return 401 Unauthorized                   │
│       ↓                                                 │
│  React handles 401 → Redirect to login                  │
└─────────────────────────────────────────────────────────┘
```

### Real-Time Updates

**WebSocket Connection for Live Progress:**

```
Frontend establishes WebSocket:
ws://localhost:8000/ws/indexing/job-id-123

Backend sends updates:
{
  "job_id": "job-id-123",
  "progress": 45,
  "status": "processing",
  "message": "Indexing FAQ document..."
}

React component updates UI in real-time:
Progress bar: 45%
Status: "Processing FAQ document..."
```

### File Upload Flow

```
User selects file in React
     ↓
React creates FormData object
     ↓
POST /api/documents/upload
Content-Type: multipart/form-data
     ↓
FastAPI receives file stream
     ↓
Validates file (type, size)
     ↓
Saves to disk
     ↓
Creates database record
     ↓
Returns: { file_id, filename, status }
     ↓
React updates UI: "Upload successful!"
```

### CORS Configuration

**Backend (FastAPI):**
```python
# Allows React app to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Frontend (React):**
```javascript
// Axios base configuration
axios.defaults.baseURL = 'http://localhost:8000/api';
axios.defaults.withCredentials = true;
```

---

## Deployment Architecture (UPDATED)

### Development Environment

```
Developer's Laptop
├─ Backend Development:
│  ├─ Python environment (venv)
│  ├─ PostgreSQL (local)
│  ├─ FastAPI development server (uvicorn)
│  └─ Access: http://localhost:8000/api
│
└─ Frontend Development:
   ├─ Node.js environment (npm/yarn)
   ├─ React development server (npm start)
   ├─ Hot module replacement (auto-reload)
   └─ Access: http://localhost:3000

Development Setup:
1. Terminal 1: cd admin_portal_backend && uvicorn main:app --reload
2. Terminal 2: cd admin_portal_frontend && npm start
3. Browser: Open http://localhost:3000
   (React automatically proxies API calls to port 8000)
```

---

### Production Environment

```
Company Server
│
├─ Nginx (Web Server - Reverse Proxy)
│  ├─ Routes /admin/* → React Frontend (port 3000)
│  ├─ Routes /api/* → FastAPI Backend (port 8000)
│  └─ Routes / → Flask chatbots (port 5000)
│
├─ React Frontend (Development Server in Dev, Built Static in Prod)
│  ├─ Development: npm start (port 3000)
│  └─ Production: Served as static files by Nginx
│
├─ FastAPI Backend (Application Server)
│  ├─ Uvicorn workers (async)
│  ├─ CORS enabled for frontend
│  └─ JWT authentication
│
├─ PostgreSQL (Database Server)
│  ├─ Can be same server or separate
│  └─ Stores all admin data
│
└─ Flask (Existing Chatbots)
   └─ No changes needed
```

**Server Requirements (UPDATED):**
- OS: Linux (Ubuntu/CentOS) or Windows Server
- RAM: 8GB minimum (was 4GB) for PostgreSQL
- Disk: 50GB free space (was 20GB) for database
- CPU: 4 cores minimum (was 2) for better concurrency

**Why More Resources?**
- PostgreSQL needs more RAM for caching
- FastAPI handles more concurrent users
- Better performance overall

---

## Data Flow Example (UPDATED)

### Scenario: Admin Uploads New FAQ Document with BYOK

```
Step 1: AUTHENTICATION
Sarah logs in with Google OAuth
↓
Identity Resolver: sarah.google@company.com → User ID: 15
↓
Loads Sarah's profile + permissions

Step 2: VERIFY API KEY
System checks: Does Sarah have OpenAI key?
↓
Query user_api_keys table for User ID: 15
↓
Found: Sarah's encrypted OpenAI key
↓
Ready to proceed

Step 3: UPLOAD FILE
Sarah clicks "Upload Document"
↓
Selects: Lollypop Design chatbot
↓
Chooses: FAQ_v3.pdf
↓
FastAPI receives upload (async)

Step 4: PROCESS FILE
Server validates file (PDF? size OK?)
↓
Backs up old FAQ to archive/ folder
↓
Saves new file to Data/lollypop_design/faq_data/
↓
Records in database:
  - Uploaded by: Sarah (User ID: 15)
  - Identity used: Google OAuth
  - File: FAQ_v3.pdf
  - When: 2024-11-25 14:30:00

Step 5: TRIGGER INDEXING (BACKGROUND)
FastAPI creates background task (no Celery needed)
↓
Background task starts:
  - Job ID: uuid-123
  - Status: running
  - User: Sarah

Step 6: USE SARAH'S API KEY
Indexing job needs OpenAI
↓
Retrieves Sarah's encrypted key from database
↓
Decrypts in memory using master key
↓
Uses key for embeddings: sk-sarah-key-***
↓
Clears decrypted key from memory
↓
Logs: "Sarah's OpenAI key used for indexing"

Step 7: UPDATE PROGRESS
Progress: 0% → 25% → 50% → 75% → 100%
↓
Each update written to PostgreSQL
↓
Sarah sees real-time progress on dashboard

Step 8: COMPLETION
Job status: completed
↓
Client status: active
↓
Notification: "FAQ indexed successfully!"
↓
Audit log: "Sarah uploaded FAQ_v3.pdf and indexed using her OpenAI key"
```

**Time:** 2 minutes upload + 5-10 minutes indexing = ~12 minutes total

**Key Differences from Old Way:**
- Uses Sarah's own API key (not shared)
- Tracks which identity she used (Google OAuth)
- No Redis/Celery (FastAPI background tasks)
- Real-time progress (PostgreSQL handles concurrency)

---



---


---

## Risk Assessment

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| PostgreSQL migration | Medium | Keep SQLite as backup during transition |
| FastAPI learning curve | Low | Well documented, similar to Flask |
| Encryption key loss | High | Store master key in 3 locations (backup) |
| Identity conflicts | Medium | Manual resolution UI for admins |
| Database corruption | Low | PostgreSQL has better recovery than SQLite |

---

### Project Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope creep | Medium | Lock requirements early, phased approach |
| Developer availability | Medium | React & FastAPI are popular, easy to find devs |
| Timeline delays | Low | Start with MVP (3-4 weeks) |
| User adoption | Low | Better than current (terminal commands) |
| Frontend-backend integration | Low | Well-defined REST API, clear contracts |
| Browser compatibility | Low | React handles most compatibility issues |
| State management complexity | Medium | Use Redux Toolkit, follow best practices |

---

## Success Metrics

### How We Measure Success

**Before Admin Portal:**
- Time to upload new FAQ: 20-30 minutes
- Time to check all chatbots: 15 minutes
- Manual terminal commands: 50+ per week
- Errors from manual work: 5-10 per month
- API key sharing: Everyone uses same key (security risk)

**After Admin Portal (Goals):**
- Time to upload new FAQ: 2-3 minutes (90% faster)
- Time to check all chatbots: 30 seconds (95% faster)
- Manual terminal commands: 0 per week (100% reduction)
- Errors from manual work: 0-1 per month (90% reduction)
- API key security: Each user has own keys (100% better)

**ROI:** Time saved = 2-3 hours per week = $5,000-10,000/year savings

---

## Maintenance Plan

### Ongoing Support Needed

**Daily:**
- Monitor system health (automated)
- Check error logs if alerts (5-10 min)

**Weekly:**
- Review audit logs (30 min)
- PostgreSQL backup verification (10 min)

**Monthly:**
- Update backend dependencies (Python packages) (1 hour)
- Update frontend dependencies (npm packages) (1 hour)
- Review user feedback (1 hour)
- Rotate encryption keys (30 min) ← NEW

**Quarterly:**
- Security audit (4-8 hours)
- Performance optimization (4-8 hours)
- Identity mapping cleanup (2 hours) ← NEW

**Total Maintenance:** ~6-12 hours per month (was 5-10)

---

## Technical Specifications Summary (UPDATED)

### What We're Building

**Type:** Web-based admin panel (separated frontend + backend)

**Languages:**
- Frontend: JavaScript (React/JSX), CSS
- Backend: Python
- Database: SQL

**Frontend Framework:** React 18+ with Redux Toolkit

**Backend Framework:** FastAPI (was Flask)

**Database:** PostgreSQL (was SQLite)

**Background Tasks:** FastAPI built-in (was Celery + Redis)

**Files Created:** ~65 files (30 backend + 35 frontend)

**Lines of Code:**
- Backend: ~2,500-3,000 lines (Python)
- Frontend: ~3,000-4,000 lines (JavaScript/JSX)

**Impact:** Minimal changes to existing code

**Server:** Runs on existing infrastructure

**Ports:**
- Frontend: 3000 (dev) or served by Nginx (prod)
- Backend API: 8000
- Existing Chatbots: 5000

**Cost:** Development only, no ongoing infrastructure cost

---

## Timeline & Milestones (UPDATED)

### 10-Week Plan

```
Week 1-2:  Backend Foundation + Database
           BACKEND:
           • PostgreSQL setup
           • FastAPI basic structure
           • Identity management design
           • User authentication (JWT)
           • API endpoints (auth, dashboard)

           FRONTEND:
           • React project setup (Create React App)
           • Redux store configuration
           • Login page UI
           • Axios client setup

           Deliverable: Can log in via React UI with multiple identity providers

Week 3:    Documents + BYOK
           BACKEND:
           • File upload endpoint
           • File validation & storage
           • User API key encryption

           FRONTEND:
           • Document upload component (drag-drop)
           • API keys management page
           • File list display

           Deliverable: Users can upload files and add their own API keys

Week 4:    Indexing (Async)
           BACKEND:
           • Background tasks (FastAPI)
           • Progress tracking
           • Use user's API keys
           • WebSocket for real-time updates

           FRONTEND:
           • Indexing progress UI
           • Real-time progress updates (WebSocket)
           • Status indicators

           Deliverable: Indexing works with BYOK, live progress tracking

Week 5:    Identity Management
           BACKEND:
           • Identity resolver
           • Merge multiple identities
           • Link accounts API

           FRONTEND:
           • Identity management page
           • Link account UI
           • Identity provider selection

           Deliverable: Users can log in from multiple sources

Week 6-7:  Testing + Dashboard
           BACKEND:
           • Test creator API
           • Test runner
           • Dashboard statistics API

           FRONTEND:
           • Dashboard with charts (Chart.js)
           • Test runner UI
           • Test results display
           • Client management page

           Deliverable: Complete monitoring with interactive dashboard

Week 8-9:  Polish + Security
           BACKEND:
           • Security audit
           • Encryption testing
           • API performance optimization

           FRONTEND:
           • UI/UX improvements
           • Responsive design (mobile support)
           • Loading states & error handling
           • Accessibility (a11y)

           Deliverable: Production-ready with polished UI

Week 10:   Deployment
           BACKEND:
           • Production setup (Uvicorn + Nginx)
           • Migration scripts (SQLite → PostgreSQL)

           FRONTEND:
           • Build optimization (npm run build)
           • Static file serving via Nginx
           • Environment configuration

           • Documentation (setup guides)

           Deliverable: Live on server, fully deployed

```

**Milestone Reviews:** End of weeks 2, 5, 7, 10

**Key Changes from Original Plan:**
- Week 1-2: Added React setup alongside backend
- Week 3-4: Parallel frontend + backend development
- Week 6-7: Interactive dashboard with charts
- Week 8-9: UI polish and responsive design
- Week 10: Frontend build process added

---

## Migration Plan (SQLite → PostgreSQL)

**For Existing Data:**

```
Step 1: Export from SQLite
↓
Step 2: Transform data format
↓
Step 3: Import to PostgreSQL
↓
Step 4: Verify data integrity
↓
Step 5: Keep SQLite as backup (1 month)
```

**Zero Downtime:**
- Run both databases in parallel for 1 week
- Gradually switch traffic
- No user disruption

---



---

## Conclusion

### What You Get (UPDATED)

**A web portal that:**
- Manages all chatbots from one place
- Saves 2-3 hours per week
- Reduces errors by 90%
- Uses production-ready technology (PostgreSQL)
- Runs on modern async framework (FastAPI)
- Supports multiple identity providers
- Implements BYOK for better security
- Costs no extra infrastructure

**Built with:**
- React (frontend) - modern, component-based UI
- FastAPI (backend) - modern, fast, async
- PostgreSQL (database) - production-ready
- Redux Toolkit (state management)
- 65 new files in two separate folders (frontend + backend)
- Minimal changes to existing code

**Timeline:**
- MVP: 3-4 weeks
- Full version: 8-10 weeks

**Cost:**
- Development: $18,000-26,000
- Infrastructure: ~$100/year (same as before)
- RAM upgrade: $200-500 one-time (if needed)
- ROI: Break even in 2-3 years from time savings

**Risk:** Low (separate from chatbots, uses proven tech)

**Key Improvements Based on Feedback:**
1. ✅ PostgreSQL instead of SQLite (production-ready)
2. ✅ FastAPI instead of Flask + Celery + Redis (simpler, faster)
3. ✅ Unified identity management (multiple providers)
4. ✅ BYOK with encryption (better security, cost tracking)

---

**Recommendation:** Proceed with phased approach - start with MVP (dashboard + upload + indexing + BYOK) in 4 weeks, then add remaining features based on feedback.

---

## Architecture Summary: Frontend-Backend Separation

### Why Separate Frontend and Backend?

**Benefits of This Architecture:**

1. **Independent Development:**
   - Frontend team can work on React UI
   - Backend team can work on FastAPI simultaneously
   - No blocking dependencies

2. **Technology Flexibility:**
   - Can upgrade React without touching backend
   - Can switch UI libraries easily
   - Backend changes don't break frontend (if API contract maintained)

3. **Better Performance:**
   - React optimizes UI rendering
   - Backend focuses on data processing
   - Can scale frontend and backend independently

4. **Modern Development Experience:**
   - Hot reload in development (instant UI updates)
   - TypeScript support available (for type safety)
   - Rich ecosystem of React libraries

5. **Deployment Flexibility:**
   - Frontend can be served from CDN (faster loading)
   - Backend can be replicated for high availability
   - Can use different hosting providers

### Folder Structure Recap

```
terralogic-chatbot-main/
│
├── admin_portal_backend/     ← FastAPI + Python
│   ├── api/                  → REST endpoints
│   ├── models/               → Database models
│   ├── core/                 → Business logic
│   └── config/               → Settings
│
├── admin_portal_frontend/    ← React + JavaScript
│   ├── src/
│   │   ├── components/       → Reusable UI components
│   │   ├── pages/            → Page components
│   │   ├── services/         → API client
│   │   └── store/            → Redux state
│   └── public/               → Static assets
│
└── existing chatbot files unchanged
```

### Communication Pattern

```
User Browser
    ↕ (HTTPS)
React App (Port 3000)
    ↕ (REST API + JWT)
FastAPI (Port 8000)
    ↕ (SQL)
PostgreSQL Database
```

**Clean separation of concerns:**
- React: Handles UI/UX, user interactions, state management
- FastAPI: Handles business logic, authentication, data processing
- PostgreSQL: Handles data storage, relationships, queries


