"""
Category Router - Manage categories and their mappings
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, attributes
from typing import List, Optional

from app.database import get_db
from app.models.category import Category
from app.models.data_row import DataRow
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse
)
from app.services.category_matcher import CategoryMatcher
from app.utils import get_logger
from app.utils.pagination import paginate_query
from app.config import settings

router = APIRouter()
logger = get_logger("app.routers.categories")


@router.get("", response_model=List[CategoryResponse])
def get_categories(
    limit: int = Query(settings.DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Get all categories
    
    Returns:
        List of all categories with their mapping rules
    """
    query = db.query(Category).order_by(Category.name)
    items, total, eff_limit, eff_offset, pages = paginate_query(query, limit, offset)
    return items


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """
    Get a specific category by ID
    
    Args:
        category_id: Category ID
        
    Returns:
        Category details
        
    Raises:
        404: Category not found
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    return category


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(category_data: CategoryCreate, db: Session = Depends(get_db)):
    """
    Create a new category
    
    Args:
        category_data: Category creation data
        
    Returns:
        Created category
        
    Raises:
        400: Category name already exists
    """
    # Check if category name already exists
    existing = db.query(Category).filter(Category.name == category_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category_data.name}' already exists"
        )
    
    # Convert mappings to dict
    mappings_dict = category_data.mappings.model_dump()
    
    # Create new category
    new_category = Category(
        name=category_data.name,
        color=category_data.color,
        icon=category_data.icon,
        mappings=mappings_dict
    )
    
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return new_category


@router.delete("/{category_id}/pattern/{pattern}")
def remove_pattern_from_category(
    category_id: int,
    pattern: str,
    db: Session = Depends(get_db)
):
    """
    Remove a specific pattern from a category
    
    Args:
        category_id: Category ID
        pattern: Pattern to remove
        
    Returns:
        Updated category
        
    Raises:
        404: Category not found
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    mappings = category.mappings or {}
    patterns = mappings.get('patterns', [])
    
    # Remove pattern (case-insensitive)
    pattern_lower = pattern.lower()
    new_patterns = [p for p in patterns if p.lower() != pattern_lower]
    
    # Update category
    category.mappings = {'patterns': new_patterns}
    attributes.flag_modified(category, 'mappings')

    db.commit()
    db.refresh(category)

    # Clear matcher cache
    matcher = CategoryMatcher(db)
    matcher.clear_cache()

    logger.info("Removed pattern for category", extra={"category_id": category_id, "pattern": pattern})

    return category


