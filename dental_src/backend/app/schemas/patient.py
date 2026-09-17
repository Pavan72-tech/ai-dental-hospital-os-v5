from pydantic import BaseModel
class PatientCreate(BaseModel):
 name:str
 phone:str|None=None
 medical_history:str|None=None
