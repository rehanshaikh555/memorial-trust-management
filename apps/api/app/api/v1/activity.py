from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import CurrentUser, get_db, require_permission
from app.core.permissions import Permission
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityPhotoCreate, ActivityPhotoResponse, ActivityReject, ActivityResponse, ActivityUpdate
from app.services import activity_service
from app.services.notification_service import create_many
from app.services.scope_service import has_school_access

router=APIRouter(prefix="/activities",tags=["Activities"])
DbSession=Annotated[Session,Depends(get_db)]

def get_activity(db:Session,activity_id:UUID)->Activity:
    obj=activity_service.get_by_id(db,activity_id)
    if obj is None:
        raise HTTPException(404,"Activity not found.")
    return obj

def check_access(db:Session,user:CurrentUser,obj:Activity)->None:
    if not has_school_access(db,user,obj.school_id):
        raise HTTPException(403,"You do not have access to this school.")

@router.post("",response_model=ActivityResponse,status_code=201,dependencies=[Depends(require_permission(Permission.ACTIVITY_CREATE.value))])
def create(data:ActivityCreate,db:DbSession,user:CurrentUser):
    if not has_school_access(db,user,data.school_id):
        raise HTTPException(403,"You do not have access to this school.")
    try:
        return activity_service.create(db,data,actor_user_id=user.id)
    except LookupError as e:
        raise HTTPException(404,str(e)) from e
    except ValueError as e:
        raise HTTPException(409,str(e)) from e

@router.get("",response_model=list[ActivityResponse],dependencies=[Depends(require_permission(Permission.ACTIVITY_READ.value))])
def listing(db:DbSession,user:CurrentUser,school_id:UUID|None=Query(None),academic_year_id:UUID|None=Query(None),activity_status:str|None=Query(None,alias="status")):
    return [x for x in activity_service.list_activities(db,school_id=school_id,academic_year_id=academic_year_id,status=activity_status) if has_school_access(db,user,x.school_id)]

@router.get("/{activity_id}",response_model=ActivityResponse,dependencies=[Depends(require_permission(Permission.ACTIVITY_READ.value))])
def get_one(activity_id:UUID,db:DbSession,user:CurrentUser):
    obj=get_activity(db,activity_id); check_access(db,user,obj); return obj

@router.patch("/{activity_id}",response_model=ActivityResponse,dependencies=[Depends(require_permission(Permission.ACTIVITY_UPDATE.value))])
def update(activity_id:UUID,data:ActivityUpdate,db:DbSession,user:CurrentUser):
    obj=get_activity(db,activity_id); check_access(db,user,obj)
    try:
        return activity_service.update(db,obj,data,actor_user_id=user.id)
    except ValueError as e:
        raise HTTPException(409,str(e)) from e

@router.post("/{activity_id}/submit",response_model=ActivityResponse,dependencies=[Depends(require_permission(Permission.ACTIVITY_SUBMIT.value))])
def submit(activity_id:UUID,db:DbSession,user:CurrentUser):
    obj=get_activity(db,activity_id); check_access(db,user,obj)
    try:
        obj=activity_service.submit(db,obj,actor_user_id=user.id,commit=False)
        create_many(db,recipient_user_ids=activity_service.get_review_recipients(db,obj),notification_type="ACTIVITY_SUBMITTED",title="Activity submitted for review",message=f"{obj.title} has been submitted for review.",related_entity_type="ACTIVITY",related_entity_id=obj.id)
        db.commit(); return obj
    except ValueError as e:
        db.rollback()
        raise HTTPException(409, str(e)) from e
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Activity workflow could not be completed.",
        ) from e

