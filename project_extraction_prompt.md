# ROLE

Act as a **Senior Software Architect, Code Auditor, Reverse Engineer, Technical Writer, and Documentation Engineer**.

Your task is to completely inspect and reverse-engineer the **entire project/folder provided to you** and create **ONE comprehensive PDF document** that serves as a complete technical blueprint and reference of the project.

Do NOT give me a brief summary.

I want an **exhaustive extraction of the project**, including its structure, features, functionality, code architecture, files, directories, functions, classes, components, dependencies, configurations, data flow, UI, database, APIs, authentication, security, deployment, and every other technically relevant detail that can be discovered from the project.

---

# 1. PROJECT SCANNING — INSPECT EVERYTHING

First recursively inspect the **entire project directory**.

Do not only inspect the obvious source-code folders.

Inspect:

- Every directory
- Every subdirectory
- Every source file
- Every configuration file
- Every environment/configuration file
- Every asset directory
- Every documentation file
- Every package/dependency file
- Every script
- Every API-related file
- Every database-related file
- Every schema/model
- Every test
- Every build/deployment file
- Every public/static asset
- Every UI component
- Every utility/helper
- Every service
- Every middleware
- Every hook
- Every route
- Every controller
- Every model
- Every class
- Every function
- Every constant
- Every important variable/configuration
- Every integration
- Every external service

Do not skip files merely because they appear small or unimportant.

If a file is binary, generated, compiled, minified, or otherwise difficult to inspect, record that fact and document whatever metadata can safely be extracted.

---

# 2. PROJECT INVENTORY

Create a complete project inventory.

For every directory provide:

- Directory path
- Purpose
- Important contents
- Relationship to other directories

For every file provide:

- Full relative path
- File name
- File type
- Language
- Approximate size/line count where available
- Purpose
- Dependencies/imports
- Important exports
- Functions/classes/components contained inside
- Whether the file is actively used
- Files that depend on it
- Files it depends on

Create a **complete directory tree** such as:

PROJECT/
├── src/
│   ├── components/
│   ├── pages/
│   ├── services/
│   └── utils/
├── public/
├── config/
├── tests/
└── ...

The tree must reflect the actual project.

Do NOT invent directories or files.

---

# 3. PROJECT OVERVIEW

Document:

- Project name
- Project type
- Framework
- Programming languages
- Architecture
- Main purpose
- Target users
- Main workflows
- Major modules
- Major technologies
- Dependencies
- External services
- Database technology
- Authentication system
- Deployment architecture
- Build system
- Testing system

Also provide a high-level architecture diagram.

---

# 4. EVERY FEATURE

Extract **EVERY identifiable feature** from the project.

For each feature document:

### Feature Name
### Purpose
### User-facing behavior
### How the user accesses it
### UI components involved
### Pages/screens involved
### Functions involved
### Classes involved
### Services involved
### API endpoints involved
### Database/data involved
### Files involved
### Dependencies
### Authentication/authorization requirements
### Validation
### Error handling
### Edge cases
### Related features
### Feature dependencies
### Current implementation status

Do not combine unrelated features.

If the project contains 50 features, document all 50.

---

# 5. USER FLOWS

Extract all major user journeys.

For each workflow document:

START
→ User action
→ UI/component
→ Function
→ State/data change
→ API/service
→ Database/external service
→ Response
→ UI update
→ END

Include flows for:

- Registration
- Login
- Logout
- Authentication
- Navigation
- Main application workflows
- Forms
- Search
- Filtering
- Uploads
- Downloads
- CRUD operations
- Settings
- Profile
- Payments if present
- Admin functions if present
- Error states
- Empty states
- Loading states
- Permission-restricted actions

Only document flows that actually exist.

---

# 6. FUNCTION-BY-FUNCTION EXTRACTION

Create a detailed inventory of **every meaningful function/method**.

For each function document:

- Function name
- File path
- Class/module
- Parameters
- Parameter types
- Return value
- Return type
- Purpose
- Internal logic
- Functions it calls
- Functions that call it
- State it modifies
- Data it reads
- Data it writes
- API calls
- Database operations
- Error handling
- Side effects
- Authentication/security implications
- Related UI
- Related features

Group functions by module/file.

Do not omit functions simply because they are short.

---

# 7. CLASS / COMPONENT EXTRACTION

For every class, component, service, controller, model, hook, provider, or equivalent structure document:

