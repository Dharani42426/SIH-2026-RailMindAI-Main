from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import exc
from typing import List
import uuid

from models import get_db
from models.user import User
from models.corridor import RailwaySection
from models.maintenance_task import MaintenanceTask
from models.maintenance_request import MaintenanceRequest
from schemas import (
    MaintenanceRequestCreate,
    MaintenanceRequestUpdate,
    MaintenanceRequestResponse,
    MaintenanceRequestReview,
    RequestStatus,
    TaskStatus,
    SourceSystem,
    Severity
)
from routes.auth import get_current_user
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user_dep(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    return get_current_user(credentials.credentials, db)

router = APIRouter(prefix="/requests", tags=["Maintenance Requests"])


@router.post("/", response_model=MaintenanceRequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(
    request_in: MaintenanceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """
    Submit a new maintenance request (Departmental users).
    """
    if not current_user.can_submit_tasks:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to submit maintenance requests."
        )

    # Verify section exists
    section = db.query(RailwaySection).filter(RailwaySection.id == request_in.section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found."
        )
    
    # KM range validation
    if request_in.km_from < section.km_start or request_in.km_to > section.km_end or request_in.km_from >= request_in.km_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid KM range for the specified section."
        )
    
    if request_in.estimated_hours <= 0:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estimated hours must be strictly positive."
        )

    # Generate request code
    import random
    dept_prefix = request_in.department.value
    random_id = str(uuid.uuid4()).split('-')[0][:4].upper()
    req_code = f"REQ-{dept_prefix}-2026-{random_id}"

    db_req = MaintenanceRequest(
        request_code=req_code,
        requester_id=current_user.id,
        department=request_in.department,
        section_id=request_in.section_id,
        work_type=request_in.work_type,
        description=request_in.description,
        justification=request_in.justification,
        km_from=request_in.km_from,
        km_to=request_in.km_to,
        estimated_hours=request_in.estimated_hours,
        block_type_required=request_in.block_type_required,
        preferred_date=request_in.preferred_date,
        status=RequestStatus.SUBMITTED.value  # Created as SUBMITTED directly for this workflow
    )
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return db_req


@router.get("/", response_model=List[MaintenanceRequestResponse])
def get_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """
    Get maintenance requests.
    CONTROLLER/ADMIN sees all requests.
    Departments see only their own department's requests.
    """
    query = db.query(MaintenanceRequest)
    if not current_user.can_approve_plans:
        # Not a controller/admin, restrict by department
        query = query.filter(MaintenanceRequest.department == current_user.department)
        
    return query.order_by(MaintenanceRequest.created_at.desc()).all()


@router.get("/{request_id}", response_model=MaintenanceRequestResponse)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """
    Get a specific request by ID.
    Enforces department-level scoping for non-controllers.
    """
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found."
        )
    
    if not current_user.can_approve_plans and req.department != current_user.department:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this department's requests."
        )
        
    return req


@router.patch("/{request_id}", response_model=MaintenanceRequestResponse)
def update_request(
    request_id: int,
    update_in: MaintenanceRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """
    Update a request. Only allowed if status is DRAFT or SUBMITTED.
    """
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
        
    if not current_user.can_approve_plans and req.department != current_user.department:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
        
    if req.status not in [RequestStatus.DRAFT.value, RequestStatus.SUBMITTED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request is locked and cannot be edited."
        )

    update_data = update_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(req, field, value)
        
    db.commit()
    db.refresh(req)
    return req


@router.post("/{request_id}/review", response_model=MaintenanceRequestResponse)
def review_request(
    request_id: int,
    review_in: MaintenanceRequestReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """
    Controller only: Accept or reject a maintenance request.
    If ACCEPT, automatically spawns a MaintenanceTask for the AI optimizer.
    """
    if not current_user.can_approve_plans:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only controllers or admins can review maintenance requests."
        )
        
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
        
    if req.status not in [RequestStatus.SUBMITTED.value, RequestStatus.UNDER_REVIEW.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request is currently {req.status}, which is not a reviewable state."
        )
        
    if review_in.action.upper() == "REJECT":
        if not review_in.rejection_reason or not review_in.rejection_reason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A rejection reason must be provided when rejecting a request."
            )
        req.status = RequestStatus.REJECTED.value
        req.rejection_reason = review_in.rejection_reason
        db.commit()
        db.refresh(req)
        return req
        
    elif review_in.action.upper() == "ACCEPT":
        # Transactional acceptance and task generation
        try:
            # 1. Create the new MaintenanceTask mapped from the request
            # Assume request originates from RailMind (not TMS/SMMS) directly or map to appropriate source
            task_code = f"RM-{req.request_code}"
            
            new_task = MaintenanceTask(
                task_code=task_code,
                source_system=SourceSystem.TMS.value, # Defaulting for now
                department=req.department,
                section_id=req.section_id,
                km_from=req.km_from,
                km_to=req.km_to,
                task_type=req.work_type,
                severity=Severity.HIGH.value, # Default or could be requested
                detected_date=req.created_at.date(),
                due_date=req.preferred_date,
                estimated_hours=req.estimated_hours,
                block_type_required=req.block_type_required,
                status=TaskStatus.PENDING.value
            )
            db.add(new_task)
            db.flush() # Flush to get the ID without committing
            
            # 2. Link back to request and mark accepted
            req.maintenance_task_id = new_task.id
            req.status = RequestStatus.ACCEPTED.value
            
            # Commit both together safely
            db.commit()
            db.refresh(req)
            return req
            
        except exc.IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error during task creation."
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate MaintenanceTask. Transaction aborted."
            )
            
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Use ACCEPT or REJECT."
        )
