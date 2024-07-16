from sqlalchemy.orm import Mapped

from .base import Base


class OpenInterest(Base):
    __main_columns__ = ["open_interest"]

    open_interest: Mapped[float]
