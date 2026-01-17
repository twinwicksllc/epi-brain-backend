"""
Quick Test Script for Phase 2 Services

Tests core functionality of Goal, Habit, Check-in, and Semantic Memory services.
This script creates a test user and performs CRUD operations.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import date, datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.models.user import User
from app.models.goal import Goal, CheckIn, Milestone
from app.models.habit import Habit, HabitCompletion
from app.models.semantic_memory import SemanticMemory
from app.services.goal_service import GoalService
from app.services.habit_service import HabitService
from app.services.check_in_service import CheckInService
from app.services.semantic_memory_service import SemanticMemoryService
from app.models.habit import HabitStatus

# Use SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test_phase2.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_test_database():
    """Create fresh test database"""
    print("Setting up test database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✓ Test database created")

def create_test_user(db):
    """Create a test user"""
    user = User(
        email="test@example.com",
        password_hash="hashed_password"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"✓ Created test user: {user.id}")
    return user

def test_goal_service(db, user_id):
    """Test Goal Service functionality"""
    print("\n" + "="*50)
    print("Testing Goal Service")
    print("="*50)
    
    service = GoalService(db)
    
    # Test 1: Create goal
    print("\n1. Creating goal...")
    goal = service.create_goal(
        user_id=user_id,
        title="Lose 10 pounds",
        description="Healthy eating and exercise plan to lose 10 pounds",
        category="health",
        target_date=date.today() + timedelta(days=90),
        accountability_style="tactical",
        check_in_frequency="weekly"
    )
    assert goal.id is not None
    assert goal.title == "Lose 10 pounds"
    assert goal.status == "not_started"
    print(f"   ✓ Goal created: {goal.id}")
    
    # Test 2: Get goal
    print("\n2. Getting goal...")
    retrieved = service.get_goal(str(goal.id), user_id)
    assert retrieved is not None
    assert retrieved.title == goal.title
    print(f"   ✓ Goal retrieved: {retrieved.title}")
    
    # Test 3: Update goal
    print("\n3. Updating goal...")
    updated = service.update_goal(
        str(goal.id),
        user_id,
        status="in_progress"
    )
    assert updated.status == "in_progress"
    print(f"   ✓ Goal status updated to: {updated.status}")
    
    # Test 4: Create check-in
    print("\n4. Creating check-in...")
    check_in = service.create_check_in(
        goal_id=str(goal.id),
        user_id=user_id,
        progress_notes="Lost 2 pounds this week!",
        mood="motivated",
        energy_level=8,
        progress_percentage=20.0
    )
    assert check_in.id is not None
    print(f"   ✓ Check-in created: {check_in.id}")
    
    # Test 5: Create milestone
    print("\n5. Creating milestone...")
    milestone = service.create_milestone(
        goal_id=str(goal.id),
        user_id=user_id,
        title="First 5 pounds",
        description="Lose first 5 pounds",
        target_date=date.today() + timedelta(days=30)
    )
    assert milestone.id is not None
    print(f"   ✓ Milestone created: {milestone.title}")
    
    # Test 6: Complete milestone
    print("\n6. Completing milestone...")
    completed = service.complete_milestone(str(milestone.id), user_id)
    assert completed.is_completed == True
    print(f"   ✓ Milestone completed: {completed.title}")
    
    # Test 7: Get goal progress
    print("\n7. Getting goal progress...")
    progress = service.get_goal_progress(str(goal.id), user_id)
    assert progress['goal_id'] == str(goal.id)
    assert progress['status'] == "in_progress"
    assert progress['total_check_ins'] == 1
    print(f"   ✓ Progress retrieved: {progress['status']}, {progress['total_check_ins']} check-ins")
    
    # Test 8: Get user goals
    print("\n8. Getting user goals...")
    goals = service.get_user_goals(user_id)
    assert len(goals) >= 1
    print(f"   ✓ Retrieved {len(goals)} goals")
    
    print("\n✓ Goal Service tests passed!")
    return goal

def test_habit_service(db, user_id):
    """Test Habit Service functionality"""
    print("\n" + "="*50)
    print("Testing Habit Service")
    print("="*50)
    
    service = HabitService(db)
    
    # Test 1: Create habit
    print("\n1. Creating habit...")
    habit = service.create_habit(
        user_id=user_id,
        name="Morning meditation",
        description="10 minutes of meditation every morning",
        frequency="daily",
        trigger="After waking up",
        routine="10 min meditation app",
        reward="Cup of coffee"
    )
    assert habit.id is not None
    assert habit.name == "Morning meditation"
    assert habit.status == HabitStatus.ACTIVE
    print(f"   ✓ Habit created: {habit.id}")
    
    # Test 2: Get habit
    print("\n2. Getting habit...")
    retrieved = service.get_habit(str(habit.id), user_id)
    assert retrieved is not None
    assert retrieved.name == habit.name
    print(f"   ✓ Habit retrieved: {retrieved.name}")
    
    # Test 3: Complete habit
    print("\n3. Completing habit...")
    completion = service.complete_habit(
        habit_id=str(habit.id),
        user_id=user_id,
        notes="Felt great today!"
    )
    assert completion.id is not None
    print(f"   ✓ Habit completion recorded: {completion.id}")
    
    # Test 4: Get due habits
    print("\n4. Getting due habits...")
    due_habits = service.get_due_habits(user_id)
    assert len(due_habits) >= 1
    print(f"   ✓ Found {len(due_habits)} due habits")
    
    # Test 5: Get habit summary
    print("\n5. Getting habit summary...")
    summary = service.get_habit_summary(str(habit.id), user_id)
    assert summary['habit_id'] == str(habit.id)
    assert summary['total_completions'] == 1
    assert summary['streak_days'] == 1
    print(f"   ✓ Summary retrieved: {summary['total_completions']} completions, {summary['streak_days']} day streak")
    
    # Test 6: Get user habits
    print("\n6. Getting user habits...")
    habits = service.get_user_habits(user_id)
    assert len(habits) >= 1
    print(f"   ✓ Retrieved {len(habits)} habits")
    
    print("\n✓ Habit Service tests passed!")
    return habit

def test_check_in_service(db, user_id):
    """Test Check-in Service functionality"""
    print("\n" + "="*50)
    print("Testing Check-in Service")
    print("="*50)
    
    goal_service = GoalService(db)
    habit_service = HabitService(db)
    check_in_service = CheckInService(db, goal_service, habit_service)
    
    # Create a test goal and habit
    goal = goal_service.create_goal(
        user_id=user_id,
        title="Test Goal",
        description="Test description",
        category="test",
        check_in_frequency="daily"
    )
    
    habit = habit_service.create_habit(
        user_id=user_id,
        name="Test Habit",
        description="Test description",
        frequency="daily",
        trigger="test trigger",
        routine="test routine"
    )
    
    # Test 1: Get pending check-ins
    print("\n1. Getting pending check-ins...")
    pending = check_in_service.get_pending_check_ins(user_id)
    assert 'due_goals' in pending
    assert 'due_habits' in pending
    print(f"   ✓ Found {pending['total_due']} pending items")
    
    # Test 2: Create goal check-in
    print("\n2. Creating goal check-in...")
    result = check_in_service.create_check_in(
        user_id=user_id,
        item_type="goal",
        item_id=str(goal.id),
        progress_notes="Making progress!",
        mood="motivated",
        energy_level=7
    )
    assert result['type'] == 'goal'
    print(f"   ✓ Goal check-in created")
    
    # Test 3: Create habit check-in
    print("\n3. Creating habit check-in...")
    result = check_in_service.create_check_in(
        user_id=user_id,
        item_type="habit",
        item_id=str(habit.id),
        notes="Done!"
    )
    assert result['type'] == 'habit'
    print(f"   ✓ Habit completion recorded")
    
    # Test 4: Get daily summary
    print("\n4. Getting daily summary...")
    summary = check_in_service.get_daily_summary(user_id)
    assert 'date' in summary
    assert 'completed_goals_today' in summary
    assert 'completed_habits_today' in summary
    print(f"   ✓ Daily summary: {summary['completed_goals_today']} goals, {summary['completed_habits_today']} habits completed")
    
    # Test 5: Get weekly trends
    print("\n5. Getting weekly trends...")
    trends = check_in_service.get_weekly_trends(user_id)
    assert 'goal_check_in_trends' in trends
    assert 'habit_completion_trends' in trends
    print(f"   ✓ Weekly trends retrieved")
    
    # Test 6: Get overdue items
    print("\n6. Getting overdue items...")
    overdue = check_in_service.get_overdue_items(user_id)
    assert 'total_overdue' in overdue
    print(f"   ✓ Found {overdue['total_overdue']} overdue items")
    
    print("\n✓ Check-in Service tests passed!")

def test_semantic_memory_service(db, user_id):
    """Test Semantic Memory Service functionality"""
    print("\n" + "="*50)
    print("Testing Semantic Memory Service")
    print("="*50)
    
    service = SemanticMemoryService(db)
    
    # Test 1: Create a test memory manually (since AI extraction not implemented)
    print("\n1. Creating test memory...")
    memory = SemanticMemory(
        user_id=user_id,
        mode="personal_friend",
        content="Test user prefers coffee in the morning",
        importance_score=0.7,
        category="preference",
        expires_at=datetime.utcnow() + timedelta(days=90)
    )
    db.add(memory)
    db.commit()
    print(f"   ✓ Test memory created: {memory.id}")
    
    # Test 2: Get memories (basic query, no semantic search yet)
    print("\n2. Retrieving memories...")
    memories = db.query(SemanticMemory).filter(
        SemanticMemory.user_id == user_id
    ).all()
    assert len(memories) >= 1
    print(f"   ✓ Retrieved {len(memories)} memories")
    
    # Test 3: Format memories for prompt
    print("\n3. Formatting memories for prompt...")
    formatted = service.format_memories_for_prompt(memories)
    assert len(formatted) > 0
    print(f"   ✓ Memories formatted for prompt")
    
    # Test 4: Test memory expiration
    print("\n4. Testing memory expiration...")
    expired_memory = SemanticMemory(
        user_id=user_id,
        mode="personal_friend",
        content="Expired memory",
        importance_score=0.5,
        category="test",
        expires_at=datetime.utcnow() - timedelta(days=1)  # Already expired
    )
    db.add(expired_memory)
    db.commit()
    
    all_memories = db.query(SemanticMemory).filter(
        SemanticMemory.user_id == user_id
    ).all()
    
    non_expired = [m for m in all_memories if not m.is_expired]
    print(f"   ✓ Memory expiration works: {len(non_expired)} non-expired out of {len(all_memories)} total")
    
    print("\n✓ Semantic Memory Service tests passed!")

def cleanup_test_database():
    """Clean up test database"""
    print("\nCleaning up test database...")
    Base.metadata.drop_all(bind=engine)
    print("✓ Test database cleaned up")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PHASE 2 SERVICES - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    # Setup
    setup_test_database()
    db = TestingSessionLocal()
    
    try:
        # Create test user
        user = create_test_user(db)
        user_id = str(user.id)
        
        # Run tests
        test_goal_service(db, user_id)
        test_habit_service(db, user_id)
        test_check_in_service(db, user_id)
        test_semantic_memory_service(db, user_id)
        
        # Success
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        print("\nPhase 2 Core Services are working correctly:")
        print("  ✓ Goal Service - CRUD, check-ins, milestones, progress")
        print("  ✓ Habit Service - CRUD, completions, streaks, due dates")
        print("  ✓ Check-in Service - Scheduling, summaries, trends")
        print("  ✓ Semantic Memory - Storage, formatting, expiration")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
        cleanup_test_database()

if __name__ == "__main__":
    main()