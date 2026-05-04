from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.models.profile import Profile
from app.schemas.profiles import ProfileCreateRequest, ProfileResponse, ProfileUpdateRequest


router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("", response_model=list[ProfileResponse])
async def list_profiles(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(Profile).order_by(Profile.created_at.desc()))
    return [ProfileResponse.model_validate(item, from_attributes=True) for item in result.scalars().all()]


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(payload: ProfileCreateRequest, session: AsyncSession = Depends(get_db_session)):
    profile = Profile(**payload.model_dump())
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return ProfileResponse.model_validate(profile, from_attributes=True)


@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(profile_id: UUID, payload: ProfileUpdateRequest, session: AsyncSession = Depends(get_db_session)):
    profile = await session.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="profile not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    await session.commit()
    await session.refresh(profile)
    return ProfileResponse.model_validate(profile, from_attributes=True)
