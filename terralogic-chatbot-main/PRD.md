# Product Requirements Document (PRD)
## Admin Portal for Chatbot Management
---

## 1. Executive Summary

### What Are We Building?

A web-based admin portal that allows team members to manage all company chatbots from one central location, without needing technical knowledge or command-line access.

### Why Are We Building It?

**Current Problem:**
- Managing 4 chatbots requires terminal commands
- Each update takes 20-30 minutes
- High risk of human error
- Only tech-savvy people can make changes
- No visibility into chatbot status

**Our Solution:**
- Simple web interface anyone can use
- Updates take 2-3 minutes
- Point-and-click operations
- Real-time status monitoring
- Secure and auditable

### Who Is This For?

- **Primary Users:** Admin team members who manage chatbot content
- **Secondary Users:** Managers who need to monitor chatbot performance
- **Not For:** End users of the chatbots (they continue using the existing chat interface)

---

## 2. Problem Statement

### Current Situation

**We manage 4 chatbots:**
1. Lollypop Design Chatbot
2. Lollypop Academy Chatbot
3. Terralogic Chatbot
4. Terralogic Academy Chatbot

**How We Manage Them Today:**
1. Open terminal/command prompt
2. Navigate to correct folder
3. Run manual commands
4. Edit configuration files
5. Upload documents via file system
6. Manually trigger indexing
7. Check logs to verify success
8. Repeat for each chatbot

**Pain Points:**

| Problem | Impact | Frequency |
|---------|--------|-----------|
| Time-consuming manual work | 2-3 hours per week wasted | Daily |
| Requires technical knowledge | Only 2-3 people can do updates | Always |
| High error rate | 5-10 mistakes per month | Weekly |
| No visibility | Can't see if chatbots are working | Always |
| No audit trail | Don't know who changed what | Always |
| Security risk | Everyone shares same API keys | Always |

### What Happens If We Don't Build This?

- Continue wasting 2-3 hours per week (100+ hours per year)
- Risk of errors affecting customer experience
- Can't scale team (requires technical training)
- No compliance or audit capabilities
- Security vulnerabilities remain

---

## 3. Goals and Objectives

### Primary Goals

1. **Save Time:** Reduce chatbot management time by 90% (from 30 min to 3 min per task)
2. **Remove Barriers:** Allow non-technical team members to manage chatbots
3. **Improve Reliability:** Reduce errors from 5-10 per month to 0-1 per month
4. **Increase Visibility:** Real-time dashboard showing all chatbot statuses
5. **Enhance Security:** Individual user API keys instead of shared credentials

**Qualitative:**
- "Easy enough for non-technical staff"
- "Confident making changes without breaking things"
- "Can see what's happening at a glance"
- "Feel in control of the chatbots"

### Non-Goals (Out of Scope)

