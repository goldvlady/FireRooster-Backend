from pydantic import BaseModel
from typing import Optional, List, Dict

class FilterModel(BaseModel):
    state_id: Optional[List[int]] = None
    county_id: Optional[List[int]] = None
    page: Optional[int] = 1
    limit: Optional[int] = 10
    

class PurchaseScannerModel(BaseModel):
    scanner_list: List[dict]