from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Extra


class Git(BaseModel):
    uri: str
    branch: str = "main"
    paths: Optional[list[Path]]
    ignore_paths: Optional[list[Path]]

    class Config:
        extra = Extra.allow