❌ **What We Are NOT Building:**
- New chatbot functionality (chatbots work the same)
- Public-facing features (end users won't see changes)
- Mobile app (web browser only)
- Integration with external marketing tools (future phase)
- Conversation analytics (future phase)

---

## 4. User Personas

**Needs:**
- Upload new FAQ documents easily
- See when indexing is complete
- Check if chatbot is responding correctly
- No coding or terminal required

**Pain Points:**
- Currently asks IT team to update chatbots
- Waits hours or days for changes
- Can't verify changes worked
- Feels dependent on others

**Goals with Admin Portal:**
- Upload FAQs in minutes
- Test chatbot responses immediately
- Independence from IT team

---
**Needs:**
- Monitor all chatbots from one place
- Quickly identify and fix issues
- Audit trail of all changes
- Control who can do what

**Pain Points:**
- Manually runs commands dozens of times per day
- Gets interrupted by content team for simple updates
- No visibility into problems until users complain
- Can't track who made changes

**Goals with Admin Portal:**
- Dashboard showing all chatbot health
- Let content team self-serve
- Automatic logging of all actions
- Role-based access control


**Needs:**
- See overview of chatbot status
- Verify team is keeping content updated
- Monitor for issues before customers complain
- Compliance and audit reports

**Pain Points:**
- No visibility into chatbot operations
- Relies on team to report issues
- Can't verify compliance requirements
- No data for decision-making

**Goals with Admin Portal:**
- Executive dashboard with key metrics
- See last update times
- View audit logs
- Export reports for compliance

---

## 5. Features and Requirements

### Must-Have Features (MVP - Phase 1)

#### Feature 1: User Authentication & Access Control

**What:**
- Login page with username/password
- Support for company SSO (Google, Microsoft)
- Different permission levels (Admin, Editor, Viewer)

**Why:**
- Security: Only authorized users can access
- Compliance: Know who did what
- Flexibility: Support multiple login methods

**Acceptance Criteria:**
- [ ] Login page with email/password option
- [ ] "Sign in with Google" button works
- [ ] "Sign in with Microsoft" button works
- [ ] Invalid login shows error message
- [ ] Successful login takes user to dashboard
- [ ] Session expires after 1 hour of inactivity

---

#### Feature 2: Dashboard (Overview)

**What:**
- Main page showing status of all chatbots
- Quick stats: active/inactive, last updated, current issues
- Recent activity log

**Why:**
- At-a-glance health check
- Quickly identify problems
- See recent changes

**Acceptance Criteria:**
- [ ] Shows all 4 chatbots with names
- [ ] Each chatbot shows status: Active/Inactive/Error
- [ ] Shows last updated date/time
- [ ] Shows last indexing status
- [ ] Quick action buttons (Upload, Index, Test)
- [ ] Recent activity feed (last 10 actions)
- [ ] Auto-refreshes every 30 seconds

---

#### Feature 3: Document Upload

**What:**
- Upload FAQ documents, manuals, knowledge base files
- Drag-and-drop or click to browse
- Shows upload progress
- Validation of file types and sizes

**Why:**
- Main task users need to do
- Replace manual file copying
- Ensure only valid files uploaded


**Acceptance Criteria:**
- [ ] Drag-and-drop area for files
- [ ] Click to browse option
- [ ] Accepts: PDF, DOCX, TXT, CSV files
- [ ] Rejects files over 50MB
- [ ] Shows upload progress bar
- [ ] Success message when complete
- [ ] Error message if file invalid
- [ ] Preview of uploaded file name and size
- [ ] Backup old file before replacing

---

#### Feature 4: Indexing Management

**What:**
- Trigger indexing after uploading documents
- Real-time progress bar
- See indexing status (queued, running, completed, failed)
- View indexing logs

**Why:**
- Documents must be indexed before chatbot can use them
- Users need to know when it's done
- Troubleshoot if indexing fails

**Acceptance Criteria:**
- [ ] "Start Indexing" button
- [ ] Progress bar shows 0-100%
- [ ] Status updates every 5 seconds
- [ ] Shows estimated time remaining
- [ ] Success notification when complete
- [ ] Error message with details if failed
- [ ] Can view indexing logs
- [ ] Can cancel indexing if needed

---

#### Feature 5: Chatbot Client Management

**What:**
- List all chatbots
- View configuration for each
- Enable/disable individual chatbots
- Edit basic settings (name, description)

**Why:**
- Central place to see all chatbots
- Ability to temporarily disable if needed
- Update metadata without code changes

**Acceptance Criteria:**
- [ ] Table showing all chatbots
- [ ] Columns: Name, Status, Last Updated, Actions
- [ ] Toggle switch to enable/disable
- [ ] View details button
- [ ] Edit name and description
- [ ] Can't delete chatbots (safety)
- [ ] Confirmation before disabling

---

#### Feature 6: API Key Management (BYOK - Bring Your Own Key)

**What:**
- Each user can add their own OpenAI/LangChain API keys
- Keys stored encrypted
- Keys displayed masked (sk-****-123)
- Delete keys option

**Why:**
- Security: No shared credentials
- Accountability: Know who uses what
- Cost control: Users manage own API usage
- Compliance: Better audit trail


**Acceptance Criteria:**
- [ ] "My API Keys" page
- [ ] Add new key button
- [ ] Form: Provider (OpenAI, LangChain), Key value
- [ ] Keys encrypted before saving
- [ ] List shows keys masked (sk-****-abc)
- [ ] Delete key button with confirmation
- [ ] Last used date/time shown
- [ ] Can add multiple keys per provider

---

#### Feature 7: Testing & Verification

**What:**
- Run predefined test queries
- See chatbot responses
- Mark tests as pass/fail
- View test history

**Why:**
- Verify chatbot working after changes
- Catch problems before users do
- Quality assurance


**Acceptance Criteria:**
- [ ] List of test cases
- [ ] "Run Test" button
- [ ] Shows chatbot response
- [ ] Pass/Fail indicator
- [ ] Can add new test cases
- [ ] Test history with timestamps
- [ ] Shows which user ran test

---

#### Feature 8: Audit Log

**What:**
- Log every action (who, what, when)
- View history of changes
- Filter by user, date, action type
- Export logs

**Why:**
- Compliance requirement
- Troubleshooting (what changed?)
- Accountability
- Security monitoring

**Acceptance Criteria:**
- [ ] Log shows: Timestamp, User, Action, Details
- [ ] Filter by date range
- [ ] Filter by user
- [ ] Filter by action type (upload, index, test, etc.)
- [ ] Search functionality
- [ ] Export to CSV
- [ ] Can't delete logs (immutable)

---

### Nice-to-Have Features (Phase 2 - Future)

#### Feature 9: Advanced Analytics
- Conversation metrics
- User satisfaction scores
- Popular questions
- Response accuracy

#### Feature 10: Multi-Language Support
- Admin portal in multiple languages
- Manage chatbots in different languages

#### Feature 11: Scheduled Tasks
- Auto-indexing on schedule
- Automated testing
- Backup schedules

#### Feature 12: Email Notifications
- Alert when indexing completes
- Notify on errors
- Daily summary emails

#### Feature 13: Conversation Viewer
- See recent chatbot conversations
- Search conversations
- Export conversation logs

---


---

## 6. Technical Requirements

### Frontend Requirements

**Technology:**
- React 18+
- Modern web browsers (Chrome, Firefox, Safari, Edge)
- Responsive design (desktop and tablet, mobile optional)

**Performance:**
- Page load time < 2 seconds
- UI interactions respond < 100ms
- Real-time updates every 5 seconds


---

### Backend Requirements

**Technology:**
- FastAPI (Python)
- PostgreSQL database
- RESTful API architecture

**Performance:**
- API response time < 500ms
- Support 10 concurrent users
- File uploads up to 50MB

**Security:**
- HTTPS only
- JWT authentication
- AES-256 encryption for API keys
- Password hashing (bcrypt)
- CORS properly configured

---

### Infrastructure Requirements

**Hosting:**
- Same server as existing chatbots
- No additional infrastructure cost

**Resources:**
- RAM: 8GB minimum
- Disk: 50GB free space
- CPU: 4 cores minimum

**Database:**
- PostgreSQL 12+
- Daily backups
- Connection pooling

---

## 7. User Interface Requirements

### General UI Principles

**Simple & Clean:**
- Minimal clutter
- Clear labels
- Consistent layout

**Intuitive:**
- No training manual needed
- Common UI patterns (buttons, forms, tables)
- Helpful tooltips

**Responsive:**
- Works on desktop (primary)
- Works on tablets
- Mobile optional (view-only)

**Accessible:**
- High contrast
- Large click targets
- Clear error messages

---

### Key Screens

#### 1. Login Page
- Company logo
- Email/password form
- "Sign in with Google" button
- "Sign in with Microsoft" button
- "Forgot password" link
- Simple, professional design

#### 2. Dashboard (Home)
- Header with navigation
- 4 chatbot status cards
- Quick action buttons
- Recent activity feed
- User menu (logout, profile)

#### 3. Upload Page
- Select chatbot dropdown
- Drag-drop upload area
- File browser button
- Upload progress bar
- List of uploaded files
- Success/error messages

#### 4. Indexing Page
- Select chatbot
- "Start Indexing" button
- Progress bar with percentage
- Status messages
- Indexing logs (collapsible)
- History of past indexing jobs

#### 5. API Keys Page
- List of user's API keys (masked)
- "Add New Key" button
- Provider dropdown (OpenAI, LangChain)
- Key input field
- Delete button per key
- Last used timestamp

#### 6. Testing Page
- Select chatbot
- List of test cases
- "Run Test" button
- Test results (pass/fail)
- Chatbot response display
- Test history

#### 7. Audit Log Page
- Table with filters
- Columns: Date, User, Action, Details
- Date range picker
- User filter
- Action type filter
- Export to CSV button

---

## 8. Data Requirements

### Data Collection

**User Data:**
- Email, name, role
- Login timestamps
- API keys (encrypted)

**Chatbot Data:**
- Name, description, status
- Configuration settings
- Last update timestamp

**Document Data:**
- Filename, size, type
- Upload timestamp
- Uploaded by (user ID)

**Indexing Data:**
- Job ID, status, progress
- Start/end timestamps
- Logs and errors

**Test Data:**
- Test cases, expected results
- Actual results
- Pass/fail status
- Execution timestamp

**Audit Data:**
- User ID, action type
- Timestamp
- Details/metadata
- Cannot be deleted

---

### Data Retention

**Active Data:**
- Users: Until account deleted
- Chatbots: Permanent
- Documents: Keep 30 days of old versions
- Indexing jobs: Keep 90 days

**Audit Logs:**
- Keep forever (compliance)
- Archive old logs after 1 year

**Test Results:**
- Keep 1 year

---

### Data Privacy

**Personal Data:**
- User email addresses
- Login activity
- API keys (encrypted)

**Compliance:**
- GDPR compliant (if applicable)
- Right to data export
- Right to account deletion

**Security:**
- All data encrypted at rest
- All communication over HTTPS
- API keys never logged in plain text

---

## 9. Integration Requirements

### Existing Systems

**Integration Points:**

1. **Existing Chatbot System:**
   - Admin portal controls existing chatbots
   - No changes to chatbot code required
   - Uses same file structure

2. **Company SSO:**
   - Google Workspace OAuth
   - Microsoft Azure AD
   - LDAP/Active Directory (optional)

3. **File System:**
   - Read/write to existing Data/ folders
   - Maintain current folder structure

4. **OpenAI API:**
   - Use user's API keys
   - Track usage per user

**No Integration With:**
- External marketing tools (future)
- CRM systems (future)
- Analytics platforms (future)

---

## 10. Security Requirements

### Authentication

- [ ] Password strength requirements (min 8 chars, uppercase, number)
- [ ] Failed login lockout (5 attempts)
- [ ] Session timeout (1 hour)
- [ ] Logout functionality
- [ ] "Remember me" option

### Authorization

- [ ] Role-based access control (Admin, Editor, Viewer)
- [ ] Resource-level permissions
- [ ] Admin can manage users
- [ ] Users can only see their own API keys

### Data Protection

- [ ] HTTPS only (no HTTP)
- [ ] API keys encrypted with AES-256
- [ ] Passwords hashed with bcrypt
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] CSRF tokens

