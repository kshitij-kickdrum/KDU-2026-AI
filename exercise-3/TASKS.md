# Tri-Model AI Assistant - Implementation Tasks

**Project**: Exercise 3 - Tri-Model AI Assistant  
**Status**: Not Started  
**Last Updated**: 2026-04-21

---

## Task Overview

- **Total Tasks**: 45
- **Completed**: 0
- **In Progress**: 0
- **Not Started**: 45

---

## Phase 1: Project Setup & Infrastructure

### 1.1 Project Structure Setup
- [ ] Create folder structure (src/, config/, tests/, data/)
- [ ] Create all necessary `__init__.py` files
- [ ] Set up `.gitignore` for Python project
- [ ] Create `requirements.txt` with all dependencies

### 1.2 Configuration Management
- [ ] Create `config/models.yaml` with model configurations
- [ ] Create `config/prompts.yaml` with prompt templates
- [ ] Implement `src/utils/config.py` for configuration loading
- [ ] Add validation for configuration files

### 1.3 Logging Setup
- [ ] Implement `src/utils/logger.py` with console logging
- [ ] Configure log levels (INFO, WARNING, ERROR)
- [ ] Set up log format: `[%(asctime)s] %(levelname)s - %(name)s - %(message)s`
- [ ] Test logging across different modules

---

## Phase 2: Core Utilities

### 2.1 Token Counter Utility
- [ ] Implement `src/utils/token_counter.py`
- [ ] Add function to count tokens for single text
- [ ] Add function to count combined question + context tokens
- [ ] Add function to check if text exceeds token limit (512)
- [ ] Write unit tests for token counter

### 2.2 Chunking Service
- [ ] Implement `src/services/chunking.py`
- [ ] Implement paragraph-first splitting strategy
- [ ] Implement sentence fallback for long paragraphs
- [ ] Implement word-level fallback for long sentences
- [ ] Add overlap logic (60 tokens from previous chunk)
- [ ] Create `Chunk` data class with metadata
- [ ] Write unit tests for chunking service

### 2.3 Validation Service
- [ ] Implement `src/services/validation.py`
- [ ] Add summary quality checks (not empty, min length, etc.)
- [ ] Add compression ratio validation (0.1-0.5)
- [ ] Add repetition detection (max 3 consecutive repeated words)
- [ ] Add sentence count validation (min 2 sentences)
- [ ] Add Q&A confidence validation
- [ ] Write unit tests for validation service

---

## Phase 3: Model Integration

### 3.1 BART Summarizer
- [ ] Implement `src/models/bart_summarizer.py`
- [ ] Add model loading with error handling
- [ ] Add tokenizer loading
- [ ] Implement chunk summarization method
- [ ] Configure generation parameters (max_length=150, min_length=50, do_sample=False)
- [ ] Add GPU/CPU device selection
- [ ] Add model caching logic
- [ ] Test BART summarization with sample text

### 3.2 Qwen Client (LM Studio)
- [ ] Implement `src/models/qwen_client.py`
- [ ] Add HTTP client for LM Studio API (localhost:1234)
- [ ] Implement merge summaries method
- [ ] Implement refine summary method with adaptive length
- [ ] Implement compress context method for Q&A
- [ ] Implement generative Q&A fallback method
- [ ] Add retry logic (3 attempts with exponential backoff)
- [ ] Add timeout handling (30 seconds)
- [ ] Add connection health check
- [ ] Test Qwen client with LM Studio running

### 3.3 RoBERTa Q&A Model
- [ ] Implement `src/models/roberta_qa.py`
- [ ] Add model loading with error handling
- [ ] Add tokenizer loading
- [ ] Implement extractive Q&A method
- [ ] Add confidence score extraction
- [ ] Configure max sequence length (512 tokens)
- [ ] Add GPU/CPU device selection
- [ ] Test RoBERTa Q&A with sample questions

---

## Phase 4: Business Logic Services

### 4.1 Adaptive Length Calculator
- [ ] Implement adaptive length calculation in `src/services/summarization.py`
- [ ] Add compression ratio logic (short: 5-8%, medium: 10-15%, long: 20-30%)
- [ ] Add absolute bounds (short: 80-250, medium: 150-500, long: 300-800)
- [ ] Add function to calculate target length from input word count
- [ ] Write unit tests for adaptive length calculator

### 4.2 Summarization Service
- [ ] Implement `src/services/summarization.py`
- [ ] Add method to generate base summary (chunk → BART → merge)
- [ ] Add method to refine summary with adaptive length
- [ ] Integrate chunking service
- [ ] Integrate BART model
- [ ] Integrate Qwen client for merging
- [ ] Integrate Qwen client for refinement
- [ ] Add validation checks
- [ ] Handle recursive merge for large chunk summaries
- [ ] Write integration tests for summarization pipeline

