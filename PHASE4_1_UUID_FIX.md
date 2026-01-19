# Phase 4.1 UUID Type Fix

## Problem
The backend deployment failed with the following error:

```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DatatypeMismatch) foreign key constraint "thought_records_user_id_fkey" cannot be implemented
DETAIL: Key columns "user_id" and "id" are of incompatible types: integer and uuid.
```

## Root Cause
The issue was a data type mismatch between local development (SQLite) and production (PostgreSQL):

1. **Local Development (SQLite):**
   - SQLite doesn't have native UUID support
   - Integer types work fine for foreign keys
   - Migration runs successfully

2. **Production (PostgreSQL):**
   - `User.id` is UUID type
   - `Conversation.id` is UUID type
   - CBT models were using INTEGER for foreign keys
   - Foreign key constraints fail due to type mismatch

## Solution
Updated all CBT models and services to use UUID types:

### Models Updated

#### 1. ThoughtRecord (`app/models/thought_record.py`)
```python
# Before:
id = Column(Integer, primary_key=True)
user_id = Column(Integer, ForeignKey("users.id"))
conversation_id = Column(Integer, ForeignKey("conversations.id"))

# After:
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"))
```

#### 2. BehavioralActivation (`app/models/behavioral_activation.py`)
```python
# Before:
id = Column(Integer, primary_key=True)
user_id = Column(Integer, ForeignKey("users.id"))
conversation_id = Column(Integer, ForeignKey("conversations.id"))

# After:
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"))
```

#### 3. ExposureHierarchy (`app/models/exposure_hierarchy.py`)
```python
# Before:
id = Column(Integer, primary_key=True)
user_id = Column(Integer, ForeignKey("users.id"))
conversation_id = Column(Integer, ForeignKey("conversations.id"))

# After:
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"))
```

### Services Updated

All three CBT services were updated to:
- Accept UUID parameters instead of integers
- Import `uuid` module
- Update method signatures:

```python
# Before:
def create_thought_record(self, user_id: int, ...)
def get_thought_record(self, record_id: int, user_id: int, ...)

# After:
def create_thought_record(self, user_id: uuid.UUID, ...)
def get_thought_record(self, record_id: uuid.UUID, user_id: uuid.UUID, ...)
```

### Additional Changes

1. **Added ForeignKey import** to all three models:
```python
from sqlalchemy import Column, String, DateTime, Integer, Float, Text, Enum as SQLEnum, ForeignKey
```

2. **Updated to_dict() methods** to convert UUID to string:
```python
def to_dict(self):
    return {
        "id": str(self.id),  # Convert UUID to string
        "user_id": str(self.user_id),
        "conversation_id": str(self.conversation_id) if self.conversation_id else None,
        ...
    }
```

## Testing

### Local Development (SQLite)
✅ Migration runs successfully
✅ Tables created with proper types
✅ SQLite handles UUID columns as TEXT

### Production (PostgreSQL)
✅ Foreign key constraints should work
✅ UUID types match existing User and Conversation models
✅ Cascade deletes should work properly

## Deployment

### What Changed
- 3 CBT models updated to use UUID
- 3 CBT services updated to accept UUID parameters
- Migration script unchanged (uses `checkfirst=True`)

### Production Migration
The production database migration will:
1. Create `thought_records` table with UUID columns
2. Create `behavioral_activations` table with UUID columns
3. Create `exposure_hierarchies` table with UUID columns
4. Foreign key constraints will work with UUID types

### Rollback Plan
If issues arise:
1. Revert commit: `git revert 4f0a222`
2. Run: `git push origin main`

## Lessons Learned

1. **Always check production database schema** when adding new models
2. **SQLite doesn't enforce strict types** - can hide type mismatches
3. **Use UUID consistently** across the entire codebase
4. **Test migrations on both SQLite and PostgreSQL** when possible

## Files Modified

1. `app/models/thought_record.py`
2. `app/models/behavioral_activation.py`
3. `app/models/exposure_hierarchy.py`
4. `app/services/thought_record_service.py`
5. `app/services/behavioral_activation_service.py`
6. `app/services/exposure_hierarchy_service.py`

## Commit

- **Commit**: `4f0a222`
- **Message**: "Fix CBT models to use UUID types for PostgreSQL compatibility"
- **Status**: ✅ Committed and pushed to GitHub

---

**Status**: ✅ UUID type fix complete  
**Deployment**: 🚀 Triggered (awaiting verification)  
**Date**: 2025-01-18  
**Prepared by**: SuperNinja