### Audit & Compliance

- [ ] Log all user actions
- [ ] Immutable audit log
- [ ] Regular security reviews
- [ ] Vulnerability scanning

---

## 11. Performance Requirements

### Response Times

| Action | Target | Maximum |
|--------|--------|---------|
| Page load | < 1 second | < 2 seconds |
| API call | < 300ms | < 500ms |
| File upload (10MB) | < 5 seconds | < 10 seconds |
| Indexing start | < 1 second | < 2 seconds |
| Real-time update | Every 5 seconds | Every 10 seconds |

### Scalability

- Support 10 concurrent users (current need)
- Can scale to 50 users (future)
- Handle 100 file uploads per day
- Database can store 1 year of audit logs

### Reliability

- 99% uptime (excluding maintenance)
- Automatic error recovery
- Graceful degradation
- Daily backups

---

## 12. Testing Requirements

### Types of Testing

**Unit Testing:**
- Backend API functions
- Frontend components
- Encryption/decryption
- Authentication logic

**Integration Testing:**
- Frontend ↔ Backend
- Backend ↔ Database
- SSO integration
- File operations

**User Acceptance Testing (UAT):**
- Content Manager workflow
- IT Admin workflow
- Manager workflow
- Error scenarios

**Security Testing:**
- Penetration testing
- Vulnerability scanning
- Authentication bypass attempts
- SQL injection tests