### 4.3 Q&A Service with 3-Level Fallback
- [ ] Implement `src/services/qa_service.py`
- [ ] Implement Level 1: RoBERTa on refined summary
- [ ] Implement Level 2: RoBERTa on base summary
- [ ] Implement Level 3: Qwen generative fallback
- [ ] Implement Level 4: Structured error response
- [ ] Add confidence threshold check (0.20)
- [ ] Add token limit check and compression trigger
- [ ] Add attempt tracking and logging
- [ ] Generate user-friendly error messages and suggestions
- [ ] Write integration tests for Q&A fallback chain

---

## Phase 5: FastAPI Backend

### 5.1 API Application Setup
- [ ] Implement `src/api/app.py` with FastAPI initialization
- [ ] Add CORS middleware configuration
- [ ] Add startup event for model loading
- [ ] Add shutdown event for cleanup
- [ ] Add global exception handlers
- [ ] Add request/response logging

### 5.2 Data Models (Pydantic)
- [ ] Create `SummarizationRequest` model
- [ ] Create `SummarizationResponse` model
- [ ] Create `RefinementRequest` model
- [ ] Create `RefinementResponse` model
- [ ] Create `QuestionRequest` model
- [ ] Create `QuestionResponse` model
- [ ] Create `QAAttempt` model
- [ ] Create `HealthResponse` model
- [ ] Add validation rules to all models

### 5.3 API Routes
- [ ] Implement `src/api/routes.py`
- [ ] Implement `POST /api/v1/summarize` endpoint
- [ ] Implement `POST /api/v1/refine` endpoint
- [ ] Implement `POST /api/v1/qa` endpoint
- [ ] Implement `GET /api/v1/health` endpoint
- [ ] Add request validation
- [ ] Add error handling for all endpoints
- [ ] Add response formatting
- [ ] Test all endpoints with Postman/curl

### 5.4 Session Management
- [ ] Implement session storage (in-memory dict)
- [ ] Add session creation on summarization
- [ ] Store base summary and refined summary in session
- [ ] Add session retrieval for Q&A
- [ ] Add session cleanup logic (TTL or manual)
- [ ] Handle session not found errors

---

## Phase 6: Streamlit UI

### 6.1 UI Layout
- [ ] Implement `src/main.py` with Streamlit
- [ ] Create page title and description
- [ ] Add text input area for large text
- [ ] Add submit button for summarization
- [ ] Create section for base summary display
- [ ] Add refinement selection (short/medium/long/keep)
- [ ] Create section for refined summary display
- [ ] Create Q&A interface section
- [ ] Add question input field
- [ ] Add answer display area with confidence indicator

### 6.2 HITL Workflow Implementation
- [ ] Implement Step 1: Submit text → Display base summary
- [ ] Add user selection UI for refinement preference
- [ ] Implement Step 2: Refine → Display refined summary
- [ ] Add "Keep base summary" option
- [ ] Show processing indicators during API calls
- [ ] Handle API errors gracefully in UI

### 6.3 Q&A Interface
- [ ] Implement question submission
- [ ] Display answer with confidence score
- [ ] Show fallback level indicator
- [ ] Display error messages with suggestions
- [ ] Show attempt details (expandable section)
- [ ] Add "Ask another question" functionality
- [ ] Maintain conversation history in session

### 6.4 UI Enhancements
- [ ] Add loading spinners for long operations
- [ ] Add success/error notifications
- [ ] Add word count display for summaries
- [ ] Add compression ratio display
- [ ] Add processing time display
- [ ] Style UI with custom CSS (optional)

---

## Phase 7: Testing

### 7.1 Unit Tests
- [ ] Write tests for `test_chunking.py` (70%+ coverage)
- [ ] Write tests for `test_validation.py` (70%+ coverage)
- [ ] Write tests for `test_token_counter.py` (70%+ coverage)
- [ ] Write tests for adaptive length calculator
- [ ] Run all unit tests and verify coverage

### 7.2 Integration Tests
- [ ] Write test for full summarization pipeline (text → base summary)
- [ ] Write test for refinement pipeline (base → refined)
- [ ] Write test for adaptive length calculation with various input sizes
- [ ] Write test for Q&A Level 1 success (refined summary)
- [ ] Write test for Q&A Level 2 fallback (base summary)
- [ ] Write test for Q&A Level 3 fallback (Qwen generative)
- [ ] Write test for Q&A Level 4 error (all fallbacks failed)
- [ ] Write test for HITL workflow
- [ ] Write test for compression activation
- [ ] Test with all 3 sample documents (AI, CSE, ML)

### 7.3 Manual Testing
- [ ] Test with sample AI article (~2000 words)
- [ ] Test with sample CSE paper (~2500 words)
- [ ] Test with sample ML tutorial (~1800 words)
- [ ] Generate short/medium/long summaries for each
- [ ] Verify summary quality and length ranges
- [ ] Ask 5 questions per document
- [ ] Verify answer accuracy
- [ ] Test edge cases (very short text, very long text)
- [ ] Test error handling (disconnect Qwen, invalid input)
- [ ] Test with GPU and CPU modes

