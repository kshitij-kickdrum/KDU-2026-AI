from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel


class ImageResponse(BaseModel):
    description: str
    objects_detected: list[str]
    scene_type: str
    confidence: str


parser = PydanticOutputParser(pydantic_object=ImageResponse)
