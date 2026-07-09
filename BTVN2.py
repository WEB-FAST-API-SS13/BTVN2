from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, Integer, String, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import Optional

# 1. Cấu hình Database (Thay bằng thông tin DB của bạn)
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://user:password@localhost/db_name"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# 2. Model Discount (Có thêm trường is_deleted cho yêu cầu sáng tạo)
class DiscountModel(Base):
    __tablename__ = "discounts"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True)
    is_deleted = Column(Boolean, default=False)  # Sáng tạo: Xóa mềm

# 3. Dependency lấy session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 4. Service Layer (Quy tắc 4)
def delete_discount_service(db: Session, discount_id: int):
    # Quy tắc 1 & 2: Kiểm tra tồn tại
    discount = db.query(DiscountModel).filter(
        DiscountModel.id == discount_id, 
        DiscountModel.is_deleted == False
    ).first()
    
    if not discount:
        raise HTTPException(status_code=404, detail="Mã giảm giá không tồn tại hoặc đã bị xóa")
    
    # Thực hiện xóa mềm (Sáng tạo)
    discount.is_deleted = True
    
    # Quy tắc 3: Phải gọi commit()
    db.commit()
    return {"message": "Xóa mã giảm giá thành công"}

# 5. API Router
app = FastAPI()

@app.delete("/discounts/{discount_id}")
def delete_discount(discount_id: int, db: Session = Depends(get_db)):
    return delete_discount_service(db, discount_id)