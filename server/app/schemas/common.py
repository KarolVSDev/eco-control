from pydantic import BaseModel
from typing import Any
class Page(BaseModel): items: list[Any]; total: int; page: int; page_size: int
