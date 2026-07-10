from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Any, List

# 1. Cấu hình Database
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://user:password@localhost/pet_boarding_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. SQLAlchemy Model (Theo yêu cầu)
class BoardingSlot(Base):
    __tablename__ = "boarding_slots"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    slot_number = Column(String(50), unique=True, nullable=False, index=True)
    room_size = Column(String(30), nullable=False)
    price_per_day = Column(Float, nullable=False)
    status = Column(String(30), default="VACANT", nullable=False)

# 3. Pydantic Schemas với Validation
class BoardingSlotBase(BaseModel):
    slot_number: str
    room_size: str
    price_per_day: float = Field(gt=0)
    status: str = "VACANT"

    @field_validator("room_size")
    def validate_size(cls, v):
        if v not in ["SMALL", "MEDIUM", "LARGE"]:
            raise ValueError("room_size phải là SMALL, MEDIUM hoặc LARGE")
        return v

    @field_validator("status")
    def validate_status(cls, v):
        if v not in ["VACANT", "OCCUPIED"]:
            raise ValueError("status phải là VACANT hoặc OCCUPIED")
        return v

class BoardingSlotCreate(BoardingSlotBase): pass

# 4. Hàm Response chuẩn 6 trường
def create_response(status_code: int, message: str, data: Any = None, error: str = None, path: str = ""):
    return {
        "statusCode": status_code,
        "message": message,
        "error": error,
        "data": data,
        "path": path,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }

# 5. Khởi tạo App & API CRUD
app = FastAPI()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.post("/boarding-slots")
def create_slot(slot: BoardingSlotCreate, db: Session = next(get_db())):
    try:
        new_slot = BoardingSlot(**slot.model_dump())
        db.add(new_slot)
        db.commit()
        db.refresh(new_slot)
        return create_response(201, "Thêm khoang thành công", new_slot, path="/boarding-slots")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/boarding-slots")
def get_all(db: Session = next(get_db())):
    slots = db.query(BoardingSlot).all()
    return create_response(200, "Lấy danh sách thành công", slots, path="/boarding-slots")

@app.get("/boarding-slots/{slot_id}")
def get_one(slot_id: int, db: Session = next(get_db())):
    slot = db.query(BoardingSlot).filter(BoardingSlot.id == slot_id).first()
    if not slot:
        return create_response(404, "Slot not found", error="Not Found", path=f"/boarding-slots/{slot_id}")
    return create_response(200, "Lấy thông tin thành công", slot, path=f"/boarding-slots/{slot_id}")

@app.put("/boarding-slots/{slot_id}")
def update_slot(slot_id: int, data: BoardingSlotCreate, db: Session = next(get_db())):
    try:
        slot = db.query(BoardingSlot).filter(BoardingSlot.id == slot_id).first()
        if not slot:
            return create_response(404, "Slot not found", error="Not Found", path=f"/boarding-slots/{slot_id}")
        
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(slot, key, value)
            
        db.commit()
        db.refresh(slot)
        return create_response(200, "Cập nhật thành công", slot, path=f"/boarding-slots/{slot_id}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/boarding-slots/{slot_id}")
def delete_slot(slot_id: int, db: Session = next(get_db())):
    try:
        slot = db.query(BoardingSlot).filter(BoardingSlot.id == slot_id).first()
        if not slot:
            return create_response(404, "Slot not found", error="Not Found", path=f"/boarding-slots/{slot_id}")
        db.delete(slot)
        db.commit()
        return create_response(200, "Xóa khoang thành công", path=f"/boarding-slots/{slot_id}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