---

## Phase 8: Sample Data & Documentation

### 8.1 Sample Data Creation
- [ ] Create `data/sample_ai_article.txt` (~2000 words)
- [ ] Create `data/sample_cse_paper.txt` (~2500 words)
- [ ] Create `data/sample_ml_tutorial.txt` (~1800 words)
- [ ] Verify all samples are AI/CSE/ML related
- [ ] Ensure samples are public domain or original content

### 8.2 Documentation
- [ ] Write `README.md` with project overview
- [ ] Add setup instructions to README
- [ ] Add usage examples to README
- [ ] Document all API endpoints with examples
- [ ] Add troubleshooting section to README
- [ ] Document configuration options
- [ ] Add inline code comments for complex logic
- [ ] Document prompt templates in `prompts.yaml`

---

## Phase 9: Code Quality & Deployment

### 9.1 Code Quality
- [ ] Run `black` formatter on all Python files
- [ ] Run `flake8` linter and fix issues
- [ ] Run `isort` to sort imports
- [ ] Remove all hardcoded values (use config)
- [ ] Add type hints to all functions
- [ ] Review and refactor complex functions
- [ ] Ensure all functions have docstrings

### 9.2 Deployment Preparation
- [ ] Verify `requirements.txt` is complete with versions
- [ ] Test FastAPI backend startup
- [ ] Test Streamlit UI startup
- [ ] Test Qwen connection (LM Studio on port 1234)
- [ ] Verify model downloads and caching
- [ ] Test full application end-to-end
- [ ] Create deployment checklist

### 9.3 Performance Optimization
- [ ] Profile summarization pipeline for bottlenecks
- [ ] Optimize chunking algorithm if needed
- [ ] Test memory usage under load
- [ ] Verify latency requirements are met
- [ ] Test with GPU acceleration
- [ ] Add caching for repeated operations (optional)

---

## Phase 10: Final Review & Submission

### 10.1 Final Testing
- [ ] Run full test suite and verify all tests pass
- [ ] Perform end-to-end manual testing
- [ ] Verify all Definition of Done criteria are met
- [ ] Test on fresh environment (clean install)
- [ ] Verify all models download correctly

### 10.2 Documentation Review
- [ ] Review README for completeness
- [ ] Review DESIGN.md for accuracy
- [ ] Ensure all code is well-commented
- [ ] Verify API documentation is complete
- [ ] Check for any TODO comments left in code

### 10.3 Submission Preparation
- [ ] Create demo video or screenshots (optional)
- [ ] Prepare presentation of key features
- [ ] Document any known limitations
- [ ] Create submission package
- [ ] Final code review

---

## Dependencies Between Tasks

**Critical Path:**
1. Phase 1 (Setup) → Phase 2 (Utilities) → Phase 3 (Models) → Phase 4 (Services) → Phase 5 (API) → Phase 6 (UI) → Phase 7 (Testing)

**Parallel Work Possible:**
- Phase 2 (Utilities) can be done in parallel
- Phase 3 (Models) can be done in parallel after Phase 1
- Phase 8 (Sample Data) can be done anytime
- Phase 9.1 (Code Quality) can be done incrementally

**Blockers:**
- Phase 5 (API) requires Phase 3 (Models) and Phase 4 (Services)
- Phase 6 (UI) requires Phase 5 (API)
- Phase 7 (Testing) requires all previous phases
- Phase 10 (Final Review) requires all phases complete

---

## Estimated Timeline

| Phase | Estimated Time | Priority |
|:------|:---------------|:---------|
| Phase 1: Setup | 2-3 hours | High |
| Phase 2: Utilities | 4-5 hours | High |
| Phase 3: Models | 6-8 hours | High |
| Phase 4: Services | 8-10 hours | High |
| Phase 5: API | 4-6 hours | High |
| Phase 6: UI | 6-8 hours | High |
| Phase 7: Testing | 6-8 hours | High |
| Phase 8: Documentation | 3-4 hours | Medium |
| Phase 9: Quality | 4-5 hours | Medium |
| Phase 10: Final Review | 2-3 hours | High |
| **Total** | **45-60 hours** | - |

---

## Notes

- Start LM Studio with Qwen model before beginning Phase 3.2
- Ensure Python 3.12 is installed before Phase 1
- GPU is optional but recommended for faster inference
- All models will download automatically on first run (~2-3 GB total)
- Keep design document (DESIGN.md) as reference throughout implementation

---

**Status Legend:**
- `[ ]` Not Started
- `[~]` In Progress
- `[x]` Completed
- `[*]` Optional Task
