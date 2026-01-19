"""
Exposure Hierarchy Service for CBT (Cognitive Behavioral Therapy)
Tracks gradual exposure to feared situations to reduce anxiety
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid, timedelta
from sqlalchemy.orm import Session
from app.models.exposure_hierarchy import ExposureHierarchy, ExposureStatus
import logging

logger = logging.getLogger(__name__)


class ExposureHierarchyService:
    """Service for managing exposure hierarchies and gradual exposure therapy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_exposure_step(
        self,
        user_id: uuid.UUID,
        hierarchy_group: str,
        feared_situation: str,
        difficulty_level: int,
        anxiety_before: int,
        conversation_id: Optional[uuid.UUID] = None,
        scheduled_for: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> ExposureHierarchy:
        """
        Create a new exposure hierarchy step
        
        Args:
            user_id: User ID
            hierarchy_group: Name of the fear/hierarchy group
            feared_situation: What is the feared situation
            difficulty_level: Difficulty level (0-100 SUDS)
            anxiety_before: Anxiety before exposure (1-10)
            conversation_id: Optional conversation ID
            scheduled_for: When the exposure is scheduled
            notes: Additional notes
        
        Returns:
            Created exposure step
        """
        try:
            exposure_step = ExposureHierarchy(
                user_id=user_id,
                conversation_id=conversation_id,
                hierarchy_group=hierarchy_group,
                feared_situation=feared_situation,
                difficulty_level=difficulty_level,
                anxiety_before=anxiety_before,
                status=ExposureStatus.NOT_STARTED,
                scheduled_for=scheduled_for,
                notes=notes
            )
            
            self.db.add(exposure_step)
            self.db.commit()
            self.db.refresh(exposure_step)
            
            logger.info(f"Created exposure step {exposure_step.id} for user {user_id}")
            return exposure_step
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating exposure step: {e}")
            raise
    
    def get_exposure_step(self, step_id: uuid.UUID, user_id: uuid.UUID) -> Optional[ExposureHierarchy]:
        """Get a specific exposure step by ID"""
        return self.db.query(ExposureHierarchy).filter(
            ExposureHierarchy.id == step_id,
            ExposureHierarchy.user_id == user_id
        ).first()
    
    def get_user_exposure_steps(
        self,
        user_id: uuid.UUID,
        hierarchy_group: Optional[str] = None,
        status: Optional[ExposureStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ExposureHierarchy]:
        """Get exposure steps for a user, optionally filtered"""
        query = self.db.query(ExposureHierarchy).filter(
            ExposureHierarchy.user_id == user_id
        )
        
        if hierarchy_group:
            query = query.filter(ExposureHierarchy.hierarchy_group == hierarchy_group)
        
        if status:
            query = query.filter(ExposureHierarchy.status == status)
        
        return query.order_by(ExposureHierarchy.difficulty_level.asc()).limit(limit).offset(offset).all()
    
    def get_hierarchy_groups(self, user_id: uuid.UUID) -> List[str]:
        """Get all hierarchy groups for a user"""
        groups = self.db.query(ExposureHierarchy.hierarchy_group).filter(
            ExposureHierarchy.user_id == user_id
        ).distinct().all()
        
        return [g[0] for g in groups]
    
    def start_exposure(
        self,
        step_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[ExposureHierarchy]:
        """Mark an exposure step as in progress"""
        exposure = self.get_exposure_step(step_id, user_id)
        
        if not exposure:
            return None
        
        try:
            exposure.status = ExposureStatus.IN_PROGRESS
            exposure.scheduled_for = datetime.utcnow()
            self.db.commit()
            self.db.refresh(exposure)
            
            logger.info(f"Started exposure {step_id} for user {user_id}")
            return exposure
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error starting exposure: {e}")
            raise
    
    def complete_exposure(
        self,
        step_id: uuid.UUID,
        user_id: uuid.UUID,
        anxiety_during: Optional[int] = None,
        anxiety_after: int,
        duration_minutes: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Optional[ExposureHierarchy]:
        """
        Mark an exposure step as completed
        
        Args:
            step_id: Exposure step ID
            user_id: User ID
            anxiety_during: Anxiety during exposure (1-10)
            anxiety_after: Anxiety after exposure (1-10)
            duration_minutes: Duration of exposure in minutes
            notes: Optional notes about the experience
        
        Returns:
            Updated exposure step
        """
        exposure = self.get_exposure_step(step_id, user_id)
        
        if not exposure:
            return None
        
        try:
            exposure.anxiety_during = anxiety_during
            exposure.anxiety_after = anxiety_after
            exposure.status = ExposureStatus.COMPLETED
            exposure.completed_at = datetime.utcnow()
            exposure.duration_minutes = duration_minutes
            
            if notes:
                exposure.notes = notes
            
            self.db.commit()
            self.db.refresh(exposure)
            
            logger.info(f"Completed exposure {step_id} for user {user_id}")
            return exposure
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error completing exposure: {e}")
            raise
    
    def avoid_exposure(
        self,
        step_id: uuid.UUID,
        user_id: uuid.UUID,
        notes: Optional[str] = None
    ) -> Optional[ExposureHierarchy]:
        """Mark an exposure step as avoided"""
        exposure = self.get_exposure_step(step_id, user_id)
        
        if not exposure:
            return None
        
        try:
            exposure.status = ExposureStatus.AVOIDED
            
            if notes:
                exposure.notes = notes
            
            self.db.commit()
            self.db.refresh(exposure)
            
            logger.info(f"Avoided exposure {step_id} for user {user_id}")
            return exposure
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error avoiding exposure: {e}")
            raise
    
    def update_exposure_step(
        self,
        step_id: uuid.UUID,
        user_id: uuid.UUID,
        **kwargs
    ) -> Optional[ExposureHierarchy]:
        """Update an exposure step"""
        exposure = self.get_exposure_step(step_id, user_id)
        
        if not exposure:
            return None
        
        try:
            for key, value in kwargs.items():
                if hasattr(exposure, key) and value is not None:
                    setattr(exposure, key, value)
            
            exposure.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(exposure)
            
            logger.info(f"Updated exposure step {step_id}")
            return exposure
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating exposure step: {e}")
            raise
    
    def delete_exposure_step(self, step_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete an exposure step"""
        exposure = self.get_exposure_step(step_id, user_id)
        
        if not exposure:
            return False
        
        try:
            self.db.delete(exposure)
            self.db.commit()
            logger.info(f"Deleted exposure step {step_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting exposure step: {e}")
            raise
    
    def get_exposure_progress(
        self,
        user_id: uuid.UUID,
        hierarchy_group: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get progress report for a hierarchy group
        
        Args:
            user_id: User ID
            hierarchy_group: Name of the hierarchy group
            days: Number of days to analyze
        
        Returns:
            Dictionary with progress report
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        exposures = self.db.query(ExposureHierarchy).filter(
            ExposureHierarchy.user_id == user_id,
            ExposureHierarchy.hierarchy_group == hierarchy_group,
            ExposureHierarchy.created_at >= since_date
        ).all()
        
        completed = [e for e in exposures if e.status == ExposureStatus.COMPLETED]
        avoided = [e for e in exposures if e.status == ExposureStatus.AVOIDED]
        in_progress = [e for e in exposures if e.status == ExposureStatus.IN_PROGRESS]
        
        # Calculate average anxiety reduction
        avg_reduction = None
        if completed:
            reductions = [e.anxiety_reduction for e in completed if e.anxiety_reduction]
            if reductions:
                avg_reduction = sum(reductions) / len(reductions)
        
        # Calculate completion rate
        completion_rate = round(len(completed) / len(exposures) * 100, 1) if exposures else 0
        
        return {
            "hierarchy_group": hierarchy_group,
            "total_exposures": len(exposures),
            "completed": len(completed),
            "avoided": len(avoided),
            "in_progress": len(in_progress),
            "completion_rate": completion_rate,
            "avg_anxiety_reduction": round(avg_reduction, 2) if avg_reduction else None,
            "period_days": days
        }
    
    def get_next_exposure_step(
        self,
        user_id: uuid.UUID,
        hierarchy_group: str
    ) -> Optional[ExposureHierarchy]:
        """
        Get the next exposure step to work on (not started, lowest difficulty)
        
        Args:
            user_id: User ID
            hierarchy_group: Name of the hierarchy group
        
        Returns:
            Next exposure step to work on
        """
        exposure = self.db.query(ExposureHierarchy).filter(
            ExposureHierarchy.user_id == user_id,
            ExposureHierarchy.hierarchy_group == hierarchy_group,
            ExposureHierarchy.status == ExposureStatus.NOT_STARTED
        ).order_by(ExposureHierarchy.difficulty_level.asc()).first()
        
        return exposure
    
    def get_anxiety_trends(
        self,
        user_id: uuid.UUID,
        hierarchy_group: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze anxiety trends over time
        
        Args:
            user_id: User ID
            hierarchy_group: Optional hierarchy group filter
            days: Number of days to analyze
        
        Returns:
            Dictionary with anxiety trends
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(ExposureHierarchy).filter(
            ExposureHierarchy.user_id == user_id,
            ExposureHierarchy.created_at >= since_date,
            ExposureHierarchy.status == ExposureStatus.COMPLETED
        )
        
        if hierarchy_group:
            query = query.filter(ExposureHierarchy.hierarchy_group == hierarchy_group)
        
        exposures = query.all()
        
        if not exposures:
            return {
                "avg_anxiety_before": None,
                "avg_anxiety_after": None,
                "avg_reduction": None,
                "total_exposures": 0
            }
        
        avg_before = sum(e.anxiety_before for e in exposures) / len(exposures)
        avg_after = sum(e.anxiety_after for e in exposures) / len(exposures)
        avg_reduction = sum(e.anxiety_reduction for e in exposures if e.anxiety_reduction) / len(exposures)
        
        return {
            "avg_anxiety_before": round(avg_before, 2),
            "avg_anxiety_after": round(avg_after, 2),
            "avg_reduction": round(avg_reduction, 2),
            "total_exposures": len(exposures)
        }
    
    def suggest_next_step(
        self,
        user_id: uuid.UUID,
        hierarchy_group: str
    ) -> Optional[Dict[str, Any]]:
        """
        Suggest the next exposure step with guidance
        
        Args:
            user_id: User ID
            hierarchy_group: Name of the hierarchy group
        
        Returns:
            Dictionary with next step suggestion and guidance
        """
        # Get next not started step
        next_step = self.get_next_exposure_step(user_id, hierarchy_group)
        
        if not next_step:
            return None
        
        # Get progress for context
        progress = self.get_exposure_progress(user_id, hierarchy_group, days=30)
        
        # Generate guidance based on difficulty
        difficulty = next_step.difficulty_category
        
        guidance = {
            "step_id": next_step.id,
            "feared_situation": next_step.feared_situation,
            "difficulty_level": next_step.difficulty_level,
            "difficulty_category": difficulty,
            "anxiety_before": next_step.anxiety_before,
            "guidance": ""
        }
        
        if difficulty == "easy":
            guidance["guidance"] = "This is an easy step. Great place to start building confidence!"
        elif difficulty == "moderate":
            guidance["guidance"] = "This is a moderate challenge. Take your time and remember your coping strategies."
        elif difficulty == "challenging":
            guidance["guidance"] = "This is challenging. Consider having support available and prepare coping techniques."
        else:
            guidance["guidance"] = "This is a difficult step. Make sure you're well-prepared and have support if needed."
        
        # Add context from progress
        if progress["completion_rate"] > 70:
            guidance["guidance"] += f" You've completed {progress['completion_rate']}% of exposures - you're making great progress!"
        
        return guidance
    
    def get_hierarchy_summary(
        self,
        user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """
        Get summary of all hierarchy groups for a user
        
        Args:
            user_id: User ID
        
        Returns:
            List of hierarchy group summaries
        """
        groups = self.get_hierarchy_groups(user_id)
        
        summaries = []
        for group in groups:
            progress = self.get_exposure_progress(user_id, group, days=30)
            summaries.append(progress)
        
        return summaries