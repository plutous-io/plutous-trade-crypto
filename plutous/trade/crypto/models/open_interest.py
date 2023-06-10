from sqlalchemy.orm import Mapped

from .base import Base


class OpenInterest(Base):
    __main_column__ = "open_interest"

    open_interest: Mapped[float]
