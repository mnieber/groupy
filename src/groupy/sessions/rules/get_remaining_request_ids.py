import typing as T

from groupy.groups.rules.get_active_chunks import get_active_chunks
from groupy.groups.rules.get_chunks import get_chunks
from groupy.sessions.models.config import Config
from groupy.sessions.models.session import Session
from groupy.sessions.rules.get_exclude_patterns import get_exclude_patterns
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_source_root import get_source_root


def get_remaining_request_ids(session: Session, config: Config) -> T.List[str]:
    # The request ids of the chunks of the next stage that are not finished
    chunks = get_active_chunks(
        get_chunks(
            get_source_root(), get_groupy_path("groups.txt"), config.max_chunk_lines
        ),
        get_exclude_patterns(),
    )
    request_ids = [f"{session.next_stage}/{chunk.id}" for chunk in chunks]
    return [
        request_id
        for request_id in request_ids
        if request_id not in session.finished_chunks
    ]
