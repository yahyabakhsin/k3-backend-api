from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Violation(Base):
    __tablename__ = "violations" 

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(50))
    id_pekerja = Column(String(50))
    violation_type = Column(String(100))
    image_path = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.now)