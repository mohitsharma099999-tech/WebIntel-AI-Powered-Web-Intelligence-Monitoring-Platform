from enum import StrEnum

from sqlalchemy.orm import Session

from .models import Change


class ChangeType(StrEnum):
    NEW = "NEW"
    MODIFIED = "MODIFIED"
    UNCHANGED = "UNCHANGED"


def detect_change(
    db: Session,
    page_id: int,
    old_hash: str | None,
    new_hash: str,
) -> ChangeType:
    if old_hash is None:
        ctype = ChangeType.NEW
    elif old_hash != new_hash:
        ctype = ChangeType.MODIFIED
    else:
        ctype = ChangeType.UNCHANGED

    if ctype is not ChangeType.UNCHANGED:
        db.add(Change(
            page_id=page_id,
            change_type=ctype.value,
            old_hash=old_hash,
            new_hash=new_hash,
        ))
    return ctype
