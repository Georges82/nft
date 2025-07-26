from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime, date
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class ProjectStatus(str, Enum):
    QUOTED = "quoted"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    PAID = "paid"
    CANCELLED = "cancelled"

class ProjectType(str, Enum):
    KITCHEN_CABINETS = "kitchen_cabinets"
    CUSTOM_FURNITURE = "custom_furniture"
    BUILT_INS = "built_ins"
    DOORS_WINDOWS = "doors_windows"
    FLOORING = "flooring"
    DECKING = "decking"
    REPAIRS = "repairs"
    OTHER = "other"

class PaymentType(str, Enum):
    DEPOSIT = "deposit"
    PROGRESS_PAYMENT = "progress_payment"
    FINAL_PAYMENT = "final_payment"
    FULL_PAYMENT = "full_payment"

# Models
class CostItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str  # materials, labor, equipment, overhead
    description: str
    quantity: float = 1.0
    unit_cost: float
    total_cost: float
    date_added: datetime = Field(default_factory=datetime.utcnow)

class PaymentRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: PaymentType
    amount: float
    date_received: date
    description: Optional[str] = None
    invoice_number: Optional[str] = None

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_name: str
    client_name: str
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    project_type: ProjectType
    description: str
    status: ProjectStatus = ProjectStatus.QUOTED
    
    # Financial data
    quoted_amount: float = 0.0
    costs: List[CostItem] = []
    payments: List[PaymentRecord] = []
    
    # Dates
    start_date: Optional[date] = None
    expected_completion: Optional[date] = None
    actual_completion: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProjectCreate(BaseModel):
    project_name: str
    client_name: str
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    project_type: ProjectType
    description: str
    quoted_amount: float = 0.0
    start_date: Optional[date] = None
    expected_completion: Optional[date] = None

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    project_type: Optional[ProjectType] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    quoted_amount: Optional[float] = None
    start_date: Optional[date] = None
    expected_completion: Optional[date] = None
    actual_completion: Optional[date] = None

class CostItemCreate(BaseModel):
    category: str
    description: str
    quantity: float = 1.0
    unit_cost: float

class PaymentCreate(BaseModel):
    type: PaymentType
    amount: float
    date_received: date
    description: Optional[str] = None
    invoice_number: Optional[str] = None

class DashboardStats(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int
    total_revenue: float
    total_costs: float
    total_profit: float
    pending_payments: float

# Helper functions
def calculate_project_totals(project_dict):
    total_costs = sum(cost.get('total_cost', 0) for cost in project_dict.get('costs', []))
    total_payments = sum(payment.get('amount', 0) for payment in project_dict.get('payments', []))
    profit_loss = total_payments - total_costs
    
    return {
        'total_costs': total_costs,
        'total_payments': total_payments, 
        'profit_loss': profit_loss,
        'outstanding_amount': project_dict.get('quoted_amount', 0) - total_payments
    }

# Routes
@api_router.get("/")
async def root():
    return {"message": "Joinery Project Management API"}

# Dashboard
@api_router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats():
    try:
        projects = await db.projects.find().to_list(1000)
        
        total_projects = len(projects)
        active_projects = len([p for p in projects if p.get('status') in ['confirmed', 'in_progress']])
        completed_projects = len([p for p in projects if p.get('status') == 'completed'])
        
        total_revenue = 0
        total_costs = 0
        pending_payments = 0
        
        for project in projects:
            totals = calculate_project_totals(project)
            total_revenue += totals['total_payments']
            total_costs += totals['total_costs']
            if project.get('status') not in ['paid', 'cancelled']:
                pending_payments += totals['outstanding_amount']
        
        total_profit = total_revenue - total_costs
        
        return DashboardStats(
            total_projects=total_projects,
            active_projects=active_projects,
            completed_projects=completed_projects,
            total_revenue=total_revenue,
            total_costs=total_costs,
            total_profit=total_profit,
            pending_payments=pending_payments
        )
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Error fetching dashboard statistics")

# Projects
@api_router.post("/projects", response_model=Project)
async def create_project(project_data: ProjectCreate):
    try:
        project_dict = project_data.dict()
        project = Project(**project_dict)
        
        # Convert date objects to strings for MongoDB storage
        project_dict_for_db = project.dict()
        for key, value in project_dict_for_db.items():
            if isinstance(value, date) and not isinstance(value, datetime):
                project_dict_for_db[key] = value.isoformat()
        
        await db.projects.insert_one(project_dict_for_db)
        return project
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail="Error creating project")

