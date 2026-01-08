from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Werknemer(Base):
    __tablename__ = "werknemers"

    id = Column(Integer, primary_key=True)
    naam = Column(String, nullable=False)
    adres = Column(String)
    uursalaris = Column(Float, nullable=False)

    uren = relationship("Uur", back_populates="werknemer")

class Uur(Base):
    __tablename__ = "uren"

    id = Column(Integer, primary_key=True)
    werknemer_id = Column(Integer, ForeignKey("werknemers.id"))
    periode = Column(String, nullable=False)
    aantal_uren = Column(Float, nullable=False)

    werknemer = relationship("Werknemer", back_populates="uren")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
