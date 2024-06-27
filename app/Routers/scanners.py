from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from database import AsyncSessionLocal
from sqlalchemy.orm import Session
from typing import List, Annotated

from app.Utils.download_audios import download
from app.Utils.remove_space import process_audio
from app.Utils.whisper import stt_archive
from app.Utils.scanners import update_scanners, validate_tier_limit
from app.Utils.auth import get_current_user
from app.Models.ScannerModel import FilterModel, PurchaseScannerModel
from schema import User
import app.Utils.crud as crud


router = APIRouter()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
        

@router.get('/update-scanners')
async def get_scanners_router(user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    scanner_lists = await update_scanners(db, 1)
    return scanner_lists

@router.post('/get-scanners-by-filter')
async def get_scanners_by_filter(model: FilterModel, user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    data = await crud.get_scanners_by_filter(db, model)
    total = await crud.get_total_scanners(db)
    return {"data": data, "pagination": {"total": total}}

@router.get('/get-state-and-county-list')
async def get_state_and_county_list_router(user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    data = await crud.get_state_and_county_list(db)
    return data

@router.get('/get-my-scanners')
async def get_my_scanner_router(model: FilterModel, user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    purchased_scanner_list = await crud.get_purchased_scanners_by_user(db, user.id)
    
    my_scanner_list = []
    for purchased_scanner in purchased_scanner_list:
        print("purchased_scanner.scanner_id: ", purchased_scanner.scanner_id)
        scanner = await crud.get_scanner_by_scanner_id(db, purchased_scanner.scanner_id)
        
        if model.state_id and (scanner.state_id not in model.state_id):
            continue
        
        if model.county_id and (scanner.county_id not in model.county_id):
            continue
            
        print(model.county_id, scanner.county_id)
        my_scanner_list.append(scanner)
    start = (model.page - 1) * model.limit
    my_scanner_list = my_scanner_list[start: start+model.limit]
    return my_scanner_list
    
@router.get('/purchase-scanners')
async def purchase_scanners_router(model: PurchaseScannerModel, user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    
    scanner_list = model.scanner_list
    print(scanner_list)
    
    # await crud.delete_purchased_scanners_by_user_id(db, user.id)
    usertype = await crud.get_user_type_by_id(db, user.user_type_id)
    
    if not validate_tier_limit(usertype, scanner_list):
        return {"status": "Exceed package limit!"}
    
    for scanner in scanner_list:
        scanner_id = scanner['scanner_id']
        try:
            await crud.insert_purchased_scanners(db, user.id, scanner_id)
        except Exception as e:
            print(e)
    return True