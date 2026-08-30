
from pydantic import BaseModel, Field


class WeatherReading(BaseModel):
  

    city: str = Field(..., min_length=1, description="City name")
    temperature: float = Field(..., description="Temperature in degrees Celsius")
    humidity: int = Field(..., ge=0, le=100, description="Humidity as a percentage")
    wind_speed: float = Field(..., ge=0, description="Wind speed in km/h")