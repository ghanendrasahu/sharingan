MASTER BUILD PROMPT
Production-Grade AI Legal Document Analyzer for Indian Startups

You are the lead architect, senior backend engineer, senior frontend engineer, ML/LLM engineer, DevOps engineer, security engineer, QA engineer, and technical product manager for this project.

Build a production-grade SaaS application for analyzing Indian legal/business documents using AI.

The product should help startups, freelancers, employees, landlords/tenants, and small businesses understand contracts by identifying:

Potential legal risks
Commercial risks
Missing or potentially missing clauses
Ambiguous clauses
Unfavorable clauses
Important obligations
Key dates
Liability exposure
Termination conditions
IP ownership issues
Confidentiality issues
Privacy/data-protection issues
Dispute-resolution provisions
Payment obligations
Plain-English explanations
Relevant Indian legal sources
Suggested drafting directions
Contract-level risk scores

The system must not represent itself as a lawyer and must not claim that an AI-generated conclusion is definitive legal advice.

The product should clearly communicate when professional legal review is appropriate.

================================================================================
SECTION 1: NON-NEGOTIABLE ENGINEERING RULES
================================================================================

Rule 1 — Production quality

Do NOT create:

fake implementations
placeholder functions
TODO-driven architecture
hardcoded API responses
mock data pretending to be production data
fake payment verification
fake authentication
fake legal citations
invented laws
invented court cases
invented legal sections

If a feature cannot be safely implemented, explain the limitation and implement the correct abstraction.

Rule 2 — Incremental development

Do NOT build the entire application in one step.

Build it milestone by milestone.

After completing every milestone:

Run tests.
Run linting.
Run type checks where applicable.
Run security checks where applicable.
Verify the feature manually.
Update documentation.
Inspect git diff.
Commit the completed feature.
Push the commit to the configured GitHub remote.
Only then move to the next milestone.

Never combine unrelated milestones into one huge commit.

================================================================================
SECTION 2: COMPLETED MILESTONES (DO NOT REIMPLEMENT)
================================================================================

The following milestones have been completed and pushed to main:

MILESTONE 01 — Repository Foundation ✅ COMPLETE
- monorepo structure
- Docker / Docker Compose
- Python environment with pyproject.toml
- React environment
- linting (ruff, eslint)
- formatting
- pre-commit hooks
- .env.example
- README
- Makefile

MILESTONE 02 — Database Foundation ✅ COMPLETE
- PostgreSQL with pgvector
- SQLAlchemy async models
- Alembic migrations
- base models with UUID, timestamps, soft delete
- health checks

MILESTONE 03 — Authentication ✅ COMPLETE
- registration with email/password
- login with JWT
- refresh tokens
- logout
- bcrypt password hashing
- RBAC (OWNER, ADMIN, MEMBER, VIEWER)
- IDOR protection

MILESTONE 04 — Organizations ✅ COMPLETE
- organizations table
- organization_members with roles
- tenant isolation
- IDOR tests

MILESTONE 05 — Object Storage ✅ COMPLETE
- MinIO for local development
- S3 abstraction layer
- secure uploads with validation
- signed URLs
- document metadata

MILESTONE 06 — Document Upload ✅ COMPLETE
- PDF and DOCX upload
- MIME type validation
- file signature validation
- size limits
- upload API with org scoping
- duplicate detection via file hash

MILESTONE 07 — Document Processing Package ✅ COMPLETE (exists in packages/)
- PDF extraction (pdf_extractor.py)
- DOCX extraction (docx_extractor.py)
- OCR abstraction (ocr.py)
- page preservation
- structured document representation
- async processing wrapper

MILESTONE 08 — Clause Segmentation Package ✅ COMPLETE (exists in packages/)
- heading detection
- numbered clauses (1., 1.1, (a), (i))
- nested clauses
- definitions
- schedules and annexures
- page references
- clause_models.py with ClauseType enum

MILESTONE 24 — Usage System ✅ COMPLETE
- usage tracking models
- credits system
- plan limits
- usage service with check_usage_limit

MILESTONE 27 — Audit Logs ✅ COMPLETE
- audit events table
- organization filtering
- secure logging
- audit API endpoints

MILESTONE 28 — Security Hardening ✅ COMPLETE
- security headers middleware
- rate limiting (100 req/min)
- input sanitization
- XSS prevention

MILESTONE 30 — Observability ✅ COMPLETE
- structured logging (structlog)
- metrics collection (prometheus)
- request IDs
- LLM cost tracking helpers
- analysis latency tracking

MILESTONE 31 — CI/CD ✅ COMPLETE
- GitHub Actions CI workflow
- lint, test, security scan, Docker build jobs
- deployment workflow

