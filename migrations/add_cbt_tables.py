"""
Migration script for Phase 4 CBT tables
Adds ThoughtRecord, BehavioralActivation, and ExposureHierarchy tables
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine
from app.models import (
    ThoughtRecord, 
    BehavioralActivation, 
    ExposureHierarchy
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Create CBT tables in the database"""
    
    logger.info("Starting Phase 4 CBT tables migration...")
    
    try:
        # Create tables
        logger.info("Creating thought_records table...")
        ThoughtRecord.__table__.create(engine, checkfirst=True)
        
        logger.info("Creating behavioral_activations table...")
        BehavioralActivation.__table__.create(engine, checkfirst=True)
        
        logger.info("Creating exposure_hierarchies table...")
        ExposureHierarchy.__table__.create(engine, checkfirst=True)
        
        logger.info("✅ CBT tables created successfully!")
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_migration()
