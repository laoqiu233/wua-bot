from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Wua(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    size: int
    wu_size: int
    a_size: int
    author: str
    chat: str
