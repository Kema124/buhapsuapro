from __future__ import annotations

from contextlib import AbstractContextManager

from sqlalchemy.orm import Session

from database.db import get_session


class UnitOfWork(AbstractContextManager):
    """Unit of Work for transactional operations.

    Usage:
        with UnitOfWork() as uow:
            ... use uow.session ...
            uow.commit()

    If an exception happens, transaction is rolled back.
    """

    def __init__(self):
        self.session: Session = get_session()
        self._committed = False

    def commit(self) -> None:
        self.session.commit()
        self._committed = True

    def rollback(self) -> None:
        self.session.rollback()

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is not None:
                self.rollback()
            elif not self._committed:
                # default: commit on successful exit
                self.commit()
        finally:
            self.session.close()
        return False
