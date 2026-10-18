"""
Onboarding routes.
Exposes endpoints for personalized onboarding journeys, manager course approvals,
automatic learning assignments, introductions, and compliance documents.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status

from ..auth import CurrentUser, ManagerOrAbove
from ..dependencies import ApprovalRepoDep, UserRepoDep
from ..models import (
    ApprovalStatus,
    OnboardingFormStatus,
    OnboardingJourney,
    UserProfile,
    UserRole,
)
from ..schemas import (
    ApprovalOut,
    OnboardingApprovalRequest,
    OnboardingApprovalResolveRequest,
    OnboardingCourseItemOut,
    OnboardingFormRequirementOut,
    OnboardingFormSubmitRequest,
    OnboardingIntroductionOut,
    OnboardingJourneyOut,
    OnboardingScheduleIntroRequest,
)
from ..services.onboarding_service import get_onboarding_service

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


def _mask_sensitive_journey_data(journey: OnboardingJourney, viewer: UserProfile) -> dict[str, Any]:
    """Mask sensitive banking/identity form data if viewer is not the user, manager, or HR/admin."""
    data = journey.model_dump()
    is_owner = viewer.id == journey.user_id
    is_manager = viewer.id == journey.manager_id
    is_admin = viewer.role == UserRole.ADMIN

    can_view_sensitive = is_owner or is_manager or is_admin

    for form in data.get("forms", []):
        if form.get("is_sensitive") and not can_view_sensitive:
            sub = form.get("submitted_data", {})
            if "account_number" in sub:
                sub["account_number"] = "••••••••" + str(sub["account_number"])[-4:]
            if "routing_number" in sub:
                sub["routing_number"] = "•••••" + str(sub["routing_number"])[-4:]
            if "document_number" in sub:
                sub["document_number"] = "••••" + str(sub["document_number"])[-4:]

    # Critical contract guarantee: normalize onboarding_steps & onboardingSteps
    steps = data.get("onboarding_steps") or []
    if not isinstance(steps, list):
        steps = []
    data["onboarding_steps"] = steps
    data["onboardingSteps"] = steps

    return data


@router.get("/journey", response_model=OnboardingJourneyOut, summary="Get my personalized onboarding journey")
@router.get("/plan", response_model=OnboardingJourneyOut, summary="Alias for onboarding journey")
async def get_my_journey(current_user: CurrentUser) -> OnboardingJourneyOut:
    service = get_onboarding_service()
    journey = await service.get_or_create_journey(current_user)
    masked = _mask_sensitive_journey_data(journey, current_user)
    return OnboardingJourneyOut.model_validate(masked)


@router.post("/plan/generate", response_model=OnboardingJourneyOut, summary="Regenerate personalized onboarding plan")
async def regenerate_plan(current_user: CurrentUser) -> OnboardingJourneyOut:
    service = get_onboarding_service()
    journey = await service.get_or_create_journey(current_user, force_refresh=True)
    masked = _mask_sensitive_journey_data(journey, current_user)
    return OnboardingJourneyOut.model_validate(masked)


@router.get("/user/{user_id}", response_model=OnboardingJourneyOut, summary="Get associate's journey (manager or admin)")
async def get_user_journey(
    user_id: str,
    current_user: CurrentUser,
    user_repo: UserRepoDep,
) -> OnboardingJourneyOut:
    target_user = await user_repo.get(user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    is_owner = current_user.id == user_id
    is_manager = target_user.manager_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN

    if not (is_owner or is_manager or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to view this associate's onboarding journey.",
        )

    service = get_onboarding_service()
    journey = await service.get_or_create_journey(target_user)
    masked = _mask_sensitive_journey_data(journey, current_user)
    return OnboardingJourneyOut.model_validate(masked)


# ─── Phase 2: Course Approvals & Automatic Assignment ─────────────────────────

@router.post("/request-approval", summary="Request manager approval for recommended courses")
async def request_course_approval(
    body: OnboardingApprovalRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    if not body.course_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one course must be selected.")

    service = get_onboarding_service()
    try:
        approval, journey = await service.request_course_approval(
            user=current_user,
            course_ids=body.course_ids,
            justification=body.justification,
        )
        masked_journey = _mask_sensitive_journey_data(journey, current_user)
        return {
            "approval": ApprovalOut.model_validate(approval.model_dump()),
            "journey": masked_journey,
            "message": "Approval request submitted successfully to your manager.",
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/manager/requests", summary="List pending course approvals for manager's reports")
async def list_manager_requests(
    current_user: CurrentUser,
    approval_repo: ApprovalRepoDep,
) -> list[dict[str, Any]]:
    approvals, _ = await approval_repo.list(limit=100)
    # Filter to course approvals where current user is approver or user is admin
    result = []
    for a in approvals:
        if a.action_type == "course_assignment_approval":
            if a.approver_id == current_user.id or current_user.role == UserRole.ADMIN:
                item = a.model_dump()
                item["is_pending"] = a.status == ApprovalStatus.PENDING
                result.append(item)
    return result


@router.post("/approvals/{approval_id}/resolve", summary="Approve, reject, or modify course selection (manager only)")
async def resolve_approval(
    approval_id: str,
    body: OnboardingApprovalResolveRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    service = get_onboarding_service()
    try:
        updated_approval, journey = await service.resolve_course_approval(
            approval_id=approval_id,
            approver=current_user,
            status=body.status,
            decision_note=body.decision_note,
            approved_course_ids=body.approved_course_ids,
        )
        masked_journey = _mask_sensitive_journey_data(journey, current_user) if journey else None
        return {
            "approval": ApprovalOut.model_validate(updated_approval.model_dump()),
            "journey": masked_journey,
            "status": updated_approval.status.value,
            "message": f"Approval request resolved as {updated_approval.status.value}.",
        }
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


# ─── Phase 3: Introductions & Forms ───────────────────────────────────────────

@router.post("/schedule-intro", summary="Schedule an introduction meeting with colleague/manager")
async def schedule_intro(
    body: OnboardingScheduleIntroRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    service = get_onboarding_service()
    try:
        meeting, journey = await service.schedule_introduction(
            user=current_user,
            intro_id=body.intro_id,
            scheduled_at=body.scheduled_at,
            duration_minutes=body.duration_minutes,
            notes=body.notes,
        )
        masked_journey = _mask_sensitive_journey_data(journey, current_user)
        return {
            "meeting_id": meeting.id,
            "title": meeting.title,
            "scheduled_at": meeting.scheduled_at.isoformat(),
            "location": meeting.location,
            "journey": masked_journey,
            "message": "Introduction meeting scheduled successfully.",
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/forms", summary="List onboarding forms and document requirements")
async def list_forms(current_user: CurrentUser) -> list[dict[str, Any]]:
    service = get_onboarding_service()
    journey = await service.get_or_create_journey(current_user)
    masked = _mask_sensitive_journey_data(journey, current_user)
    return masked.get("forms", [])


@router.post("/forms/{form_id}/submit", summary="Submit a required onboarding document or compliance form")
async def submit_form(
    form_id: str,
    body: OnboardingFormSubmitRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    service = get_onboarding_service()
    try:
        journey = await service.submit_form(
            user=current_user,
            form_id=form_id,
            form_data=body.form_data,
            signature_confirmation=body.signature_confirmation,
        )
        masked = _mask_sensitive_journey_data(journey, current_user)
        return {
            "form_id": form_id,
            "status": "submitted",
            "journey": masked,
            "message": "Form submitted successfully for review.",
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
