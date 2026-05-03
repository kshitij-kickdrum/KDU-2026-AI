"""Shared test configs."""

VALID_AGENTS_CONFIG = {
    "researcher": {
        "role": "Senior Research Analyst",
        "goal": "Gather information",
        "backstory": "You always cite sources.",
        "tools": ["failing_tool"],
    },
    "fact_checker": {
        "role": "Fact Verification Specialist",
        "goal": "Verify findings",
        "backstory": "You verify claims.",
        "tools": [],
    },
    "writer": {
        "role": "Technical Writer",
        "goal": "Write reports",
        "backstory": "You write clearly.",
        "tools": [],
    },
}

VALID_TASKS_CONFIG = {
    "research_task": {
        "description": "Research {topic}",
        "expected_output": "Findings",
        "agent": "researcher",
    },
    "fact_check_task": {
        "description": "Verify {research_results}",
        "expected_output": "Verification",
        "agent": "fact_checker",
    },
    "writing_task": {
        "description": "Write {fact_check_details}",
        "expected_output": "Document",
        "agent": "writer",
    },
}
