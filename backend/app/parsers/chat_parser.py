from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel


class GeneralResponse(BaseModel):
    answer: str
    follow_up: str | None = None


parser = PydanticOutputParser(pydantic_object=GeneralResponse)
