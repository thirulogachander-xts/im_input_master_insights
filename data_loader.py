import pandas as pd
from sqlalchemy.orm import Session
from .database import engine, Base, SessionLocal
from .models import InputMaster
import os

def load_data():
    Base.metadata.create_all(bind=engine)
    
    csv_path = os.path.join(os.path.dirname(__file__), "tbl_input_master_repository.csv")
    
    if not os.path.exists(csv_path):
        return False, f"CSV file not found at {csv_path}"

    # Try different encodings
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_path, encoding='utf-16')
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, encoding='latin-1')
    
    db = SessionLocal()
    try:
        db.query(InputMaster).delete()
        
        df = df.where(pd.notnull(df), None)
        records = df.to_dict(orient="records")
        
        for record in records:
            if "Table name - tbl_report_master_repository" in record:
                record["table_name_ref"] = record.pop("Table name - tbl_report_master_repository")
        
        db.bulk_insert_mappings(InputMaster, records)
        db.commit()
        return True, f"Successfully loaded {len(records)} records."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()
