"""
LangChain utilities for resume processing
"""
import json
import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple

# To mark the functions that students are expected to implement
try:
    from _devtools import student_task
except ModuleNotFoundError:
    def student_task(_description: str = ""):
        def decorator(obj):
            return obj
        return decorator

# LangChain imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
except Exception:
    HuggingFaceEmbeddings = None
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS

logger = logging.getLogger(__name__)


def clamp_score(value: Any) -> int:
    """Normalize score values to an integer in [0, 100]."""
    try:
        numeric = int(round(float(value)))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, numeric))


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """Extract first JSON object from model output."""
    if not text:
        return None
    candidates = [text.strip()]
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    candidates.extend(fenced)
    bare = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if bare:
        candidates.append(bare.group(0))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return None


def _invoke_json_chain(prompt_template: str, inputs: Dict[str, Any], llm) -> Dict[str, Any]:
    """Run an LLM chain and parse JSON response with graceful fallback."""
    if not llm:
        return {"error": "LangChain LLM not available.", "raw": ""}

    try:
        prompt = PromptTemplate.from_template(prompt_template)
        chain = prompt | llm | StrOutputParser()
        raw = chain.invoke(inputs)
        parsed = _extract_json_object(raw)
        if parsed is None:
            return {"error": "Model did not return valid JSON.", "raw": raw}
        parsed["_raw"] = raw
        return parsed
    except Exception as e:
        return {"error": str(e), "raw": ""}


def _normalize_scored_result(
    parsed: Dict[str, Any],
    component_defaults: List[str],
) -> Dict[str, Any]:
    """Normalize scored analysis output into stable schema."""
    result: Dict[str, Any] = {
        "title": str(parsed.get("title", "Analysis")).strip() or "Analysis",
        "total_score": clamp_score(parsed.get("total_score", 0)),
        "components": [],
        "evidence": [],
        "recommendations": [],
        "summary": str(parsed.get("summary", "")).strip(),
        "raw": parsed.get("_raw", ""),
        "error": parsed.get("error", ""),
    }

    components = parsed.get("components", [])
    if isinstance(components, list):
        for component in components:
            if not isinstance(component, dict):
                continue
            result["components"].append(
                {
                    "name": str(component.get("name", "Component")).strip(),
                    "score": clamp_score(component.get("score", 0)),
                    "weight": clamp_score(component.get("weight", 0)),
                    "reason": str(component.get("reason", "")).strip(),
                }
            )

    present_names = {item["name"].lower() for item in result["components"]}
    for default_name in component_defaults:
        if default_name.lower() not in present_names:
            result["components"].append(
                {"name": default_name, "score": 0, "weight": 0, "reason": "Not provided by model."}
            )

    evidence = parsed.get("evidence", [])
    if isinstance(evidence, list):
        result["evidence"] = [str(item).strip() for item in evidence if str(item).strip()]

    recommendations = parsed.get("recommendations", [])
    if isinstance(recommendations, list):
        result["recommendations"] = [str(item).strip() for item in recommendations if str(item).strip()]

    if not result["summary"]:
        result["summary"] = "No summary provided."

    return result