**Performance Testing:**
- Load testing (10 concurrent users)
- File upload stress test
- Database query performance

---

### Acceptance Criteria for MVP

**Before Launch:**
- [ ] All must-have features complete
- [ ] 0 critical bugs
- [ ] < 5 minor bugs
- [ ] UAT passed by 3 test users
- [ ] Security review passed
- [ ] Performance tests passed
- [ ] Documentation complete

---

## 13. Timeline

### Phase 1: MVP (8-10 weeks)

**Weeks 1-2: Foundation**
- Setup React + FastAPI
- Database schema
- Basic authentication

**Weeks 3-4: Core Features**
- Document upload
- Indexing
- API key management

**Weeks 5-6: Testing & Dashboard**
- Test runner
- Dashboard UI
- Client management

**Weeks 7-8: Polish**
- UI improvements
- Error handling
- Security hardening

**Weeks 9-10: Deployment**
- Production setup
- User training
- Documentation

### Phase 2: Enhancements (Future)

- Analytics dashboard
- Email notifications
- Scheduled tasks
- Multi-language support

---

## 14. Success Criteria

### Launch Criteria

**Must Have:**
- All MVP features working
- 3 successful UAT sessions
- Security audit passed
- Documentation complete
- Training materials ready

**Quality Metrics:**
- 0 critical bugs
- < 5 minor bugs
- Page load < 2 seconds
- API response < 500ms

