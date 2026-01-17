# Field Name Fixes Needed

## GoalService ✅
- [x] Line 342: `goal.check_in_frequency` → Remove (doesn't exist in model)
- [x] Line 361: `goal.streak_days` → `goal.current_streak_days`
- [x] Line 366-367: `goal.target_date` → `goal.time_bound_deadline`
- [x] Line 505: `goal.streak_days = 0` → `goal.current_streak_days = 0`
- [x] Line 509: `goal.check_in_frequency` → Remove
- [x] Line 523: `goal.streak_days = streak` → `goal.current_streak_days = streak`
- [x] Line 536: `goal.check_in_frequency` → Remove

## HabitService ✅
- [x] `is_active` → `status` (correctly mapped in get_user_habits)
- [x] `target_days` → `custom_days` (correctly mapped in create_habit)

## CheckInService ✅
- [x] `progress_notes` → `notes` (correctly mapped in create_check_in)

## API Schemas ✅
- [x] GoalCreate schema (fixed field names)
- [x] GoalUpdate schema (fixed field names)
- [x] GoalResponse schema (fixed field names)
- [x] CheckInCreate schema (notes instead of progress_notes)
- [x] create_goal endpoint (fixed parameter names)
- [x] create_check_in endpoint (notes instead of progress_notes)