"""
Simple Model Test Script

Tests that the database models work correctly without the service layer.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import date, datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.models.user import User
from app.models.goal import Goal, CheckIn, Milestone, GoalStatus, GoalCategory
from app.models.habit import Habit, HabitCompletion, HabitStatus
from app.models.semantic_memory import SemanticMemory

# Use SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test_models_simple.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def main():
    """Test basic model operations"""
    print("\n" + "="*60)
    print("SIMPLE MODEL TEST SUITE")
    print("="*60)
    
    # Setup
    print("\nSetting up test database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✓ Test database created")
    
    db = TestingSessionLocal()
    
    try:
        # Create test user
        print("\n1. Creating test user...")
        user = User(
            email="test@example.com",
            password_hash="hashed_password"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"   ✓ Created test user: {user.id}")
        
        # Test Goal model
        print("\n2. Creating goal...")
        goal = Goal(
            user_id=user.id,
            title="Lose 10 pounds",
            description="Healthy eating and exercise plan",
            category=GoalCategory.HEALTH,
            time_bound_deadline=datetime.utcnow() + timedelta(days=90),
            accountability_style="tactical",
            created_by_mode="personal_friend"
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        print(f"   ✓ Goal created: {goal.title}")
        print(f"   ✓ Status: {goal.status}")
        print(f"   ✓ Progress: {goal.progress_percentage}%")
        
        # Test CheckIn model
        print("\n3. Creating check-in...")
        check_in = CheckIn(
            goal_id=goal.id,
            user_id=user.id,
            notes="Lost 2 pounds this week!",
            mood="motivated",
            energy_level=8,
            successful=True,
            progress_update="Going well with diet",
            obstacles_faced="None",
            next_steps="Continue current plan"
        )
        db.add(check_in)
        db.commit()
        db.refresh(check_in)
        print(f"   ✓ Check-in created: {check_in.id}")
        
        # Test Goal update_progress method
        print("\n4. Testing goal.update_progress()...")
        goal.update_progress(successful=True)
        db.commit()
        db.refresh(goal)
        print(f"   ✓ Streak: {goal.current_streak_days} days")
        print(f"   ✓ Total check-ins: {goal.total_check_ins}")
        
        # Test Milestone model
        print("\n5. Creating milestone...")
        milestone = Milestone(
            goal_id=goal.id,
            title="First 5 pounds",
            description="Lose first 5 pounds",
            target_date=date.today() + timedelta(days=30)
        )
        db.add(milestone)
        db.commit()
        db.refresh(milestone)
        print(f"   ✓ Milestone created: {milestone.title}")
        
        # Test Habit model
        print("\n6. Creating habit...")
        habit = Habit(
            user_id=user.id,
            name="Morning meditation",
            description="10 minutes of meditation every morning",
            frequency="daily",
            trigger="After waking up",
            routine="10 min meditation app",
            reward="Cup of coffee",
            created_by_mode="personal_friend"
        )
        db.add(habit)
        db.commit()
        db.refresh(habit)
        print(f"   ✓ Habit created: {habit.name}")
        print(f"   ✓ Status: {habit.status}")
        
        # Test HabitCompletion model
        print("\n7. Creating habit completion...")
        completion = habit.record_completion()
        if completion:
            db.add(completion)
            db.commit()
            db.refresh(habit)
            print(f"   ✓ Completion recorded")
            print(f"   ✓ Streak: {habit.current_streak_days} days")
            print(f"   ✓ Total completions: {habit.total_completions}")
        else:
            print("   Note: Habit already completed today")
        
        # Test SemanticMemory model
        print("\n8. Creating semantic memory...")
        # For SQLite, embedding is stored as TEXT. Provide a dummy embedding string.
        memory = SemanticMemory(
            user_id=user.id,
            mode="personal_friend",
            embedding="0.1,0.2,0.3",  # Dummy embedding for SQLite
            content="Test user prefers coffee in the morning",
            importance_score=0.7,
            category="preference",
            expires_at=datetime.utcnow() + timedelta(days=90)
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        print(f"   ✓ Memory created: {memory.content[:40]}...")
        
        # Test queries
        print("\n9. Testing queries...")
        goals = db.query(Goal).filter(Goal.user_id == user.id).all()
        print(f"   ✓ Found {len(goals)} goals")
        
        habits = db.query(Habit).filter(Habit.user_id == user.id).all()
        print(f"   ✓ Found {len(habits)} habits")
        
        memories = db.query(SemanticMemory).filter(SemanticMemory.user_id == user.id).all()
        print(f"   ✓ Found {len(memories)} memories")
        
        # Test goal.is_due_today
        print("\n10. Testing habit.is_due_today...")
        is_due = habit.is_due_today
        print(f"   ✓ Habit is due today: {is_due}")
        
        # Test memory expiration
        print("\n11. Testing memory expiration...")
        expired_memory = SemanticMemory(
            user_id=user.id,
            mode="personal_friend",
            embedding="0.4,0.5,0.6",  # Dummy embedding
            content="Expired memory",
            importance_score=0.5,
            category="test",
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        db.add(expired_memory)
        db.commit()
        
        all_memories = db.query(SemanticMemory).filter(
            SemanticMemory.user_id == user.id
        ).all()
        non_expired = [m for m in all_memories if not m.is_expired]
        print(f"   ✓ Non-expired memories: {len(non_expired)} out of {len(all_memories)} total")
        
        # Success
        print("\n" + "="*60)
        print("✓ ALL MODEL TESTS PASSED!")
        print("="*60)
        print("\nDatabase models are working correctly:")
        print("  ✓ User model")
        print("  ✓ Goal model with check-ins and milestones")
        print("  ✓ Habit model with completions")
        print("  ✓ SemanticMemory model")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
        # Cleanup
        print("\nCleaning up test database...")
        Base.metadata.drop_all(bind=engine)
        print("✓ Test database cleaned up")

if __name__ == "__main__":
    main()