- Name
- File path
- Responsibility
- Properties
- Methods
- Inputs/props
- Outputs
- Dependencies
- Parent/child relationships
- Consumers
- Lifecycle behavior
- State management
- Events
- API interactions
- Database interactions
- Error handling

---

# 8. UI/UX DOCUMENTATION

If the project contains a frontend, document every page/screen/view.

For each page:

- Route/path
- Purpose
- Layout
- Components
- Buttons
- Forms
- Inputs
- Navigation
- Modals
- Tables
- Cards
- Menus
- States
- Loading behavior
- Error behavior
- Empty states
- Responsive behavior
- Authentication requirements
- Data displayed
- Actions available
- Functions triggered

Create a **page → component → function → service/API** relationship map.

---

# 9. ROUTING

Extract all routes.

For each route document:

- Route
- HTTP method if applicable
- Page/controller
- Authentication requirement
- Authorization requirement
- Parameters
- Query parameters
- Request body
- Response
- Middleware
- Validation
- Error handling
- Related files

---

# 10. API DOCUMENTATION

Extract every API endpoint.

For each endpoint:

- Endpoint
- HTTP method
- Purpose
- Request format
- Headers
- Authentication
- Parameters
- Query parameters
- Request body
- Validation
- Response structure
- Error responses
- Status codes
- Database operations
- External API calls
- Calling frontend component/function
- Files implementing the endpoint

Create an API summary table.

---

# 11. DATABASE / DATA MODEL

If a database exists, document:

- Database technology
- Tables/collections
- Schemas
- Models
- Fields
- Data types
- Required fields
- Default values
- Relationships
- Foreign keys
- Indexes
- Constraints
- Queries
- CRUD operations
- Migrations
- Seed data
- Database services
- Data flow

Create an ER-style relationship diagram where possible.

---

# 12. STATE MANAGEMENT

Identify all state management mechanisms.

Document:

- Global state
- Local state
- Context/providers
- Stores
- Redux/Zustand/etc. if applicable
- State variables
- State mutations
- Persistence
- Synchronization
- Derived state
- State dependencies

Explain which components read and modify each important state.

---

# 13. AUTHENTICATION & AUTHORIZATION

Document exactly how authentication works.

Include:

- Registration
- Login
- Logout
- Sessions
- Tokens
- Cookies
- JWT
- Refresh tokens
- Password handling
- Password reset
- Email verification
- Role system
- Permissions
- Protected routes
- Middleware
- Session expiration
- Auto logout
- Tab visibility behavior
- Inactivity behavior
- Security checks

Clearly distinguish:

**Implemented**
vs.
**Partially implemented**
vs.
**Not found**

Do not assume security functionality exists without evidence.

---

# 14. SECURITY AUDIT

Identify:

- Authentication vulnerabilities
- Authorization issues
- Input validation weaknesses
- XSS risks
- CSRF risks
- SQL/NoSQL injection risks
- Sensitive data exposure
- Hardcoded secrets
- Insecure storage
- Weak session handling
- CORS configuration
- API security
- File upload security
- Dependency vulnerabilities where detectable
- Client-side security issues
- Server-side security issues

For every issue provide:

- Severity
- Location
- Evidence
- Why it matters
- Recommended fix

Do not claim a vulnerability unless supported by the code/configuration.

---

# 15. DEPENDENCIES

Extract all dependencies.

For each dependency:

- Package/library
- Version
- Purpose
- Where used
- Important APIs used
- Whether required at runtime/build time
- Potentially unused dependency
- Compatibility concerns

Include package managers and lock files.

---

# 16. ENVIRONMENT & CONFIGURATION

Document:

- Environment variables
- Configuration files
- Build configuration
- Runtime configuration
- Feature flags
- API URLs
- Database configuration
- Third-party service configuration
- Secrets references

**IMPORTANT: NEVER expose actual passwords, API keys, tokens, private keys, credentials, or other secrets in the PDF.**

Replace secrets with:

`[REDACTED SECRET]`

Document only the variable name and its purpose.

---

# 17. EXTERNAL SERVICES & INTEGRATIONS

Identify every external integration.

Examples:

- Payment providers
- Authentication providers
- Email services
- Cloud storage
- Analytics
- AI APIs
- Maps
- Social login
- CDN
- Hosting
- Databases
- Third-party APIs

For each:

- Service
- Purpose
- Files using it
- API calls
- Authentication method
- Data exchanged
- Failure behavior
- Configuration requirements

---

# 18. ERROR HANDLING

Identify:

