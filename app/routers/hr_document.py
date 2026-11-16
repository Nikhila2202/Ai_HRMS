
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_permission
from database import get_db

from app.models.model import (
    HRDocumentType,
    HRDocumentRequest,
    HRDocumentRequestHistory,
    User
)

from app.auth.dependencies import get_current_user
from app.schemas.hr_document import (
    HRDocumentRequestUpdate,
    HRDocumentRequestUpdate,
    HRDocumentTypeResponse,
    HRDocumentRequestCreate,
    HRDocumentRequestResponse
)


router = APIRouter(
    tags=["HR Document Management"]
)


# 1. GET ALL ACTIVE DOCUMENT TYPES

@router.get(
    "/documents/types",
    response_model=list[HRDocumentTypeResponse]
)
def get_document_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    document_types = db.query(HRDocumentType).filter(
        HRDocumentType.is_active.is_(True)
    ).order_by(
        HRDocumentType.document_type_name.asc()
    ).all()

    return document_types


# 2. POST CREATE DOCUMENT REQUEST

@router.post(
    "/document-requests",
    response_model=HRDocumentRequestResponse,
    status_code=status.HTTP_201_CREATED
)
def create_document_request(
    request_data: HRDocumentRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Check employee account

    if not current_user.employee_id:
        raise HTTPException(
            status_code=403,
            detail="User is not linked to an employee"
        )

    # Check document type exists and is active

    document_type = db.query(HRDocumentType).filter(
        HRDocumentType.document_type_code
        == request_data.document_type,
        HRDocumentType.is_active.is_(True)
    ).first()

    if not document_type:
        raise HTTPException(
            status_code=404,
            detail="Active document type not found"
        )

    try:

        # Create document request

        new_request = HRDocumentRequest(
            employee_id=current_user.employee_id,
            document_type=document_type.document_type_code,
            purpose=request_data.purpose,
            status="pending"
        )

        db.add(new_request)
        db.flush()

        # Create request history

        history = HRDocumentRequestHistory(
            document_request_id=new_request.document_request_id,
            previous_status=None,
            new_status="pending",
            action_by_user_id=current_user.user_id,
            comments="Document request submitted"
        )

        db.add(history)

        db.commit()
        db.refresh(new_request)

        return new_request

    except Exception:
        db.rollback()
        raise


# 3. GET LOGGED-IN EMPLOYEE DOCUMENT REQUESTS

@router.get(
    "/documents/me",
    response_model=list[HRDocumentRequestResponse]
)
def get_my_document_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if not current_user.employee_id:
        raise HTTPException(
            status_code=403,
            detail="User is not linked to an employee"
        )

    requests = db.query(HRDocumentRequest).filter(
        HRDocumentRequest.employee_id
        == current_user.employee_id
    ).order_by(
        HRDocumentRequest.requested_at.desc()
    ).all()

    return requests


# 4. GET DOCUMENT REQUEST BY ID

@router.get(
    "/documents/{request_id}",
    response_model=HRDocumentRequestResponse
)
def get_document_request_by_id(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if not current_user.employee_id:
        raise HTTPException(
            status_code=403,
            detail="User is not linked to an employee"
        )

    document_request = db.query(HRDocumentRequest).filter(
        HRDocumentRequest.document_request_id == request_id,
        HRDocumentRequest.employee_id == current_user.employee_id
    ).first()

    if not document_request:
        raise HTTPException(
            status_code=404,
            detail="Document request not found"
        )

    return document_request

    HRDocumentRequestResponse,
    HRDocumentRequestUpdate


from app.auth.dependencies import get_current_user




@router.patch(
    "/document-requests/{request_id}",
    response_model=HRDocumentRequestResponse,
    status_code=status.HTTP_200_OK
)
def update_document_request(
    request_id: int,
    request_data: HRDocumentRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:
        # 1. Check whether document request exists

        document_request = db.query(HRDocumentRequest).filter(
            HRDocumentRequest.document_request_id == request_id
        ).first()

        if not document_request:
            raise HTTPException(
                status_code=404,
                detail="Document request not found"
            )

        # 2. Get previous status

        previous_status = document_request.status

        # 3. Get submitted fields

        update_data = request_data.model_dump(exclude_unset=True)

        current_user: User = Depends(
    require_permission("document_request.update")
)

        # 4. Validate status

        allowed_statuses = ["pending", "approved", "rejected"]

        if "status" in update_data:
            new_status = update_data["status"]

            if new_status not in allowed_statuses:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid document request status"
                )

            if previous_status in ["approved", "rejected"]:
                raise HTTPException(
                    status_code=400,
                    detail="This document request has already been processed"
                )

        # 5. Update document request fields

        for field, value in update_data.items():
            setattr(document_request, field, value)

        # 6. If status changed, update processing details
        new_status = document_request.status

        if new_status != previous_status:

            document_request.processed_by_employee_id = (
                current_user.employee_id
            )

            document_request.processed_at = datetime.now(timezone.utc)

            # 7. Insert history record

            history = HRDocumentRequestHistory(
                document_request_id=document_request.document_request_id,
                previous_status=previous_status,
                new_status=new_status,
                action_by_user_id=current_user.user_id,
                comments=f"Document request status changed from {previous_status} to {new_status}"
            )

            db.add(history)

        # 8. Commit changes

        db.commit()
        db.refresh(document_request)

        return document_request

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise
