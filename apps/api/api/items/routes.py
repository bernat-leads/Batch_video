"""Item routes — example CRUD endpoints for the template."""

import uuid

from fastapi import APIRouter, Depends, HTTPException

from api.deps.auth import AuthenticatedUserDep, get_user
from api.items.crud import ItemCrudDep
from api.items.schemas import ItemCreate, ItemResponse, ItemUpdate

router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(get_user)],
)


@router.get("/", response_model=list[ItemResponse])
async def list_items(
    crud: ItemCrudDep,
    current_user: AuthenticatedUserDep,
    skip: int = 0,
    limit: int = 100,
) -> list[ItemResponse]:
    items = await crud.get_by_user_id(current_user.id, skip=skip, limit=limit)
    return [ItemResponse.model_validate(item) for item in items]


@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(
    body: ItemCreate,
    crud: ItemCrudDep,
    current_user: AuthenticatedUserDep,
) -> ItemResponse:
    from api.items.models.item import Item as ItemModel

    item = ItemModel(
        user_id=current_user.id,
        title=body.title,
        content=body.content,
    )
    from api.deps.db import save

    await save(crud.db_session, item)
    return ItemResponse.model_validate(item)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: uuid.UUID,
    crud: ItemCrudDep,
    current_user: AuthenticatedUserDep,
) -> ItemResponse:
    item = await crud.get(item_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemResponse.model_validate(item)


@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: uuid.UUID,
    body: ItemUpdate,
    crud: ItemCrudDep,
    current_user: AuthenticatedUserDep,
) -> ItemResponse:
    item = await crud.get(item_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found")
    updated = await crud.update(item_id, body)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemResponse.model_validate(updated)


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: uuid.UUID,
    crud: ItemCrudDep,
    current_user: AuthenticatedUserDep,
) -> None:
    item = await crud.get(item_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found")
    await crud.delete(item_id)
