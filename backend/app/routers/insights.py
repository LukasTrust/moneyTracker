"""
Insights Router - API endpoints for spending insights
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.schemas.insight import (
    InsightResponse,
    InsightListResponse,
    InsightDismiss,
    InsightGenerationRequest,
    InsightGenerationResponse,
    InsightStatistics,
    InsightGenerationLogResponse
)
from app.models.insight import Insight, InsightGenerationLog
from app.services.insights_generator import InsightsGenerator


router = APIRouter()


@router.get("/displayable", response_model=List[InsightResponse])
def get_displayable_insights(
    account_id: Optional[int] = Query(None, description="Filter by account ID (NULL for global insights)"),
    max_count: int = Query(1, ge=1, le=5, description="Maximum number of insights to return"),
    db: Session = Depends(get_db)
):
    """
    Get insights ready to be displayed (respecting cooldown periods)
    
    This endpoint returns insights that:
    - Are not dismissed
    - Have passed their cooldown period (or never shown)
    - Are not expired
    - Are sorted by priority
    
    Use this for popup/notification systems where you want to show 1-2 insights at a time.
    
    Args:
        account_id: Filter by account (None = all accounts + global insights)
        max_count: Maximum number of insights (default: 1)
        
    Returns:
        List of displayable insights
    """
    generator = InsightsGenerator(db)
    insights = generator.get_displayable_insights(
        account_id=account_id,
        max_count=max_count
    )
    
    return insights


@router.post("/mark-shown/{insight_id}")
def mark_insight_shown(
    insight_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark an insight as shown (updates last_shown_at and show_count)
    
    Call this endpoint when an insight is displayed to the user.
    This starts the cooldown timer for that insight.
    
    Args:
        insight_id: ID of insight that was shown
        
    Returns:
        Success message
    """
    generator = InsightsGenerator(db)
    success = generator.mark_insight_shown(insight_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Insight nicht gefunden")
    
    return {
        "success": True,
        "message": f"Insight #{insight_id} als angezeigt markiert"
    }


@router.get("/", response_model=InsightListResponse)
def get_insights(
    account_id: Optional[int] = Query(None, description="Filter by account ID (NULL for global insights)"),
    include_dismissed: bool = Query(False, description="Include dismissed insights"),
    insight_type: Optional[str] = Query(None, description="Filter by insight type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of insights"),
    db: Session = Depends(get_db)
):
    """
    Get insights for display
    
    Returns active (non-dismissed) insights by default, ordered by priority and creation date.
    
    Args:
        account_id: Filter by account (None = all accounts + global insights)
        include_dismissed: Include dismissed insights
        insight_type: Filter by type (mom_increase, yoy_decrease, etc.)
        severity: Filter by severity (info, success, warning, alert)
        limit: Maximum number of insights to return
        
    Returns:
        List of insights with metadata
    """
    query = db.query(Insight)
    
    # Filter by account
    if account_id is not None:
        # Get insights for specific account + global insights (account_id = NULL)
        query = query.filter(or_(Insight.account_id == account_id, Insight.account_id.is_(None)))
    
    # Filter by dismissed status
    if not include_dismissed:
        query = query.filter(Insight.is_dismissed == False)
    
    # Filter by type
    if insight_type:
        query = query.filter(Insight.insight_type == insight_type)
    
    # Filter by severity
    if severity:
        query = query.filter(Insight.severity == severity)
    
    # Filter out expired insights
    query = query.filter(
        or_(
            Insight.valid_until.is_(None),
            Insight.valid_until >= datetime.now()
        )
    )
    
    # Order by priority (desc) and creation date (desc)
    query = query.order_by(Insight.priority.desc(), Insight.created_at.desc())
    
    # Get total count before limit
    total = query.count()
    
    # Apply limit
    insights = query.limit(limit).all()
    
    # Count active vs dismissed
    active_count = db.query(Insight).filter(Insight.is_dismissed == False).count()
    dismissed_count = db.query(Insight).filter(Insight.is_dismissed == True).count()
    
    return InsightListResponse(
        insights=insights,
        total=total,
        active_count=active_count,
        dismissed_count=dismissed_count
    )


@router.post("/generate", response_model=InsightGenerationResponse)
def generate_insights(
    request: InsightGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate new insights
    
    Analyzes transaction data and generates personalized spending insights.
    Automatically cleans up old insights before generating new ones.
    
    Args:
        request: Generation request with account_id and optional generation_types
        
    Returns:
        Generation result with count of insights generated
    """
    generator = InsightsGenerator(db)
    
    # Clean up old/expired insights first
    removed_count = generator.cleanup_old_insights(
        account_id=request.account_id,
        days_old=30
    )
    
    # Check if recently generated (unless force_regenerate is True)
    if not request.force_regenerate:
        recent_log = db.query(InsightGenerationLog).filter(
            and_(
                InsightGenerationLog.account_id == request.account_id,
                InsightGenerationLog.generated_at >= datetime.now().replace(hour=0, minute=0, second=0)
            )
        ).first()
        
        if recent_log:
            # Already generated today - return existing insights
            existing_count = db.query(Insight).filter(
                and_(
                    Insight.account_id == request.account_id,
                    Insight.is_dismissed == False
                )
            ).count()
            
            return InsightGenerationResponse(
                success=True,
                insights_generated=0,
                insights_removed=0,
                generation_type='cached',
                message=f"Insights wurden heute bereits generiert. {existing_count} aktive Insights vorhanden."
            )
    
    # Generate insights (use dict-based generator with small per-process cache)
    generation_types = request.generation_types
    if generation_types and 'full_analysis' in generation_types:
        generation_types = None  # Generate all types

    new_insights_dicts = generator.generate_all_insights_dict(
        account_id=request.account_id,
        generation_types=generation_types,
        force_regenerate=request.force_regenerate
    )

    # Convert dicts into ORM Insight objects and persist
    for ins in new_insights_dicts:
        valid_until = None
        if ins.get('valid_until'):
            try:
                valid_until = datetime.fromisoformat(ins.get('valid_until'))
            except Exception:
                valid_until = None

        orm_insight = Insight(
            account_id=ins.get('account_id'),
            insight_type=ins.get('insight_type'),
            severity=ins.get('severity') or 'info',
            title=ins.get('title') or '',
            description=ins.get('description') or '',
            insight_data=ins.get('insight_data'),
            priority=ins.get('priority') or 5,
            cooldown_hours=ins.get('cooldown_hours') or 24,
            valid_until=valid_until
        )

        db.add(orm_insight)
    
    # Log generation
    log_entry = InsightGenerationLog(
        account_id=request.account_id,
        generation_type=','.join(generation_types) if generation_types else 'full_analysis',
        insights_generated=len(new_insights),
        generation_params={
            'force_regenerate': request.force_regenerate,
            'generation_types': generation_types
        }
    )
    db.add(log_entry)
    
    db.commit()
    
    return InsightGenerationResponse(
        success=True,
        insights_generated=len(new_insights),
        insights_removed=removed_count,
        generation_type=','.join(generation_types) if generation_types else 'full_analysis',
        message=f"Erfolgreich {len(new_insights)} Insights generiert. {removed_count} alte Insights entfernt."
    )


@router.post("/dismiss/{insight_id}")
def dismiss_insight(
    insight_id: int,
    db: Session = Depends(get_db)
):
    """
    Dismiss an insight
    
    Marks an insight as dismissed (hidden from view).
    User can still see dismissed insights by enabling include_dismissed filter.
    
    Args:
        insight_id: ID of insight to dismiss
        
    Returns:
        Success message
    """
    insight = db.query(Insight).filter(Insight.id == insight_id).first()
    
    if not insight:
        raise HTTPException(status_code=404, detail="Insight nicht gefunden")
    
    if insight.is_dismissed:
        raise HTTPException(status_code=400, detail="Insight wurde bereits ausgeblendet")
    
    insight.is_dismissed = True
    insight.dismissed_at = datetime.now()
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Insight #{insight_id} wurde ausgeblendet"
    }


@router.get("/statistics", response_model=InsightStatistics)
def get_insight_statistics(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    db: Session = Depends(get_db)
):
    """
    Get insight statistics
    
    Returns aggregate statistics about insights: counts by type, severity, account, etc.
    
    Args:
        account_id: Filter by account (None = all accounts)
        
    Returns:
        Statistics object
    """
    query = db.query(Insight)
    
    if account_id is not None:
        query = query.filter(or_(Insight.account_id == account_id, Insight.account_id.is_(None)))
    
    # Total counts
    total_insights = query.count()
    active_insights = query.filter(Insight.is_dismissed == False).count()
    dismissed_insights = query.filter(Insight.is_dismissed == True).count()
    
    # Insights by type
    type_counts = {}
    type_results = db.query(
        Insight.insight_type,
        func.count(Insight.id).label('count')
    ).group_by(Insight.insight_type).all()
    
    for insight_type, count in type_results:
        type_counts[insight_type] = count
    
    # Insights by severity
    severity_counts = {}
    severity_results = db.query(
        Insight.severity,
        func.count(Insight.id).label('count')
    ).group_by(Insight.severity).all()
    
    for severity, count in severity_results:
        severity_counts[severity] = count
    
    # Insights by account
    account_counts = {}
    account_results = db.query(
        Insight.account_id,
        func.count(Insight.id).label('count')
    ).group_by(Insight.account_id).all()
    
    for acc_id, count in account_results:
        account_counts[acc_id if acc_id is not None else 0] = count
    
    # Last generation timestamp
    last_log = db.query(InsightGenerationLog).order_by(
        InsightGenerationLog.generated_at.desc()
    ).first()
    
    return InsightStatistics(
        total_insights=total_insights,
        active_insights=active_insights,
        dismissed_insights=dismissed_insights,
        insights_by_type=type_counts,
        insights_by_severity=severity_counts,
        insights_by_account=account_counts,
        last_generation=last_log.generated_at if last_log else None
    )


@router.get("/generation-logs", response_model=List[InsightGenerationLogResponse])
def get_generation_logs(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of logs"),
    db: Session = Depends(get_db)
):
    """
    Get insight generation history
    
    Returns log entries of when insights were generated.
    
    Args:
        account_id: Filter by account (None = all accounts)
        limit: Maximum number of logs to return
        
    Returns:
        List of generation log entries
    """
    query = db.query(InsightGenerationLog)
    
    if account_id is not None:
        query = query.filter(
            or_(InsightGenerationLog.account_id == account_id, InsightGenerationLog.account_id.is_(None))
        )
    
    query = query.order_by(InsightGenerationLog.generated_at.desc())
    
    logs = query.limit(limit).all()
    
    return logs


@router.delete("/{insight_id}")
def delete_insight(
    insight_id: int,
    db: Session = Depends(get_db)
):
    """
    Permanently delete an insight
    
    Args:
        insight_id: ID of insight to delete
        
    Returns:
        Success message
    """
    insight = db.query(Insight).filter(Insight.id == insight_id).first()
    
    if not insight:
        raise HTTPException(status_code=404, detail="Insight nicht gefunden")
    
    db.delete(insight)
    db.commit()
    
    return {
        "success": True,
        "message": f"Insight #{insight_id} wurde gelöscht"
    }