MILESTONE 32 — Production Deployment ✅ COMPLETE
- production Dockerfiles (multi-stage, non-root)
- docker-compose.prod.yml
- nginx configuration
- health checks
- backup scripts

================================================================================
SECTION 3: REMAINING MILESTONES (PRIORITY ORDER)
================================================================================

Execute these milestones in order. Each builds on the previous.

--------------------------------------------------------------------------------
PHASE A: Wire Existing Packages to API Layer
--------------------------------------------------------------------------------

MILESTONE A1 — Connect Document Processing to Celery Tasks

Current state: packages/document_processing has real extraction code, but
apps/api/app/tasks/document.py uses time.sleep() simulations.

Implement:
- Import legallens_docproc.processor in tasks/document.py
- Replace simulate steps with real extraction calls
- process_document_task calls process_document_async()
- Store extraction results in database (document_pages, document_clauses tables)
- Update task progress in real-time
- Handle errors with proper retry logic

Files to modify:
- apps/api/app/tasks/document.py
- apps/api/app/models/document.py (add pages/clauses if needed)

Tests:
- Upload a real PDF, verify text extraction
- Upload a real DOCX, verify text extraction
- Verify page/clause data stored correctly

Commit: feat: wire real document extraction into Celery tasks

--------------------------------------------------------------------------------
MILESTONE A2 — Connect Clause Segmentation to Pipeline

Current state: clause_segmenter.py exists with 305 lines of real regex patterns,
but is not called by the processing pipeline.

Implement:
- After text extraction, call clause_segmenter.segment_clauses()
- Store clauses in document_clauses table
- Include page references and clause types
- Handle nested clauses properly

Files to modify:
- apps/api/app/tasks/document.py
- apps/api/app/models/document.py

Tests:
- Verify clauses extracted with correct types
- Verify page references preserved
- Test nested clause handling

Commit: feat: connect clause segmentation to document pipeline

--------------------------------------------------------------------------------
MILESTONE A3 — Connect AI Analyzer to Analysis Tasks

Current state: ai_analyzer.py exists with OpenAI/Groq provider abstraction,
but analyze_document_task uses time.sleep() simulation.

Implement:
- Import AIAnalyzer from legallens_docproc
- Configure LLM provider from settings (OPENAI_API_KEY or GROQ_API_KEY)
- Call analyzer.analyze_document() with extracted clauses
- Store results in analysis_results table
- Track token usage and cost

Files to modify:
- apps/api/app/tasks/document.py
- apps/api/app/models/ (add analysis_result model if needed)
- apps/api/app/core/config.py (ensure LLM keys configured)

Tests:
- Verify AI analysis returns structured risks
- Verify results stored in database
- Mock LLM for unit tests

Commit: feat: wire AI analyzer into analysis tasks

--------------------------------------------------------------------------------
MILESTONE A4 — Replace Mock Analysis API Endpoints

Current state: apps/api/app/api/v1/analysis.py returns hardcoded mock data.

Implement:
- POST /analysis/analyze → trigger Celery task, return task_id
- GET /analysis/status/{task_id} → query Celery for real status
- GET /analysis/result/{document_id} → fetch from database
- GET /analysis/risks/{analysis_id} → fetch risks from DB
- DELETE /analysis/cancel/{task_id} → revoke Celery task

Files to modify:
- apps/api/app/api/v1/analysis.py
- apps/api/app/models/ (ensure analysis models exist)

