from sqlalchemy.orm import Session
from .models import Change

def detect_change(db: Session, page_id: int, old_hash: str | None, new_hash: str):
    if old_hash is None:
        change_type = "NEW"
    elif old_hash != new_hash:
        change_type = "MODIFIED"
    else:
        change_type = "UNCHANGED"

    if change_type != "UNCHANGED":
        db.add(Change(page_id=page_id, change_type=change_type,
                      old_hash=old_hash, new_hash=new_hash))
    return change_type
