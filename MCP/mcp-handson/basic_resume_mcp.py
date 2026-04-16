"""
Basic Resume Shortlister MCP Tool

This tool allows Claude to view and access resume PDFs for shortlisting candidates.
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
from typing import Annotated

import mcp.server.stdio
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import (
    TextContent,
    Tool,
    INVALID_PARAMS,
)
from pydantic import BaseModel, Field

from utils.resume_utils import read_resume, ensure_dir_exists

# Initialize the server
server = Server("resume_shortlister")

RESUME_DIR = os.environ.get("RESUME_DIR", "./assets")

@student_task("Define the ReadResume model")
class ReadResume(BaseModel):
    file_path: Annotated[str, Field(description="Path to the resume PDF file")]

@student_task("Define the ListResumes model")
class ListResumes(BaseModel):
    pass

@student_task("Implement the list_tools function")
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="read_resume",
            description="Read and extract text from a resume PDF file",
            inputSchema=ReadResume.model_json_schema(),
        ),
        Tool(
            name="list_resumes",
            description="List all available resume files",
            inputSchema=ListResumes.model_json_schema(),
        ),
    ]

@student_task("Implement the call_tool function")
@server.call_tool()
async def call_tool(name, arguments):    
    if name == "read_resume":
        try:
            args = ReadResume(**(arguments or {}))
        except ValueError as e:
            raise Exception(INVALID_PARAMS, str(e))
            
        file_path = args.file_path

        resume_text = read_resume(file_path, RESUME_DIR)
        if not resume_text:
            return [TextContent(type="text", text=f"Error: Could not read resume at {file_path}")]

        response = f"Resume: {file_path}\n\n{resume_text}"
        return [TextContent(type="text", text=response)]
    
    elif name == "list_resumes":
        ensure_dir_exists(RESUME_DIR)
        try:
            resume_files = sorted(
                file_name
                for file_name in os.listdir(RESUME_DIR)
                if file_name.lower().endswith(".pdf")
                and os.path.isfile(os.path.join(RESUME_DIR, file_name))
            )

            if not resume_files:
                return [TextContent(type="text", text="No resume files found in the directory")]

            response = f"Found {len(resume_files)} resume files:\n\n"
            for i, resume_file in enumerate(resume_files, 1):
                response += f"{i}. {resume_file}\n"

            return [TextContent(type="text", text=response)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error listing resumes: {str(e)}")]
    
    else:
        raise Exception(INVALID_PARAMS, f"Unknown tool: {name}")

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
                    server_name="resume_shortlister",
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
