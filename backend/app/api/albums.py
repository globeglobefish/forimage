from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.user import User
from app.models.album import Album
from app.models.image import Image
from app.schemas.album import AlbumCreate, AlbumUpdate, AlbumResponse, AlbumListResponse
from app.api.deps import get_current_user
from app.services.storage import get_storage_backend

router = APIRouter(prefix="/albums", tags=["Albums"])


@router.get("", response_model=AlbumListResponse)
async def get_my_albums(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's albums."""
    result = await db.execute(
        select(Album)
        .where(Album.user_id == user.id)
        .options(selectinload(Album.images))
        .order_by(Album.created_at.desc())
    )
    albums = result.scalars().all()
    
    return AlbumListResponse(
        items=[AlbumResponse.model_validate(album) for album in albums],
        total=len(albums),
    )


@router.post("", response_model=AlbumResponse, status_code=status.HTTP_201_CREATED)
async def create_album(
    data: AlbumCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new album."""
    # Check if album name already exists for this user
    result = await db.execute(
        select(Album).where(Album.user_id == user.id, Album.name == data.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Album with this name already exists"
        )
    
    album = Album(
        name=data.name,
        description=data.description,
        is_public=data.is_public,
        user_id=user.id,
    )
    
    db.add(album)
    await db.commit()
    
    # Reload with images relationship for image_count property
    result = await db.execute(
        select(Album)
        .where(Album.id == album.id)
        .options(selectinload(Album.images))
    )
    album = result.scalar_one()
    
    return AlbumResponse.model_validate(album)


@router.get("/{album_id}", response_model=AlbumResponse)
async def get_album(
    album_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get album details."""
    result = await db.execute(
        select(Album)
        .where(Album.id == album_id, Album.user_id == user.id)
        .options(selectinload(Album.images))
    )
    album = result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found"
        )
    
    return AlbumResponse.model_validate(album)


@router.put("/{album_id}", response_model=AlbumResponse)
async def update_album(
    album_id: int,
    data: AlbumUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update album."""
    result = await db.execute(
        select(Album)
        .where(Album.id == album_id, Album.user_id == user.id)
        .options(selectinload(Album.images))
    )
    album = result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found"
        )
    
    # Check if new name conflicts with existing album
    if data.name and data.name != album.name:
        name_check = await db.execute(
            select(Album).where(
                Album.user_id == user.id, 
                Album.name == data.name,
                Album.id != album_id
            )
        )
        if name_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Album with this name already exists"
            )
        album.name = data.name
    
    if data.description is not None:
        album.description = data.description
    
    if data.is_public is not None:
        album.is_public = data.is_public
    
    await db.commit()
    
    # Reload with images relationship for image_count property
    result = await db.execute(
        select(Album)
        .where(Album.id == album_id)
        .options(selectinload(Album.images))
    )
    album = result.scalar_one()
    
    return AlbumResponse.model_validate(album)


@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_album(
    album_id: int,
    delete_images: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete album.
    If delete_images is True, also delete all images in the album.
    Otherwise, images are moved out of the album (album_id set to NULL).
    """
    result = await db.execute(
        select(Album)
        .where(Album.id == album_id, Album.user_id == user.id)
        .options(selectinload(Album.images))
    )
    album = result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found"
        )
    
    if delete_images:
        # Delete all images in the album - use file_path for date-based paths
        storage = get_storage_backend()
        for image in album.images:
            file_path = image.file_path if image.file_path else image.full_filename
            await storage.delete(file_path)
            await db.delete(image)
    else:
        # Move images out of album
        for image in album.images:
            image.album_id = None
    
    await db.delete(album)
    await db.commit()


@router.get("/{album_id}/images")
async def get_album_images(
    album_id: int,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get images in an album with sorting.
    """
    # Verify album ownership
    result = await db.execute(
        select(Album).where(Album.id == album_id, Album.user_id == user.id)
    )
    album = result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found"
        )
    
    # Build query
    query = select(Image).where(Image.album_id == album_id)
    
    # Apply sorting
    sort_column = Image.created_at
    if sort_by == "file_size":
        sort_column = Image.file_size
    
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    # Pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    images_result = await db.execute(query)
    images = images_result.scalars().all()
    
    from app.schemas.image import ImageResponse
    return {
        "items": [ImageResponse.model_validate(img) for img in images],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
