from app.tools.search_tool import SearchTool
from app.tools.weather_tool import WeatherTool


def test_external_tools_have_expected_schemas():
    weather = WeatherTool().schema
    search = SearchTool().schema
    assert weather["function"]["name"] == "get_weather"
    assert "location" in weather["function"]["parameters"]["properties"]
    assert search["function"]["name"] == "search"
    assert "query" in search["function"]["parameters"]["properties"]

