"""
Thought Record Service for CBT (Cognitive Behavioral Therapy)
Handles cognitive restructuring and thought record management
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.thought_record import ThoughtRecord, CognitiveDistortionType
from app.models.user import User
from app.models.conversation import Conversation
import uuid
import logging

logger = logging.getLogger(__name__)


class ThoughtRecordService:
    """Service for managing thought records and cognitive restructuring"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_thought_record(
        self,
        user_id: uuid.UUID,
        situation: str,
        automatic_thought: str,
        emotion: str,
        emotion_intensity: int,
        cognitive_distortion: CognitiveDistortionType,
        conversation_id: Optional[uuid.UUID] = None,
        evidence_for: Optional[str] = None,
        evidence_against: Optional[str] = None,
        challenging_thought: Optional[str] = None,
        outcome: Optional[str] = None,
        outcome_intensity: Optional[int] = None
    ) -> ThoughtRecord:
        """
        Create a new thought record
        
        Args:
            user_id: User ID (UUID)
            situation: What happened
            automatic_thought: The automatic negative thought
            emotion: Emotion felt
            emotion_intensity: Emotion intensity (1-10)
            cognitive_distortion: Type of cognitive distortion
            conversation_id: Optional conversation ID (UUID)
            evidence_for: Evidence supporting the thought
            evidence_against: Evidence against the thought
            challenging_thought: Balanced alternative thought
            outcome: Outcome after challenging
            outcome_intensity: Emotion intensity after (1-10)
        
        Returns:
            Created thought record
        """
        try:
            thought_record = ThoughtRecord(
                user_id=user_id,
                conversation_id=conversation_id,
                situation=situation,
                automatic_thought=automatic_thought,
                emotion=emotion,
                emotion_intensity=emotion_intensity,
                cognitive_distortion=cognitive_distortion,
                evidence_for=evidence_for,
                evidence_against=evidence_against,
                challenging_thought=challenging_thought,
                outcome=outcome,
                outcome_intensity=outcome_intensity
            )
            
            self.db.add(thought_record)
            self.db.commit()
            self.db.refresh(thought_record)
            
            logger.info(f"Created thought record {thought_record.id} for user {user_id}")
            return thought_record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating thought record: {e}")
            raise
    
    def get_thought_record(self, record_id: uuid.UUID, user_id: uuid.UUID) -> Optional[ThoughtRecord]:
        """Get a specific thought record by ID"""
        return self.db.query(ThoughtRecord).filter(
            ThoughtRecord.id == record_id,
            ThoughtRecord.user_id == user_id
        ).first()
    
    def get_user_thought_records(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[ThoughtRecord]:
        """Get all thought records for a user"""
        return self.db.query(ThoughtRecord).filter(
            ThoughtRecord.user_id == user_id
        ).order_by(ThoughtRecord.created_at.desc()).limit(limit).offset(offset).all()
    
    def update_thought_record(
        self,
        record_id: uuid.UUID,
        user_id: uuid.UUID,
        **kwargs
    ) -> Optional[ThoughtRecord]:
        """Update a thought record"""
        thought_record = self.get_thought_record(record_id, user_id)
        
        if not thought_record:
            return None
        
        try:
            for key, value in kwargs.items():
                if hasattr(thought_record, key) and value is not None:
                    setattr(thought_record, key, value)
            
            thought_record.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(thought_record)
            
            logger.info(f"Updated thought record {record_id}")
            return thought_record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating thought record: {e}")
            raise
    
    def delete_thought_record(self, record_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a thought record"""
        thought_record = self.get_thought_record(record_id, user_id)
        
        if not thought_record:
            return False
        
        try:
            self.db.delete(thought_record)
            self.db.commit()
            logger.info(f"Deleted thought record {record_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting thought record: {e}")
            raise
    
    def get_distortion_patterns(
        self,
        user_id: uuid.UUID,
        days: int = 30
    ) -> Dict[str, int]:
        """
        Analyze cognitive distortion patterns for a user
        
        Args:
            user_id: User ID (UUID)
            days: Number of days to analyze
        
        Returns:
            Dictionary mapping distortion types to counts
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        records = self.db.query(ThoughtRecord).filter(
            ThoughtRecord.user_id == user_id,
            ThoughtRecord.created_at >= since_date
        ).all()
        
        patterns = {}
        for record in records:
            distortion = record.cognitive_distortion.value if record.cognitive_distortion else "unknown"
            patterns[distortion] = patterns.get(distortion, 0) + 1
        
        return patterns
    
    def get_most_common_distortions(
        self,
        user_id: uuid.UUID,
        days: int = 30,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get the most common cognitive distortions for a user
        
        Args:
            user_id: User ID (UUID)
            days: Number of days to analyze
            limit: Number of top distortions to return
        
        Returns:
            List of dictionaries with distortion type and count
        """
        patterns = self.get_distortion_patterns(user_id, days)
        
        sorted_patterns = sorted(
            patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {
                "distortion": distortion,
                "count": count,
                "percentage": round((count / sum(patterns.values()) * 100), 1) if patterns else 0
            }
            for distortion, count in sorted_patterns[:limit]
        ]
    
    def get_emotion_trends(
        self,
        user_id: uuid.UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze emotion intensity trends over time
        
        Args:
            user_id: User ID (UUID)
            days: Number of days to analyze
        
        Returns:
            Dictionary with emotion trends
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        records = self.db.query(ThoughtRecord).filter(
            ThoughtRecord.user_id == user_id,
            ThoughtRecord.created_at >= since_date
        ).all()
        
        completed_records = [r for r in records if r.is_complete]
        
        if not completed_records:
            return {
                "avg_intensity_before": None,
                "avg_intensity_after": None,
                "avg_improvement": None,
                "total_records": len(records),
                "completed_records": 0
            }
        
        avg_before = sum(r.emotion_intensity for r in completed_records) / len(completed_records)
        avg_after = sum(r.outcome_intensity for r in completed_records if r.outcome_intensity) / len([r for r in completed_records if r.outcome_intensity])
        avg_improvement = sum(r.intensity_change for r in completed_records if r.intensity_change) / len([r for r in completed_records if r.intensity_change])
        
        return {
            "avg_intensity_before": round(avg_before, 2),
            "avg_intensity_after": round(avg_after, 2),
            "avg_improvement": round(avg_improvement, 2),
            "total_records": len(records),
            "completed_records": len(completed_records)
        }
    
    def get_insights(
        self,
        user_id: uuid.UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive insights about a user's thought patterns
        
        Args:
            user_id: User ID (UUID)
            days: Number of days to analyze
        
        Returns:
            Dictionary with insights
        """
        patterns = self.get_distortion_patterns(user_id, days)
        common_distortions = self.get_most_common_distortions(user_id, days)
        trends = self.get_emotion_trends(user_id, days)
        
        return {
            "period_days": days,
            "total_records": sum(patterns.values()),
            "distortion_patterns": patterns,
            "common_distortions": common_distortions,
            "emotion_trends": trends,
            "completion_rate": round(
                trends["completed_records"] / trends["total_records"] * 100, 1
            ) if trends["total_records"] > 0 else 0
        }
    
    def suggest_challenging_questions(
        self,
        cognitive_distortion: CognitiveDistortionType
    ) -> List[str]:
        """
        Suggest challenging questions based on cognitive distortion type
        
        Args:
            cognitive_distortion: Type of cognitive distortion
        
        Returns:
            List of challenging questions
        """
        questions = {
            CognitiveDistortionType.ALL_OR_NOTHING: [
                "Is there any middle ground here?",
                "Can you see this as shades of gray rather than black and white?",
                "What would happen if things were partially good and partially bad?"
            ],
            CognitiveDistortionType.OVERGENERALIZATION: [
                "Is this one situation really proof of a universal rule?",
                "Have there been exceptions to this pattern?",
                "What evidence do you have that this ALWAYS happens?"
            ],
            CognitiveDistortionType.MENTAL_FILTER: [
                "What positive aspects are you filtering out?",
                "Can you list three things that went well?",
                "Are you ignoring any strengths or successes?"
            ],
            CognitiveDistortionType.DISQUALIFYING_POSITIVE: [
                "Why are you dismissing this positive experience?",
                "What would you say if a friend told you this?",
                "Can you accept this as genuine progress?"
            ],
            CognitiveDistortionType.JUMPING_CONCLUSIONS: [
                "What evidence do you actually have for this?",
                "Are you mind-reading or fortune-telling?",
                "What are other possible explanations?"
            ],
            CognitiveDistortionType.MAGNIFICATION: [
                "Is this really as catastrophic as it seems?",
                "On a scale of 1-10, how bad is this really?",
                "What's the worst that could actually happen?"
            ],
            CognitiveDistortionType.MINIMIZATION: [
                "Why are you downplaying this?",
                "What would someone else say about this?",
                "Can you acknowledge your strengths here?"
            ],
            CognitiveDistortionType.EMOTIONAL_REASONING: [
                "Just because you feel it, does that make it true?",
                "What facts contradict this feeling?",
                "How would you view this if you felt differently?"
            ],
            CognitiveDistortionType.SHOULD_STATEMENTS: [
                "Who says you should?",
                "What if you dropped the 'should'?",
                "Is this expectation realistic?"
            ],
            CognitiveDistortionType.LABELING: [
                "What if you described the behavior instead of labeling yourself?",
                "Are you really 'always' this way?",
                "What would you say to a friend in this situation?"
            ],
            CognitiveDistortionType.PERSONALIZATION: [
                "What other factors contributed to this?",
                "Are you taking responsibility for something out of your control?",
                "What role did others play in this?"
            ]
        }
        
        return questions.get(cognitive_distortion, [
            "What evidence supports this thought?",
            "What evidence contradicts this thought?",
            "What's a more balanced way to look at this?"
        ])
