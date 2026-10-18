from dataclassy import dataclass


@dataclass
class LastRun:
    stage: str
    result: str
    request_id: str = ""
    error: str = ""
