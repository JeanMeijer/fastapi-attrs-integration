from dataclasses import dataclass
from datetime import datetime

from attrs import define
from fastapi import FastAPI

from schema.schema import AppSchema

app = FastAPI()


@define
@dataclass
class DirectionModel:
    origin: str
    destination: str


@define
class FlightModel:
    flight_number: int
    origin: str
    destination: str
    departure_time: datetime
    nested: DirectionModel


app_schema = AppSchema()

directions_responses = {
    200: app_schema.ref(DirectionModel)
}


@app.get("/directions", responses=directions_responses)
async def directions():
    return DirectionModel(origin="origin", destination="destination")


@app.get("/flights", responses={200: app_schema.ref(FlightModel)}, status_code=200)
async def flights():
    return FlightModel(flight_number=123, origin="origin", destination="destination", departure_time=datetime.now(),
                       nested=DirectionModel(origin="origin", destination="destination"))


app_schema.add_component_schema(app)