- try/catch blocks
- Error boundaries
- Global error handlers
- API error handling
- Validation errors
- Network errors
- Authentication errors
- Database errors
- User-facing errors
- Logging
- Recovery mechanisms

Document what happens when each major operation fails.

---

# 19. TESTING

Extract:

- Unit tests
- Integration tests
- End-to-end tests
- Test files
- Test frameworks
- Test configuration
- Tested features
- Untested features
- Coverage information if available

Create:

**Feature → Test Coverage**

mapping.

---

# 20. BUILD & DEPLOYMENT

Document:

- Build commands
- Development commands
- Production commands
- Build pipeline
- Deployment platform
- Hosting configuration
- CI/CD
- Environment configuration
- Database deployment
- Asset deployment
- Domain configuration if present
- Production requirements
- Runtime requirements

Document deployment dependencies and potential deployment failure points.

---

# 21. FILE DEPENDENCY GRAPH

Determine relationships such as:

File A
→ imports File B
→ calls Function C
→ accesses Service D
→ accesses Database E

Create dependency diagrams wherever practical.

Identify:

- Highly connected files
- Core modules
- Entry points
- Utility modules
- Dead/unreferenced modules
- Circular dependencies
- Potential architectural bottlenecks

---

# 22. DATA FLOW

Document important data flows.

For example:

USER INPUT
↓
UI
↓
VALIDATION
↓
FUNCTION
↓
SERVICE
↓
API
↓
DATABASE
↓
RESPONSE
↓
STATE
↓
UI

Create diagrams for major workflows.

---

# 23. PROJECT ENTRY POINTS

Identify:

- Application entry point
- Frontend entry point
- Backend entry point
- Main configuration
- Main router
- Main database connection
- Main state provider
- Main server
- Build entry point

Explain the startup sequence.

---

# 24. CODE QUALITY AUDIT

Evaluate:

- Architecture
- Maintainability
- Readability
- Modularity
- Naming
- Duplication
- Complexity
- Coupling
- Cohesion
- Error handling
- Type safety
- Documentation
- Testing
- Scalability

Provide evidence-based findings.

---

# 25. DEAD CODE & UNUSED CODE

Identify possible:

- Unused files
- Unused functions
- Unused components
- Unused dependencies
- Unused variables
- Commented-out implementations
- Duplicate implementations
- Legacy code

Clearly label these as:

**Confirmed unused**

or

**Potentially unused — requires verification**

Do not falsely classify code as unused.

---

# 26. PERFORMANCE AUDIT

Identify potential:

- Expensive operations
- Unnecessary API calls
- Excessive re-renders
- Large assets
- Memory leaks
- Inefficient database queries
- Blocking operations
- Duplicate requests
- Poor caching
- Large bundles
- Slow startup operations

For each issue:

- Location
- Evidence
- Impact
- Severity
- Recommendation

---

# 27. ACCESSIBILITY

If a frontend exists, inspect:

- Semantic HTML
- Keyboard navigation
- Focus management
- ARIA
- Labels
- Form accessibility
- Contrast
- Screen-reader compatibility
- Error messaging
- Responsive behavior

Document actual findings only.

---

# 28. RESPONSIVE DESIGN

Document behavior across:

- Desktop
- Tablet
- Mobile

Identify responsive breakpoints and responsive components/styles where detectable.

---

# 29. BUSINESS LOGIC

Extract and explain important business rules.

For every major rule:

- Rule
- Where implemented
- Conditions
- Inputs
- Outputs
- Exceptions
- Related functions
- Related UI
- Related database/API operations

---

# 30. CONFIGURATION MATRIX

Create a table containing:

| Configuration | Location | Purpose | Required? | Default | Environment |
|---|---|---|---|---|---|

Do not expose secrets.

---

# 31. COMPLETE FEATURE MATRIX

Create:

| Feature | Frontend | Backend | Database | API | Authentication | Tests | Status |
|---|---|---|---|---|---|---|---|

Use actual project evidence.

---

# 32. COMPLETE FILE MATRIX

Create:

| File | Type | Purpose | Imports | Exports | Used By | Status |
|---|---|---|---|---|---|---|

Include all relevant project files.

---

# 33. ARCHITECTURE DIAGRAMS

Create clean diagrams for:

1. Overall architecture
2. Directory architecture
3. Application startup
4. User authentication
5. Major user workflows
6. Frontend → backend flow
7. API architecture
8. Database relationships
9. Data flow
10. Important module dependencies

Diagrams must be based on the actual project.

---