def init_langchain_components(
    openrouter_api_key,
    chat_model="openai/gpt-4o-mini",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
):
    """Initialize LangChain components.
    
    Args:
        openrouter_api_key: OpenRouter API key for chat model
        chat_model: Chat model name
        embedding_model: Embedding model name
        
    Returns:
        tuple: (embeddings_or_none, llm_or_none)
    """
    llm = None
    embeddings = None
    if HuggingFaceEmbeddings is None:
        logger.error("HuggingFaceEmbeddings is unavailable in this Python environment.")
    else:
        try:
            embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        except Exception as e:
            logger.error(f"Error initializing Hugging Face embeddings: {e}")

    if openrouter_api_key:
        llm = ChatOpenAI(
            temperature=0,
            model=chat_model,
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    return embeddings, llm

def prepare_resume_documents(resume_text, filename):
    """
    Split resume text into chunks and wrap them as LangChain Document objects.
    
    Args:
        resume_text: Raw resume text
        filename: Name of the resume file
    
    Returns:
        dict: Contains original text and chunked Document list
    """
    # Step 1: Chunk the resume
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(resume_text)

    # Step 2: Wrap each chunk in a Document with metadata
    documents = [
        Document(page_content=chunk, metadata={"source": filename, "chunk_index": i})
        for i, chunk in enumerate(chunks)
    ]

    return {
        "text": resume_text,
        "chunks": documents
    }

def find_relevant_sections(processed_resume, job_description, embeddings):
    """
    Use FAISS vector store to find top 3 resume chunks most relevant to a job description.
    
    Args:
        processed_resume: Output of process_resume_with_langchain (includes chunks)
        job_description: Job description string
        embeddings: Embeddings object
    
    Returns:
        List of (chunk_text, similarity_score) tuples
    """
    if embeddings is None:
        return []

    # Build FAISS index from processed chunks
    vectorstore = FAISS.from_documents(processed_resume["chunks"], embeddings)

    # Perform semantic search
    results = vectorstore.similarity_search_with_score(job_description, k=3)

    # Return list of (text, score)
    return [(doc.page_content, score) for doc, score in results]


def detect_duplicates_with_embeddings(
    target_text: str,
    target_filename: str,
    corpus: List[Tuple[str, str]],
    embeddings,
    similarity_threshold: float = 0.82,
) -> Dict[str, Any]:
    """Detect near-duplicate resumes by cosine similarity over resume-level embeddings."""
    if embeddings is None:
        return {
            "duplicates": [],
            "note": "Embeddings unavailable; duplicate detection skipped.",
        }

    other_files = [item for item in corpus if item[0] != target_filename]
    if not other_files:
        return {"duplicates": [], "note": "No other resumes available for comparison."}

    try:
        target_vec = embeddings.embed_query(target_text)
        docs = [text for _, text in other_files]
        names = [name for name, _ in other_files]
        doc_vecs = embeddings.embed_documents(docs)
    except Exception as e:
        return {"duplicates": [], "note": f"Embedding generation failed: {str(e)}"}

    def cosine_similarity(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    scored = []
    for name, vec in zip(names, doc_vecs):
        similarity = cosine_similarity(target_vec, vec)
        scored.append({"file_path": name, "similarity": round(similarity, 4)})

    scored.sort(key=lambda item: item["similarity"], reverse=True)
    duplicates = [item for item in scored if item["similarity"] >= similarity_threshold]

    return {
        "duplicates": duplicates,
        "top_matches": scored[:5],
        "threshold": similarity_threshold,
    }

@student_task("Create a skill extraction chain")
def extract_skills_with_langchain(resume_text, llm):
    """Extract skills from resume text using LangChain.
    
    Args:
        resume_text: Resume text content
        llm: LangChain language model
        
    Returns:
        str: Extracted skills or error message
    """
    if not llm:
        return "LangChain LLM not available for skill extraction."
    
    try:
        prompt = PromptTemplate.from_template(
            """
            Extract the skills from the following resume.
            Organize them into categories:
            - Technical Skills
            - Soft Skills
            - Languages
            - Tools & Platforms

            Resume:
            {resume_text}

            Extracted Skills:
            """
        )

        chain = prompt | llm | StrOutputParser()
        skills = chain.invoke({"resume_text": resume_text})
        return skills
        
    except Exception as e:
        return f"Error extracting skills: {str(e)}"


@student_task("Create an assessment chain")
def assess_resume_for_job(resume_text, job_description, llm):
    """Assess how well a resume matches a job description.
    
    Args:
        resume_text: Resume text content
        job_description: Job description text
        llm: LangChain language model
        
    Returns:
        str: Assessment or error message
    """
    if not llm:
        return "LangChain LLM not available for resume assessment."
    
    try:
        prompt = PromptTemplate.from_template(
            """
            You are a skilled recruiter. Evaluate how well the following resume matches the job description.

            Resume:
            {resume_text}

            Job Description:
            {job_description}

            Provide an assessment with:
            1. Match Score (0-100)
            2. Matching Skills & Qualifications
            3. Missing Skills & Qualifications
            4. Overall Assessment
            """
        )

        chain = prompt | llm | StrOutputParser()
        assessment = chain.invoke(
            {"resume_text": resume_text, "job_description": job_description}
        )
        return assessment
        
    except Exception as e:
        return f"Error assessing resume: {str(e)}"


def ats_score_with_langchain(resume_text: str, job_description: str, llm) -> Dict[str, Any]:
    parsed = _invoke_json_chain(
        """
        You are an ATS scoring engine.
        Score the resume against the job description on a 0-100 scale with weighted components.
        Return ONLY valid JSON with this schema:
        {{
          "title": "ATS Score",
          "total_score": number,
          "summary": "string",
          "components": [
            {{"name":"Skills Match","score":number,"weight":number,"reason":"string"}},
            {{"name":"Experience Relevance","score":number,"weight":number,"reason":"string"}},
            {{"name":"Project Relevance","score":number,"weight":number,"reason":"string"}},
            {{"name":"Clarity & Structure","score":number,"weight":number,"reason":"string"}},
            {{"name":"ATS Formatting Risk","score":number,"weight":number,"reason":"string"}}
          ],
          "evidence": ["string"],
          "recommendations": ["string"]
        }}

        Resume:
        {resume_text}

        Job Description:
        {job_description}
        """,
        {"resume_text": resume_text, "job_description": job_description},
        llm,
    )
    return _normalize_scored_result(
        parsed,
        [
            "Skills Match",
            "Experience Relevance",
            "Project Relevance",
            "Clarity & Structure",
            "ATS Formatting Risk",
        ],
    )


def keyword_stuffing_with_langchain(resume_text: str, job_description: str, llm) -> Dict[str, Any]:
    parsed = _invoke_json_chain(
        """
        Detect keyword stuffing in the resume with respect to the job description.
        Return ONLY valid JSON:
        {{
          "title":"Keyword Stuffing Detection",
          "total_score": number,
          "summary":"string",
          "components":[
            {{"name":"Keyword Balance","score":number,"weight":number,"reason":"string"}},
            {{"name":"Context Quality","score":number,"weight":number,"reason":"string"}},
            {{"name":"Evidence Strength","score":number,"weight":number,"reason":"string"}}
          ],
          "evidence":["string"],
          "recommendations":["string"]
        }}
        Score 100 means low stuffing risk.

        Resume:
        {resume_text}

        Job Description:
        {job_description}
        """,
        {"resume_text": resume_text, "job_description": job_description},
        llm,
    )
    return _normalize_scored_result(
        parsed,
        ["Keyword Balance", "Context Quality", "Evidence Strength"],
    )


def project_quality_with_langchain(
    resume_text: str,
    llm,
    job_description: str = "",
) -> Dict[str, Any]:
    parsed = _invoke_json_chain(
        """
        Evaluate project quality from the resume.
        Return ONLY valid JSON:
        {{
          "title":"Project Quality Evaluation",
          "total_score": number,
          "summary":"string",
          "components":[
            {{"name":"Impact","score":number,"weight":number,"reason":"string"}},
            {{"name":"Ownership","score":number,"weight":number,"reason":"string"}},
            {{"name":"Complexity","score":number,"weight":number,"reason":"string"}},
            {{"name":"Outcome Clarity","score":number,"weight":number,"reason":"string"}}
          ],
          "evidence":["string"],
          "recommendations":["string"]
        }}

        Resume:
        {resume_text}

        Job Description (optional context):
        {job_description}
        """,
        {"resume_text": resume_text, "job_description": job_description or "Not provided"},
        llm,
    )
    return _normalize_scored_result(parsed, ["Impact", "Ownership", "Complexity", "Outcome Clarity"])


def red_flags_with_langchain(resume_text: str, llm) -> Dict[str, Any]:
    return _invoke_json_chain(
        """
        Detect resume red flags and rank by severity.
        Return ONLY valid JSON:
        {{
          "title":"Resume Red-Flag Detector",
          "summary":"string",
          "findings":[
            {{"issue":"string","severity":"low|medium|high","confidence":"low|medium|high","evidence":"string"}}
          ],
          "recommendations":["string"]
        }}

        Resume:
        {resume_text}
        """,
        {"resume_text": resume_text},
        llm,
    )


def interview_questions_with_langchain(
    resume_text: str,
    job_description: str,
    llm,
    question_count: int = 8,
) -> Dict[str, Any]:
    count = max(4, min(20, int(question_count)))
    return _invoke_json_chain(
        """
        Generate personalized interview questions based on the resume and role.
        Return ONLY valid JSON:
        {{
          "title":"Interview Question Generator",
          "summary":"string",
          "technical_questions":[{{"question":"string","reason":"string"}}],
          "behavioral_questions":[{{"question":"string","reason":"string"}}]
        }}
        Generate exactly {question_count} total questions, split roughly evenly.

        Resume:
        {resume_text}

        Job Description:
        {job_description}
        """,
        {
            "resume_text": resume_text,
            "job_description": job_description,
            "question_count": count,
        },
        llm,
    )
