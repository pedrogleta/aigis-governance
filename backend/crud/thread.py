from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from models.thread import Thread, Message


class ThreadCRUD:
    @staticmethod
    def create_thread(db: Session, thread_id: str, created_at: datetime) -> Thread:
        db_thread = Thread(thread_id=thread_id, created_at=created_at)
        db.add(db_thread)
        db.commit()
        db.refresh(db_thread)
        return db_thread

    @staticmethod
    def get_thread_by_thread_id(db: Session, thread_id: str) -> Optional[Thread]:
        return db.query(Thread).filter(Thread.thread_id == thread_id).first()

    @staticmethod
    def add_message(
        db: Session,
        thread: Thread,
        sender: str,
        text: Optional[str],
        timestamp: datetime,
    ) -> Message:
        db_msg = Message(thread=thread, sender=sender, text=text, timestamp=timestamp)
        db.add(db_msg)
        db.commit()
        db.refresh(db_msg)
        return db_msg

    @staticmethod
    def get_thread_with_messages(db: Session, thread: Thread) -> Thread:
        # ensure messages are loaded
        db.refresh(thread)
        return thread


thread_crud = ThreadCRUD()
