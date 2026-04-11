from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser

from app.core.config import settings
from app.core.exceptions import ParseError
from app.core.llm import build_chat_model
from app.core.logging import get_logger

logger = get_logger(__name__)

_fix_llm = build_chat_model(
    model=settings.text_model,
    api_key=settings.text_model_api_key,
)

_FIX_PROMPT = (
    "The following response could not be parsed as valid JSON.\n\n"
    "Error: {error}\n\n"
    "Bad output:\n{bad_output}\n\n"
    "Return a corrected version that strictly follows this schema:\n{format_instructions}\n\n"
    "Reply with valid JSON only. No explanation, no extra text."
)


def parse_with_retry(raw: str, parser: PydanticOutputParser) -> dict:
    retries = 0
    bad_output = raw
    last_error = ""

    while retries <= settings.max_parser_retries:
        try:
            parsed = parser.parse(bad_output)
            if retries > 0:
                logger.info("parse succeeded after retry", retries=retries)
            return parsed.model_dump()
        except OutputParserException as exc:
            last_error = str(exc)
            retries += 1

            if retries > settings.max_parser_retries:
                break

            logger.warning("parse failed, retrying", attempt=retries, error=last_error)

            fix_prompt = _FIX_PROMPT.format(
                error=last_error,
                bad_output=bad_output,
                format_instructions=parser.get_format_instructions(),
            )
            response = _fix_llm.invoke(fix_prompt)
            bad_output = response.content

    logger.error("parse failed after max retries", retries=retries)
    raise ParseError()
