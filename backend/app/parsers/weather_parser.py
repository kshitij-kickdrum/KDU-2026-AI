from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel


class WeatherResponse(BaseModel):
    temperature: str
    feels_like: str
    summary: str
    location: str
    advice: str


parser = PydanticOutputParser(pydantic_object=WeatherResponse)