@router.get("/check-pattern-conflict/{pattern}")
def check_pattern_conflict(
    pattern: str,
    current_category_id: Optional[int] = Query(None, description="Current category ID to exclude from check"),
    db: Session = Depends(get_db)
):
    """
    Check if a pattern already exists in another category
    
    Args:
        pattern: Pattern to check
        current_category_id: Current category ID (to exclude from search)
        
    Returns:
        Conflict information if pattern exists in another category
        
    Example Response:
        {
            "conflict": true,
            "category_id": 2,
            "category_name": "Lebensmittel",
            "category_color": "#10b981",
            "category_icon": "🛒"
        }
    """
    pattern_lower = pattern.lower().strip()
    
    # Find all categories
    categories = db.query(Category).all()
    
    for cat in categories:
        # Skip current category
        if current_category_id and cat.id == current_category_id:
            continue
        
        mappings = cat.mappings or {}
        patterns = mappings.get('patterns', [])
        
        # Check if pattern exists (case-insensitive)
        if any(p.lower() == pattern_lower for p in patterns):
            return {
                "conflict": True,
                "category_id": cat.id,
                "category_name": cat.name,
                "category_color": cat.color,
                "category_icon": cat.icon
            }
    
    return {"conflict": False}


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing category
    
    Args:
        category_id: Category ID
        category_data: Updated category data
        
    Returns:
        Updated category
        
    Raises:
        404: Category not found
        400: Category name already exists
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    # Check name uniqueness if name is being updated
    update_data = category_data.model_dump(exclude_unset=True)
    
    # Debug logging
    logger.debug("Update Category %s - update_data keys=%s", category_id, list(update_data.keys()))
    
    if 'name' in update_data and update_data['name'] != category.name:
        existing = db.query(Category).filter(
            Category.name == update_data['name']
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with name '{update_data['name']}' already exists"
            )
    
    # Validate and clean mappings if provided
    if 'mappings' in update_data and update_data['mappings'] is not None:
        patterns = update_data['mappings'].get('patterns', [])
        
        # Remove empty patterns and strip whitespace
        cleaned_patterns = [p.strip() for p in patterns if p and p.strip()]
        
        # Remove duplicates (case-insensitive)
        seen = set()
        unique_patterns = []
        for pattern in cleaned_patterns:
            pattern_lower = pattern.lower()
            if pattern_lower not in seen:
                seen.add(pattern_lower)
                unique_patterns.append(pattern)
        
        # Validate pattern length
        if any(len(p) > 100 for p in unique_patterns):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pattern length must not exceed 100 characters"
            )
        
        update_data['mappings'] = {'patterns': unique_patterns}
        logger.debug("Cleaned patterns for category_id=%s count=%d", category_id, len(unique_patterns))
    
    # Update fields
    for field, value in update_data.items():
        if field == 'mappings' and value is not None:
            # Set the value
            setattr(category, field, value)
            # CRITICAL FIX: Mark JSON field as modified so SQLAlchemy tracks the change
            attributes.flag_modified(category, field)
        else:
            setattr(category, field, value)
    
    db.commit()
    db.refresh(category)

    # Clear CategoryMatcher cache after category update
    matcher = CategoryMatcher(db)
    matcher.clear_cache()

    logger.info("Category updated", extra={"category_id": category_id})
    logger.debug("New mappings in DB", extra={"category_id": category_id, "mappings": category.mappings})

    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """
    Delete a category
    
    Args:
        category_id: Category ID
        
    Raises:
        404: Category not found
        
    Note:
        Transactions associated with this category will have their
        category_id set to NULL (due to SET NULL foreign key constraint)
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    db.delete(category)
    db.commit()
    
    return None


@router.post("/recategorize", status_code=status.HTTP_200_OK)
def recategorize_transactions(
    account_id: Optional[int] = Query(None, description="Account ID to recategorize (None for all accounts)"),
    db: Session = Depends(get_db)
):
    """
    Recategorize all transactions based on current category mapping rules
    
    This endpoint re-applies category matching to all existing transactions.
    Use this after updating category patterns to ensure all transactions
    are correctly categorized.
    
    Args:
        account_id: Optional account ID to filter transactions (None = all accounts)
        
    Returns:
        Statistics about the recategorization process
        
    Example Response:
        {
            "total_transactions": 1250,
            "categorized": 982,
            "uncategorized": 268,
            "updated_count": 145,
            "category_distribution": {
                "Lebensmittel": 350,
                "Transport": 120,
                "Gesundheit": 45
            }
        }
    """
    # Build query
    query = db.query(DataRow)
    if account_id:
        query = query.filter(DataRow.account_id == account_id)
    
    total_transactions = db.query(DataRow).filter(DataRow.account_id == account_id) if account_id else db.query(DataRow)
    total_count = total_transactions.count()

    if total_count == 0:
        return {
            "total_transactions": 0,
            "categorized": 0,
            "uncategorized": 0,
            "updated_count": 0,
            "category_distribution": {}
        }

    # Initialize matcher
    matcher = CategoryMatcher(db)
    matcher.clear_cache()  # Ensure fresh category data

    # Statistics accumulators
    updated_count = 0
    # Prefetch category id -> name map to avoid N+1 queries
    category_map = {c.id: c.name for c in db.query(Category).all()}

    # Process transactions in chunks to avoid loading all into memory
    batch_size = 1000
    offset = 0
    from sqlalchemy import func
    while True:
        batch_query = query.order_by(DataRow.id).offset(offset).limit(batch_size)
        transactions = batch_query.all()
        if not transactions:
            break

        # Build list of transaction payloads for bulk matching
        tx_payloads = []
        tx_ids = []
        old_category_map = {}
        for tx in transactions:
            tx_ids.append(tx.id)
            old_category_map[tx.id] = tx.category_id
            tx_payloads.append({
                'recipient': tx.recipient,
                'purpose': tx.purpose,
            })

        # Bulk match using precompiled patterns
        new_categories = matcher.match_bulk(tx_payloads)

        # Map of target_category -> list of transaction ids to update
        updates_by_category: dict = {}
        uncategorized_ids = []

        for tx_id, new_cat in zip(tx_ids, new_categories):
            old_cat = old_category_map.get(tx_id)
            if new_cat != old_cat:
                # Schedule update
                if new_cat is None:
                    uncategorized_ids.append(tx_id)
                else:
                    updates_by_category.setdefault(new_cat, []).append(tx_id)

        # Apply updates in batches for performance
        def _chunks(lst, n=500):
            for i in range(0, len(lst), n):
                yield lst[i:i+n]

        # Update categorized -> category_id
        for category_id, ids in updates_by_category.items():
            for chunk in _chunks(ids, 500):
                db.query(DataRow).filter(DataRow.id.in_(chunk)).update({DataRow.category_id: category_id}, synchronize_session=False)
                updated_count += len(chunk)

        # Update uncategorized (set category_id = None)
        for chunk in _chunks(uncategorized_ids, 500):
            db.query(DataRow).filter(DataRow.id.in_(chunk)).update({DataRow.category_id: None}, synchronize_session=False)
            updated_count += len(chunk)

        # Commit batched updates for this chunk
        db.commit()

        offset += batch_size

    # Compute final statistics from database counts to be accurate
    categorized_count = db.query(func.count(DataRow.id)).filter(DataRow.account_id == account_id, DataRow.category_id.isnot(None)).scalar() if account_id else db.query(func.count(DataRow.id)).filter(DataRow.category_id.isnot(None)).scalar()
    categorized_count = categorized_count or 0
    uncategorized_count = total_count - categorized_count

    # Rebuild category_distribution by querying counts grouped by category_id
    distribution = {}
    rows = db.query(DataRow.category_id, func.count(DataRow.id)).filter(DataRow.category_id.isnot(None))
    if account_id:
        rows = rows.filter(DataRow.account_id == account_id)
    rows = rows.group_by(DataRow.category_id).all()
    for cat_id, cnt in rows:
        name = category_map.get(cat_id)
        if name:
            distribution[name] = cnt
    category_distribution = distribution
    
    logger.info(
        "Recategorized transactions",
        extra={
            "total": len(transactions),
            "updated": updated_count,
            "categorized": categorized_count,
            "uncategorized": uncategorized_count,
        },
    )
    
    return {
        "total_transactions": total_transactions,
        "categorized": categorized_count,
        "uncategorized": uncategorized_count,
        "updated_count": updated_count,
        "category_distribution": category_distribution
    }