@router.post("/{activity_id}/approve",response_model=ActivityResponse,dependencies=[Depends(require_permission(Permission.ACTIVITY_APPROVE.value))])
def approve(activity_id:UUID,db:DbSession,user:CurrentUser):
    obj=get_activity(db,activity_id); check_access(db,user,obj)
    try:
        obj=activity_service.approve(db,obj,actor_user_id=user.id,commit=False)
        create_many(db,recipient_user_ids=[obj.created_by],notification_type="ACTIVITY_APPROVED",title="Activity approved",message=f"{obj.title} has been approved.",related_entity_type="ACTIVITY",related_entity_id=obj.id)
        db.commit(); return obj
    except ValueError as e:
        db.rollback()
        raise HTTPException(409, str(e)) from e
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Activity workflow could not be completed.",
        ) from e

@router.post("/{activity_id}/reject",response_model=ActivityResponse,dependencies=[Depends(require_permission(Permission.ACTIVITY_APPROVE.value))])
def reject(activity_id:UUID,data:ActivityReject,db:DbSession,user:CurrentUser):
    obj=get_activity(db,activity_id); check_access(db,user,obj)
    try:
        obj=activity_service.reject(db,obj,actor_user_id=user.id,reason=data.reason,commit=False)
        create_many(db,recipient_user_ids=[obj.created_by],notification_type="ACTIVITY_REJECTED",title="Activity rejected",message=f"{obj.title} was rejected: {data.reason}",related_entity_type="ACTIVITY",related_entity_id=obj.id,priority="HIGH")
        db.commit(); return obj
    except ValueError as e:
        db.rollback()
        raise HTTPException(409, str(e)) from e
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Activity workflow could not be completed.",
        ) from e

@router.post("/{activity_id}/publish",response_model=ActivityResponse,dependencies=[Depends(require_permission(Permission.ACTIVITY_PUBLISH.value))])
def publish(activity_id:UUID,db:DbSession,user:CurrentUser):
    obj=get_activity(db,activity_id); check_access(db,user,obj)
    try:
        obj=activity_service.publish(db,obj,actor_user_id=user.id,commit=False)
        create_many(db,recipient_user_ids=[obj.created_by],notification_type="ACTIVITY_PUBLISHED",title="Activity published",message=f"{obj.title} has been published.",related_entity_type="ACTIVITY",related_entity_id=obj.id)
        db.commit(); return obj
    except ValueError as e:
        db.rollback()
        raise HTTPException(409, str(e)) from e
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Activity workflow could not be completed.",
        ) from e

@router.post("/{activity_id}/photos",response_model=ActivityPhotoResponse,status_code=201,dependencies=[Depends(require_permission(Permission.ACTIVITY_UPDATE.value))])
def add_photo(activity_id:UUID,data:ActivityPhotoCreate,db:DbSession,user:CurrentUser):
    obj=get_activity(db,activity_id); check_access(db,user,obj)
    try:
        return activity_service.add_photo(db,obj,actor_user_id=user.id,file_name=data.file_name,storage_path=data.storage_path,mime_type=data.mime_type,file_size=data.file_size,caption=data.caption,display_order=data.display_order)
    except ValueError as e:
        raise HTTPException(409,str(e)) from e

@router.get("/{activity_id}/photos",response_model=list[ActivityPhotoResponse],dependencies=[Depends(require_permission(Permission.ACTIVITY_READ.value))])
def photos(activity_id:UUID,db:DbSession,user:CurrentUser):
    obj=get_activity(db,activity_id); check_access(db,user,obj); return activity_service.list_photos(db,activity_id)

@router.delete("/{activity_id}/photos/{photo_id}",status_code=204,dependencies=[Depends(require_permission(Permission.ACTIVITY_UPDATE.value))])
def delete_photo(activity_id:UUID,photo_id:UUID,db:DbSession,user:CurrentUser):
    obj=get_activity(db,activity_id); check_access(db,user,obj)
    photo=activity_service.get_photo(db,photo_id)
    if photo is None: raise HTTPException(404,"Activity photo not found.")
    try:
        activity_service.delete_photo(db,obj,photo,actor_user_id=user.id)
    except LookupError as e:
        raise HTTPException(404,str(e)) from e
    except ValueError as e:
        raise HTTPException(409,str(e)) from e
