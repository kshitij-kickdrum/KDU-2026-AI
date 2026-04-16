"""
Enhanced Resume Shortlister MCP Tool with LangChain

This tool extends the basic resume shortlister with LangChain capabilities for
resume analysis, skill extraction, and job matching.
"""

# To mark the functions that students are expected to implement
try:
    from _devtools import student_task
except ModuleNotFoundError:
    def student_task(_description: str = ""):
        def decorator(obj):
            return obj
        return decorator

import asyncio
import os
from pathlib import Path
from typing import Annotated, Any, Dict

import mcp.server.stdio
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.shared.exceptions import McpError
from mcp.types import (
    TextContent,
    Tool,
    INVALID_PARAMS,
)
from pydantic import BaseModel, Field

from utils.resume_utils import read_resume, ensure_dir_exists
from utils.langchain_utils import (
    init_langchain_components,
    prepare_resume_documents,
    find_relevant_sections,
    extract_skills_with_langchain,
    assess_resume_for_job,
    ats_score_with_langchain,
    keyword_stuffing_with_langchain,
    project_quality_with_langchain,
    red_flags_with_langchain,
    detect_duplicates_with_embeddings,
    interview_questions_with_langchain,
)

from dotenv import load_dotenv

# Load dotenv from explicit path to support Claude Desktop launches.
DEFAULT_ENV_PATH = Path(__file__).resolve().parents[1] / "solutions" / ".env"
ENV_FILE_PATH = Path(os.environ.get("SECRETS_ENV_FILE", str(DEFAULT_ENV_PATH)))
load_dotenv(dotenv_path=ENV_FILE_PATH, override=False)

# Initialize the server
server = Server("resume_shortlister_enhanced")