# 34. KNOWN ISSUES

Create a prioritized issue list.

Classify:

### CRITICAL
Application-breaking/security/data-loss issues.

### HIGH
Major functional or architectural problems.

### MEDIUM
Important quality/performance/maintainability issues.

### LOW
Minor improvements.

For every issue include:

- Issue
- Location
- Evidence
- Impact
- Severity
- Recommended solution

---

# 35. MISSING / UNKNOWN INFORMATION

Create a dedicated section called:

**UNKNOWN / NOT VERIFIABLE FROM PROJECT**

List anything that cannot be determined from the supplied files.

Examples:

- External server configuration
- Undocumented production infrastructure
- Credentials
- External dashboard configuration
- Runtime behavior that cannot be verified statically

Never fabricate missing information.

---

# 36. IMPLEMENTATION STATUS

For important functionality classify it as:

- ✅ Fully implemented
- 🟡 Partially implemented
- 🔴 Broken / problematic
- ⚪ Not found
- ❓ Cannot verify

Explain the evidence for each classification.

---

# 37. FINAL PROJECT BLUEPRINT

End the PDF with a concise but comprehensive blueprint containing:

## Project Architecture
## Complete Feature List
## Complete Directory Structure
## Core Modules
## Important Functions
## Important Classes/Components
## APIs
## Database
## Authentication
## External Services
## Data Flows
## Dependencies
## Configuration
## Security
## Performance
## Testing
## Deployment
## Known Issues
## Technical Debt
## Recommended Improvements
## Unknown Information

---

# 38. DOCUMENT QUALITY REQUIREMENTS

The final PDF must be:

- Professional
- Well structured
- Searchable
- Printable
- Easy to navigate
- Technically precise
- Consistent
- Clearly sectioned

Include:

- Cover page
- Table of contents
- Section numbering
- Page numbers
- Headers/footers
- Tables
- Code snippets where useful
- Architecture diagrams
- Flow diagrams
- Cross-references
- Glossary where necessary

Use syntax highlighting for important code snippets.

Do not fill the document with unnecessary screenshots or repeated code.

---

# 39. CRITICAL ACCURACY RULES

These rules are mandatory:

1. **Do not invent anything.**
2. **Do not assume a feature exists because the project appears to need it.**
3. **Only document functionality supported by the actual project.**
4. Clearly distinguish facts from inference.
5. Never expose secrets.
6. Never silently skip directories.
7. Never silently skip source files.
8. If something cannot be inspected, explicitly report it.
9. Preserve exact file paths.
10. Preserve exact function/class/component names.
11. Cross-check relationships before documenting them.
12. Do not claim a function is unused without sufficient evidence.
13. Do not claim a security vulnerability without evidence.
14. Do not claim a feature is broken without evidence.
15. Do not modify the original project.
16. Do not delete or rename anything.
17. Do not alter project functionality.
18. The PDF must represent the **actual current state of the supplied project**, not an idealized version.

---

# 40. TWO-PASS VALIDATION

Before generating the final PDF, perform a second independent verification pass.

### PASS 1 — EXTRACTION

Extract the complete project information.

### PASS 2 — VALIDATION

Check:

- Every directory accounted for
- Every important file accounted for
- Every feature accounted for
- Every route accounted for
- Every API accounted for
- Every important function accounted for
- Every class/component accounted for
- Dependencies verified
- Database structures verified
- Authentication verified
- Configuration verified
- External integrations verified
- Cross-references verified
- No fabricated information
- No exposed secrets
- No major omissions

Create a final:

**DOCUMENTATION COVERAGE CHECK**

table showing what was successfully inspected and documented.

---

# FINAL OUTPUT

Generate exactly **ONE PDF file** containing the complete project documentation.

The PDF should be treated as the project's:

**MASTER TECHNICAL DOCUMENTATION + ARCHITECTURE REFERENCE + FEATURE INVENTORY + CODEBASE MAP + AUDIT REPORT**

The goal is that a developer who has never seen the project can read this single PDF and understand:

**WHAT the project does  
→ HOW it works  
→ WHERE everything is located  
→ WHICH files implement each feature  
→ WHICH functions/classes/components are involved  
→ HOW data moves through the system  
→ HOW APIs and databases interact  
→ HOW authentication/security works  
→ HOW it is configured and deployed  
→ WHAT problems currently exist  
→ WHAT cannot be verified**

Do not provide only a summary.

**Inspect first. Extract second. Validate third. Generate the PDF last.**
