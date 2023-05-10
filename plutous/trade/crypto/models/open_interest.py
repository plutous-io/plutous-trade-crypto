from sqlalchemy.orm import Mapped

from .base import Base


class OpenInterest(Base):
    open_interest: Mapped[float]