RESUME_DIR = os.environ.get("RESUME_DIR", "./assets")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPEN_API_KEY", "")
HF_EMBEDDING_MODEL = os.environ.get("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Hint: Use the init_langchain_components function
embeddings, llm = init_langchain_components(
    openrouter_api_key=OPENROUTER_API_KEY,
    embedding_model=HF_EMBEDDING_MODEL,
)

@student_task("Create a resume-job matching chain")
class MatchResume(BaseModel):
    file_path: Annotated[str, Field(description="Path to the resume PDF file")]
    job_description: Annotated[str, Field(description="Job description to match against")]

@student_task("Create a skill extraction chain")
class ExtractSkills(BaseModel):
    file_path: Annotated[str, Field(description="Path to the resume PDF file")]

class AtsScoreResume(BaseModel):
    file_path: Annotated[str, Field(description="Path to the resume PDF file")]
    job_description: Annotated[str, Field(description="Job description to score against")]

class DetectKeywordStuffing(BaseModel):
    file_path: Annotated[str, Field(description="Path to the resume PDF file")]
    job_description: Annotated[str, Field(description="Job description for keyword comparison")]

class EvaluateProjectQuality(BaseModel):
    file_path: Annotated[str, Field(description="Path to the resume PDF file")]
    job_description: Annotated[str | None, Field(default=None, description="Optional job description context")]

class DetectResumeRedFlags(BaseModel):
    file_path: Annotated[str, Field(description="Path to the resume PDF file")]

class DetectDuplicateCandidate(BaseModel):
    file_path: Annotated[str, Field(description="Path to the resume PDF file")]

class GenerateInterviewQuestions(BaseModel):
    file_path: Annotated[str, Field(description="Path to the resume PDF file")]
    job_description: Annotated[str, Field(description="Job description context")]
    question_count: Annotated[int, Field(default=8, ge=4, le=20, description="Total number of questions")]

def _resolve_resume_path(file_path: str) -> str:
    return os.path.join(RESUME_DIR, file_path) if not os.path.isabs(file_path) else file_path

def _load_resume_text(file_path: str) -> str:
    full_path = _resolve_resume_path(file_path)
    if not os.path.exists(full_path):
        raise McpError(INVALID_PARAMS, f"Resume file not found: {file_path}")
    resume_text = read_resume(file_path, RESUME_DIR)
    if not resume_text:
        raise McpError(INVALID_PARAMS, f"Failed to read resume: {file_path}")
    return resume_text

def _format_scored_response(header: str, result: Dict[str, Any]) -> str:
    lines = [header]
    if result.get("error"):
        lines.append(f"\nError: {result['error']}")
        if result.get("raw"):
            lines.append(f"\nRaw Model Output:\n{result['raw']}")
        return "\n".join(lines)

    lines.append(f"\nTotal Score: {int(result.get('total_score', 0))}/100")
    lines.append(f"\nSummary: {result.get('summary', 'No summary provided.')}")

    components = result.get("components", [])
    if components:
        lines.append("\nComponent Scores:")
        for item in components:
            lines.append(
                f"- {item.get('name', 'Component')}: {int(item.get('score', 0))}/100 "
                f"(Weight {int(item.get('weight', 0))}%)"
            )
            reason = str(item.get("reason", "")).strip()
            if reason:
                lines.append(f"  Reason: {reason}")

    evidence = result.get("evidence", [])
    if evidence:
        lines.append("\nEvidence Snippets:")
        for item in evidence:
            lines.append(f"- {item}")

    recommendations = result.get("recommendations", [])
    if recommendations:
        lines.append("\nRecommendations:")
        for item in recommendations:
            lines.append(f"- {item}")

    return "\n".join(lines)

def _format_json_like_response(header: str, payload: Dict[str, Any], list_key: str) -> str:
    lines = [header]
    if payload.get("error"):
        lines.append(f"\nError: {payload['error']}")
        if payload.get("raw"):
            lines.append(f"\nRaw Model Output:\n{payload['raw']}")
        return "\n".join(lines)

    lines.append(f"\nSummary: {payload.get('summary', 'No summary provided.')}")
    items = payload.get(list_key, [])
    if isinstance(items, list) and items:
        lines.append("\nFindings:")
        for item in items:
            if isinstance(item, dict):
                issue = item.get("issue") or item.get("question") or str(item)
                severity = item.get("severity")
                confidence = item.get("confidence")
                reason = item.get("reason") or item.get("evidence")
                meta = []
                if severity:
                    meta.append(f"severity={severity}")
                if confidence:
                    meta.append(f"confidence={confidence}")
                meta_text = f" ({', '.join(meta)})" if meta else ""
                lines.append(f"- {issue}{meta_text}")
                if reason:
                    lines.append(f"  Note: {reason}")
            else:
                lines.append(f"- {item}")

    recommendations = payload.get("recommendations", [])
    if isinstance(recommendations, list) and recommendations:
        lines.append("\nRecommendations:")
        for item in recommendations:
            lines.append(f"- {item}")
    return "\n".join(lines)

@student_task("Implement the list_tools function")
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="match_resume",
            description="Match a resume against a job description",
            inputSchema=MatchResume.model_json_schema(),
        ),
        Tool(
            name="extract_skills",
            description="Extract skills from a resume",
            inputSchema=ExtractSkills.model_json_schema(),
        ),
        Tool(
            name="ats_score_resume",
            description="Generate ATS-style scoring of a resume against a job description",
            inputSchema=AtsScoreResume.model_json_schema(),
        ),
        Tool(
            name="detect_keyword_stuffing",
            description="Detect keyword stuffing and low-evidence buzzword repetition",
            inputSchema=DetectKeywordStuffing.model_json_schema(),
        ),
        Tool(
            name="evaluate_project_quality",
            description="Score project quality for impact, ownership, complexity, and outcomes",
            inputSchema=EvaluateProjectQuality.model_json_schema(),
        ),
        Tool(
            name="detect_resume_red_flags",
            description="Detect red flags such as gaps, inconsistencies, and vague claims",
            inputSchema=DetectResumeRedFlags.model_json_schema(),
        ),
        Tool(
            name="detect_duplicate_candidate",
            description="Detect near-duplicate resumes across all local resumes",
            inputSchema=DetectDuplicateCandidate.model_json_schema(),
        ),
        Tool(
            name="generate_interview_questions",
            description="Generate personalized technical and behavioral interview questions",
            inputSchema=GenerateInterviewQuestions.model_json_schema(),
        ),
    ]

@student_task("Implement the call_tool function")
@server.call_tool()
async def call_tool(name, arguments):
    
    if name == "match_resume":
        try:
            args = MatchResume(**(arguments or {}))
        except ValueError as e:
            raise McpError(INVALID_PARAMS, str(e))
            
        file_path = args.file_path
        job_description = args.job_description
        
        filename = os.path.basename(file_path)
        
        # Step 1: Read raw text
        resume_text = _load_resume_text(file_path)
        
        # Step 2: Chunk and wrap in Documents (no embedding here)
        processed_resume = prepare_resume_documents(resume_text, filename)

        # Step 3: Find relevant sections using FAISS (embeddings happen here)
        embedding_warning = ""
        try:
            relevant_sections = find_relevant_sections(processed_resume, job_description, embeddings)
        except Exception as e:
            relevant_sections = []
            embedding_warning = f"Embedding search unavailable: {str(e)}"

        # Step 4: Ask LLM for assessment
        assessment = assess_resume_for_job(resume_text, job_description, llm)

        # Step 5: Return the formatted response
        response = f"Resume-Job Match Analysis for '{file_path}':\n\n"

        if relevant_sections:
            response += "Most relevant resume sections for this job:\n\n"
            for i, (section, similarity) in enumerate(relevant_sections, 1):
                response += f"Relevant Section {i} (Similarity score: {similarity:.4f}):\n{section}\n\n"
        else:
            if embeddings is None:
                response += "No embedding-based relevant sections found (embedding model failed to initialize).\n\n"
            elif embedding_warning:
                response += f"{embedding_warning}\n\n"
            else:
                response += "No embedding-based relevant sections found for this job description.\n\n"

        response += "Full Assessment:\n\n"
        response += assessment

        return [TextContent(type="text", text=response)]
    
    elif name == "extract_skills":
        try:
            args = ExtractSkills(**(arguments or {}))
        except ValueError as e:
            raise McpError(INVALID_PARAMS, str(e))
            
        file_path = args.file_path
        
        # Read the resume
        resume_text = _load_resume_text(file_path)
            
        skills = extract_skills_with_langchain(resume_text, llm)

        response = f"Skills Extracted from '{file_path}':\n\n{skills}"
        return [TextContent(type="text", text=response)]

    elif name == "ats_score_resume":
        try:
            args = AtsScoreResume(**(arguments or {}))
        except ValueError as e:
            raise McpError(INVALID_PARAMS, str(e))

        resume_text = _load_resume_text(args.file_path)
        result = ats_score_with_langchain(resume_text, args.job_description, llm)
        response = _format_scored_response(f"ATS Scoring for '{args.file_path}'", result)
        return [TextContent(type="text", text=response)]

    elif name == "detect_keyword_stuffing":
        try:
            args = DetectKeywordStuffing(**(arguments or {}))
        except ValueError as e:
            raise McpError(INVALID_PARAMS, str(e))

        resume_text = _load_resume_text(args.file_path)
        result = keyword_stuffing_with_langchain(resume_text, args.job_description, llm)
        response = _format_scored_response(f"Keyword Stuffing Analysis for '{args.file_path}'", result)
        return [TextContent(type="text", text=response)]

    elif name == "evaluate_project_quality":
        try:
            args = EvaluateProjectQuality(**(arguments or {}))
        except ValueError as e:
            raise McpError(INVALID_PARAMS, str(e))

        resume_text = _load_resume_text(args.file_path)
        result = project_quality_with_langchain(resume_text, llm, args.job_description or "")
        response = _format_scored_response(f"Project Quality Evaluation for '{args.file_path}'", result)
        return [TextContent(type="text", text=response)]

    elif name == "detect_resume_red_flags":
        try:
            args = DetectResumeRedFlags(**(arguments or {}))
        except ValueError as e:
            raise McpError(INVALID_PARAMS, str(e))

        resume_text = _load_resume_text(args.file_path)
        result = red_flags_with_langchain(resume_text, llm)
        response = _format_json_like_response(
            f"Resume Red-Flag Analysis for '{args.file_path}'",
            result,
            "findings",
        )
        return [TextContent(type="text", text=response)]

    elif name == "detect_duplicate_candidate":
        try:
            args = DetectDuplicateCandidate(**(arguments or {}))
        except ValueError as e:
            raise McpError(INVALID_PARAMS, str(e))

        target_text = _load_resume_text(args.file_path)
        all_pdfs = sorted(
            file_name
            for file_name in os.listdir(RESUME_DIR)
            if file_name.lower().endswith(".pdf")
            and os.path.isfile(os.path.join(RESUME_DIR, file_name))
        )
        corpus = []
        for pdf_file in all_pdfs:
            text = read_resume(pdf_file, RESUME_DIR)
            if text:
                corpus.append((pdf_file, text))

        result = detect_duplicates_with_embeddings(
            target_text=target_text,
            target_filename=os.path.basename(args.file_path),
            corpus=corpus,
            embeddings=embeddings,
        )

        lines = [f"Duplicate Candidate Detection for '{args.file_path}'"]
        note = result.get("note")
        if note:
            lines.append(f"\nNote: {note}")
        duplicates = result.get("duplicates", [])
        if duplicates:
            lines.append("\nPotential Duplicates:")
            for item in duplicates:
                lines.append(f"- {item['file_path']}: similarity={item['similarity']}")
        else:
            lines.append("\nNo likely duplicates found above threshold.")
        top_matches = result.get("top_matches", [])
        if top_matches:
            lines.append("\nTop Similar Resumes:")
            for item in top_matches:
                lines.append(f"- {item['file_path']}: similarity={item['similarity']}")
        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "generate_interview_questions":
        try:
            args = GenerateInterviewQuestions(**(arguments or {}))
        except ValueError as e:
            raise McpError(INVALID_PARAMS, str(e))

        resume_text = _load_resume_text(args.file_path)
        result = interview_questions_with_langchain(
            resume_text=resume_text,
            job_description=args.job_description,
            llm=llm,
            question_count=args.question_count,
        )
        if result.get("error"):
            response = _format_json_like_response(
                f"Interview Question Generation for '{args.file_path}'",
                result,
                "technical_questions",
            )
            return [TextContent(type="text", text=response)]

        lines = [f"Interview Questions for '{args.file_path}'"]
        lines.append(f"\nSummary: {result.get('summary', 'No summary provided.')}")
        technical = result.get("technical_questions", [])
        behavioral = result.get("behavioral_questions", [])
        if technical:
            lines.append("\nTechnical Questions:")
            for idx, q in enumerate(technical, 1):
                if isinstance(q, dict):
                    lines.append(f"{idx}. {q.get('question', '')}")
                    reason = str(q.get("reason", "")).strip()
                    if reason:
                        lines.append(f"   Why: {reason}")
                else:
                    lines.append(f"{idx}. {q}")
        if behavioral:
            lines.append("\nBehavioral Questions:")
            for idx, q in enumerate(behavioral, 1):
                if isinstance(q, dict):
                    lines.append(f"{idx}. {q.get('question', '')}")
                    reason = str(q.get("reason", "")).strip()
                    if reason:
                        lines.append(f"   Why: {reason}")
                else:
                    lines.append(f"{idx}. {q}")
        return [TextContent(type="text", text="\n".join(lines))]
    
    else:
        raise McpError(INVALID_PARAMS, f"Unknown tool: {name}")

async def main():
    """Main entry point for the MCP server."""
    try:        
        ensure_dir_exists(RESUME_DIR)
        
        # Start the server
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="resume_shortlister_enhanced",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except Exception as e:
        raise

if __name__ == "__main__":
    asyncio.run(main())