### Post-Launch Metrics (30 days)

**Usage:**
- 80% of team using portal (instead of terminal)
- 100+ actions logged per week

**Performance:**
- Average update time < 5 minutes
- < 2 errors per week
- > 95% uptime

**Satisfaction:**
- User satisfaction > 4/5
- Would recommend to others: > 80%

### 90-Day Review

**Quantitative:**
- Time savings: 2-3 hours/week confirmed
- Error reduction: < 1 error/month
- User adoption: 100% of content team

**Qualitative:**
- "I can update chatbots myself now"
- "The dashboard gives me visibility"
- "I feel confident making changes"

---

## 15. Risks and Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-------------
| Database migration issues | Low | High | Keep SQLite backup, migrate gradually |
| API key encryption vulnerability | Low | Critical | Use industry-standard AES-256, store master key securely |
| Integration with existing chatbots | Low | High | Minimal changes, thorough testing |

### Project Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Timeline delays | Medium | Medium | Start with MVP, defer nice-to-have features |
| User adoption resistance | Low | Medium | Involve users early, make UI intuitive |
| Scope creep | High | Medium | Lock requirements, phased approach |

### Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| ROI not achieved | Low | Medium | Track metrics, adjust based on feedback |
| Security breach | Low | Critical | Security audit, best practices, encryption |
| Compliance issues | Low | High | Audit logging, data privacy measures |

---

## 16. Dependencies

### External Dependencies

- PostgreSQL database
- OpenAI API
- Company SSO (Google/Microsoft)
- Existing chatbot system

### Internal Dependencies

- IT team for server access
- Content team for UAT
- Management approval
- Budget approval

### Blocking Issues

- None currently identified

---

## 17. Appendix

### Glossary

**Terms:**
- **MVP:** Minimum Viable Product - basic version with essential features
- **BYOK:** Bring Your Own Key - users provide their own API keys
- **JWT:** JSON Web Token - authentication method
- **SSO:** Single Sign-On - use company login
- **CORS:** Cross-Origin Resource Sharing - security for web requests
- **Indexing:** Process of preparing documents for chatbot use
- **UAT:** User Acceptance Testing - testing by actual users