@api_router.get("/projects", response_model=List[Dict])
async def get_projects():
    try:
        projects = await db.projects.find().sort("created_at", -1).to_list(1000)
        
        # Add calculated fields
        for project in projects:
            totals = calculate_project_totals(project)
            project.update(totals)
        
        return projects
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        raise HTTPException(status_code=500, detail="Error fetching projects")

@api_router.get("/projects/{project_id}", response_model=Dict)
async def get_project(project_id: str):
    try:
        project = await db.projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        totals = calculate_project_totals(project)
        project.update(totals)
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project: {e}")
        raise HTTPException(status_code=500, detail="Error fetching project")

@api_router.put("/projects/{project_id}", response_model=Dict)
async def update_project(project_id: str, project_data: ProjectUpdate):
    try:
        update_dict = {k: v for k, v in project_data.dict().items() if v is not None}
        update_dict['updated_at'] = datetime.utcnow()
        
        # Convert date objects to strings for MongoDB storage
        for key, value in update_dict.items():
            if isinstance(value, date) and not isinstance(value, datetime):
                update_dict[key] = value.isoformat()
        
        result = await db.projects.update_one(
            {"id": project_id}, 
            {"$set": update_dict}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        updated_project = await db.projects.find_one({"id": project_id})
        totals = calculate_project_totals(updated_project)
        updated_project.update(totals)
        return updated_project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail="Error updating project")

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    try:
        result = await db.projects.delete_one({"id": project_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail="Error deleting project")

# Cost Items
@api_router.post("/projects/{project_id}/costs")
async def add_cost_item(project_id: str, cost_data: CostItemCreate):
    try:
        cost_dict = cost_data.dict()
        cost_dict['total_cost'] = cost_dict['quantity'] * cost_dict['unit_cost']
        cost_item = CostItem(**cost_dict)
        
        result = await db.projects.update_one(
            {"id": project_id},
            {"$push": {"costs": cost_item.dict()}, "$set": {"updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return cost_item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding cost item: {e}")
        raise HTTPException(status_code=500, detail="Error adding cost item")

@api_router.delete("/projects/{project_id}/costs/{cost_id}")
async def delete_cost_item(project_id: str, cost_id: str):
    try:
        result = await db.projects.update_one(
            {"id": project_id},
            {"$pull": {"costs": {"id": cost_id}}, "$set": {"updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {"message": "Cost item deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting cost item: {e}")
        raise HTTPException(status_code=500, detail="Error deleting cost item")

# Payments
@api_router.post("/projects/{project_id}/payments")
async def add_payment(project_id: str, payment_data: PaymentCreate):
    try:
        payment = PaymentRecord(**payment_data.dict())
        
        result = await db.projects.update_one(
            {"id": project_id},
            {"$push": {"payments": payment.dict()}, "$set": {"updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return payment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding payment: {e}")
        raise HTTPException(status_code=500, detail="Error adding payment")

@api_router.delete("/projects/{project_id}/payments/{payment_id}")
async def delete_payment(project_id: str, payment_id: str):
    try:
        result = await db.projects.update_one(
            {"id": project_id},
            {"$pull": {"payments": {"id": payment_id}}, "$set": {"updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {"message": "Payment deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting payment: {e}")
        raise HTTPException(status_code=500, detail="Error deleting payment")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()