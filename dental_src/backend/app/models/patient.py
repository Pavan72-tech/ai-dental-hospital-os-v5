from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import String,Integer,Text
from app.database import Base
class Patient(Base):
 __tablename__='patients'
 id:Mapped[int]=mapped_column(Integer,primary_key=True)
 uhid:Mapped[str]=mapped_column(String(50),unique=True)
 name:Mapped[str]=mapped_column(String(160))
 phone:Mapped[str|None]=mapped_column(String(30),nullable=True)
 medical_history:Mapped[str|None]=mapped_column(Text,nullable=True)