Tests:
- Start analysis, poll status, verify completion
- Verify 404 for non-existent documents
- Verify authorization (user can only see their org's analyses)

Commit: feat: replace mock analysis endpoints with real implementation

--------------------------------------------------------------------------------
MILESTONE A5 — Replace Mock Search API Endpoints

Current state: apps/api/app/api/v1/search.py returns hardcoded mock data.

Implement:
- Use legallens_docproc.semantic_search and vector_store
- POST /search/semantic → query pgvector embeddings
- POST /search/clauses → search clause embeddings
- POST /search/index → generate and store embeddings for document
- GET /search/stats → real stats from vector store

Prerequisite: Ensure embeddings are generated in document pipeline.

Files to modify:
- apps/api/app/api/v1/search.py
- apps/api/app/tasks/document.py (add embedding generation)

Tests:
- Index a document, verify searchable
- Search returns relevant clauses
- Stats reflect actual index size

Commit: feat: replace mock search endpoints with real semantic search

--------------------------------------------------------------------------------
MILESTONE A6 — Replace Mock Reports API Endpoints

Current state: apps/api/app/api/v1/reports.py returns hardcoded mock data.

Implement:
- Use legallens_docproc.report_generator
- POST /reports/generate → create report from analysis results
- GET /reports/{document_id} → list reports from DB
- GET /reports/detail/{report_id} → fetch report from DB
- POST /reports/export → export as JSON/HTML/Markdown/PDF
- DELETE /reports/{report_id} → delete from DB

Files to modify:
- apps/api/app/api/v1/reports.py
- apps/api/app/models/ (add report model)

Tests:
- Generate report after analysis
- Export in multiple formats
- Verify report content matches analysis

Commit: feat: replace mock report endpoints with real generation

--------------------------------------------------------------------------------
PHASE B: Build Empty AI/Legal/Retrieval Packages
--------------------------------------------------------------------------------

MILESTONE B1 — Build LangGraph Analysis Engine (packages/ai)

Current state: packages/ai/legallens_ai is empty (only __init__.py).

Implement:
- TypedDict state for analysis pipeline
- Graph nodes: DocumentClassifier, ClauseRouter, RiskAnalyzer, MissingClauseAnalyzer
- LegalRetriever node (stub for now)
- EvidenceVerifier node
- RiskScorer node
- RecommendationGenerator node
- QualityChecker node
- Error handling and checkpointing

File structure:
packages/ai/legallens_ai/
├── __init__.py
├── state.py (AnalysisState TypedDict)
├── graph.py (build_analysis_graph)
├── nodes/
│   ├── __init__.py
│   ├── classifier.py
│   ├── risk_analyzer.py
│   ├── missing_clause.py
│   ├── legal_retriever.py
│   ├── evidence_verifier.py
│   ├── risk_scorer.py
│   ├── recommendations.py
│   └── quality_checker.py
└── prompts/
    ├── __init__.py
    └── analysis_prompts.py

Dependencies to add:
- langgraph
- langchain-core

Tests:
- Test each node in isolation
- Test full graph execution with mock LLM
- Verify structured outputs

Commit: feat: build LangGraph analysis engine

--------------------------------------------------------------------------------
MILESTONE B2 — Build Indian Legal Corpus (packages/legal)

Current state: packages/legal/legallens_legal is empty (only __init__.py).

Implement:
- Source schema with metadata and versioning
- Ingestion pipeline for legal sources
- Chunking for retrieval
- Initial corpus from authoritative Indian legal sources:
  - Indian Contract Act, 1872
  - Companies Act, 2013
  - Information Technology Act, 2000
  - Arbitration and Conciliation Act, 1996
  - Digital Personal Data Protection framework

File structure:
packages/legal/legallens_legal/
├── __init__.py
├── models.py (LegalSource, LegalChunk)
├── sources/
│   ├── __init__.py
│   ├── contract_act.py
│   ├── companies_act.py
│   └── it_act.py
├── ingestion.py
├── chunking.py
└── versioning.py

Tests:
- Verify source metadata
- Verify chunking produces valid chunks
- Verify versioning works

Commit: feat: establish versioned Indian legal corpus

--------------------------------------------------------------------------------
MILESTONE B3 — Build Hybrid Retrieval System (packages/retrieval)

Current state: packages/retrieval/legallens_retrieval is empty (only __init__.py).

Implement:
- VectorRetriever (pgvector)
- KeywordRetriever (BM25 or similar)
- HybridRetriever (combines both with reranking)
- Metadata filters (jurisdiction, document_type, law, section)

File structure:
packages/retrieval/legallens_retrieval/
├── __init__.py
├── base.py (Retriever interface)
├── vector.py (VectorRetriever)
├── keyword.py (KeywordRetriever)
├── hybrid.py (HybridRetriever with reranking)
├── filters.py
└── evaluation.py (Recall@K, MRR, NDCG)

Tests:
- Test each retriever in isolation
- Test hybrid combination
- Verify retrieval metrics

Commit: feat: implement hybrid legal retrieval

--------------------------------------------------------------------------------
MILESTONE B4 — Document Classification

Current state: No document type classification exists.

Implement:
- DocumentClassifier using LLM
- Classify into: employment, nda, lease, vendor, consultancy, founder, term_sheet, other, unknown
- Return confidence score
- Store classification in documents table

Files to modify:
- apps/api/app/tasks/document.py
- apps/api/app/models/document.py
- packages/ai/legallens_ai/nodes/classifier.py

Tests:
- Verify correct classification for sample documents
- Verify confidence scores
- Verify "unknown" for ambiguous documents

Commit: feat: add legal document classification

--------------------------------------------------------------------------------
MILESTONE B5 — Risk Analysis with Evidence

Current state: AI analyzer exists but risk analysis is basic.

Implement:
- RiskAnalyzer node with structured outputs
- Risk taxonomy (legal, commercial, IP, confidentiality, privacy, operational)
- Evidence references from legal corpus
- Confidence scores
- Store risks in analysis_risks table

Files to modify:
- packages/ai/legallens_ai/nodes/risk_analyzer.py
- apps/api/app/models/ (add risk model)

Tests:
- Verify structured risk output
- Verify evidence references
- Verify confidence calibration

Commit: feat: implement evidence-based risk analysis

--------------------------------------------------------------------------------
MILESTONE B6 — Missing Clause Detection

Implement:
- MissingClauseAnalyzer node
- Document-type-specific expectations (NDA needs IP clause, employment needs termination, etc.)
- Confidence and evidence for each missing clause
- Store in analysis_missing_clauses table

Files to modify:
- packages/ai/legallens_ai/nodes/missing_clause.py
- apps/api/app/models/

Tests:
- Verify missing clauses detected for incomplete documents
- Verify low false positive rate

Commit: feat: implement missing clause analysis

--------------------------------------------------------------------------------
MILESTONE B7 — Citation Verification

Implement:
- EvidenceVerifier node
- Map claims to legal sources
- Validate citations exist and support claims
- Filter unsupported claims
- Store verified citations

Files to modify:
- packages/ai/legallens_ai/nodes/evidence_verifier.py
- packages/legal/legallens_legal/

Tests:
- Verify valid citations retained
- Verify invalid citations removed
- Verify confidence reflects evidence quality

Commit: feat: implement legal citation verification

--------------------------------------------------------------------------------
MILESTONE B8 — Deterministic Risk Scoring

Implement:
- RiskScorer node (NOT LLM-based)
- Scoring dimensions: legal severity, enforceability, financial exposure, business impact
- Configurable weights
- Score bands: 0-29 Low, 30-49 Moderate, 50-69 High, 70-100 Critical
- Document clearly that score is heuristic, not legal determination

Files to modify:
- packages/ai/legallens_ai/nodes/risk_scorer.py

Tests:
- Verify deterministic output for same input
- Verify weights configurable
- Verify score bands correct

Commit: feat: implement explainable risk scoring

--------------------------------------------------------------------------------
PHASE C: Frontend Integration
--------------------------------------------------------------------------------

MILESTONE C1 — Analysis Dashboard with Real Data

Current state: Dashboard shows live counts but analysis page consumes mock API.

Implement:
- Connect AnalysisPage to real /analysis endpoints
- Show real risk scores and risk cards
- Show real missing clauses
- Show real citations with links
- Loading states and error handling

Files to modify:
- apps/web/src/pages/AnalysisPage.tsx
- apps/web/src/components/AnalysisResults.tsx
- apps/web/src/components/RiskVisualization.tsx

Tests:
- Run analysis, verify results display
- Verify risk navigation works
- Verify error states handled

Commit: feat: connect analysis dashboard to real API

--------------------------------------------------------------------------------
MILESTONE C2 — Document Viewer with Clause Navigation

Implement:
- PDF viewer component
- Clause navigation sidebar
- Click clause to highlight in PDF
- Risk indicators on clauses
- Side-by-side analysis view

Files to create/modify:
- apps/web/src/components/PdfViewer.tsx
- apps/web/src/components/ClauseNavigation.tsx
- apps/web/src/pages/DocumentViewerPage.tsx

Tests:
- Verify PDF renders
- Verify clause navigation works
- Verify highlighting works

Commit: feat: add evidence-driven document viewer

--------------------------------------------------------------------------------
MILESTONE C3 — Contract Q&A

Current state: Mock endpoint only.

Implement:
- POST /documents/{id}/ask endpoint (real implementation)
- Q&A UI component
- Document-grounded answers
- Legal evidence citations
- Conversation history (optional)

Files to modify:
- apps/api/app/api/v1/analysis.py (or new qa.py)
- apps/web/src/components/ContractQA.tsx

Tests:
- Ask question, verify grounded answer
- Verify "unknown" when document doesn't answer
- Verify citations included

Commit: feat: add grounded contract Q&A

--------------------------------------------------------------------------------
MILESTONE C4 — Contract Comparison

Current state: Mock endpoint only.

Implement:
- POST /documents/compare endpoint
- Upload two versions
- Detect added/removed/modified clauses
- Risk change analysis
- Before/after display UI

Files to modify:
- apps/api/app/api/v1/ (add comparison.py)
- apps/web/src/pages/ComparisonPage.tsx

Tests:
- Upload two versions, verify diff
- Verify risk changes detected

Commit: feat: implement contract version comparison

--------------------------------------------------------------------------------
MILESTONE C5 — PDF Report Generation

Implement:
- Professional PDF report template
- Include: executive summary, risks, missing clauses, citations, recommendations
- Download from UI
- Disclaimer and limitations

Files to modify:
- packages/document_processing/legallens_docproc/report_generator.py
- apps/web/src/components/ReportDownload.tsx

Tests:
- Generate report, verify PDF structure
- Verify all sections present

Commit: feat: add downloadable PDF analysis reports

--------------------------------------------------------------------------------
PHASE D: Payment Integration
--------------------------------------------------------------------------------

MILESTONE D1 — Persist Payment Data to Database

Current state: PaymentService uses in-memory dicts, no DB persistence.

Implement:
- Create payments and subscriptions tables (may exist)
- Store orders in database
- Store payments in database
- Store subscriptions in database
- Replace in-memory dicts with DB queries

Files to modify:
- apps/api/app/services/payment.py
- apps/api/app/models/payment.py

Tests:
- Create order, verify in DB
- Complete payment, verify subscription in DB
- Restart server, verify data persists

Commit: feat: persist payment data to database

--------------------------------------------------------------------------------
MILESTONE D2 — Integrate Real Razorpay API

Current state: Payment service creates mock order IDs, no real Razorpay SDK.

Implement:
- Install razorpay SDK
- Create real orders via Razorpay API
- Verify real payment signatures
- Handle real webhooks
- Test with Razorpay test mode

Dependencies:
- razorpay

Files to modify:
- apps/api/app/services/payment.py
- apps/api/app/core/config.py (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)

Tests:
- Create order, verify Razorpay order ID
- Verify signature with test payment
- Verify webhook handling

Commit: feat: integrate Razorpay API

--------------------------------------------------------------------------------
PHASE E: Final Validation
--------------------------------------------------------------------------------

MILESTONE E1 — Evaluation Framework

Implement:
- Golden test dataset (synthetic contracts)
- Retrieval metrics (Recall@K, MRR, NDCG)
- Risk detection metrics (precision, recall, F1)
- Citation correctness metrics
- Hallucination checks
- Regression test suite

Files to create:
- data/evaluation/ (synthetic contracts)
- tests/evaluation/ (evaluation tests)

Tests:
- All evaluation tests pass
- Quality thresholds met

Commit: test: establish AI evaluation framework

--------------------------------------------------------------------------------
MILESTONE E2 — Final QA

Run:
- All unit tests
- All integration tests
- All security tests
- All frontend tests
- All evaluation tests
- Load tests
- Migration tests from clean DB

Fix all critical/high issues.

Commit: test: complete production release validation

================================================================================
SECTION 4: DEFINITION OF DONE
================================================================================

The project is NOT complete until ALL of these are true:

[ ] Authentication works
[ ] Authorization works
[ ] Multi-tenancy works
[ ] Tenant isolation tested
[x] PDF upload works
[x] DOCX upload works
[x] File validation works
[x] Secure storage works
[ ] PDF extraction works (package exists, not wired)
[ ] Clause segmentation works (package exists, not wired)
[ ] Document classification works
[ ] Legal corpus exists
[ ] Legal corpus is versioned
[ ] Hybrid RAG works
[ ] Retrieval evaluation exists
[ ] LangGraph analysis works
[ ] Structured LLM outputs work
[ ] Risk detection works
[ ] Missing clause detection works
[ ] Citation verification works
[ ] Risk scoring works
[ ] Contract Q&A works
[ ] Contract comparison works
[ ] PDF report generation works
[x] Usage limits work
[ ] Razorpay works (mock only)
[ ] Webhook verification works
[x] Audit logging works
[x] Security tests pass
[ ] AI evaluation passes
[x] CI passes
[x] Docker builds
[x] Production configuration exists
[x] Documentation is complete
[x] .env is not committed
[x] No secrets are committed
[ ] Every remaining milestone has a git commit
[ ] Every remaining milestone has been pushed

================================================================================
SECTION 5: EXECUTION INSTRUCTION
================================================================================

Start with MILESTONE A1.

Do not jump ahead.

After each milestone:

1. Run tests
2. Run linting
3. Run type checks
4. Verify manually
5. git status
6. git diff
7. Commit with exact message specified
8. Push
9. Confirm commit succeeded

Then proceed to next milestone.

Prefer at every stage:

correctness > speed
security > convenience
evidence > confidence
maintainability > cleverness
real implementation > mock implementation

The final result must be a real production-grade SaaS architecture, not a demo disguised as production software.
