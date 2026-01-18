# Phase 4: Psychology Expert CBT Implementation Plan

## Overview
Phase 4 will enhance the Psychology Expert mode with Cognitive Behavioral Therapy (CBT) techniques, providing therapeutic-level support without legal liability. This phase adds critical safety layers and evidence-based mental health tools.

---

## Phase 4.1: CBT Technique Library

### Database Models

#### 1. ThoughtRecord
- Tracks user's cognitive distortions and thought patterns
- Fields:
  - `situation` (TEXT): What happened
  - `automatic_thought` (TEXT): The initial thought
  - `emotion` (TEXT): How it made them feel
  - `emotion_intensity` (INT): 1-10 scale
  - `cognitive_distortion` (TEXT): Type of distortion (all-or-nothing, overgeneralization, etc.)
  - `challenging_thought` (TEXT): Balanced alternative thought
  - `outcome` (TEXT): Result after challenging
  - `created_at` (TIMESTAMP)

#### 2. BehavioralActivation
- Tracks activities and their impact on mood
- Fields:
  - `activity` (TEXT): Activity description
  - `mood_before` (INT): 1-10 scale before activity
  - `mood_after` (INT): 1-10 scale after activity
  - `difficulty_rating` (INT): 1-10 scale (avoidance level)
  - `completion_status` (ENUM): planned, completed, skipped
  - `notes` (TEXT): Optional notes
  - `created_at` (TIMESTAMP)

#### 3. ExposureHierarchy
- Tracks gradual exposure to feared situations
- Fields:
  - `feared_situation` (TEXT): What is feared
  - `difficulty_level` (INT): 1-100 scale
  - `anxiety_before` (INT): 1-10 scale
  - `anxiety_after` (INT): 1-10 scale
  - `completion_status` (ENUM): not_started, in_progress, completed, avoided
  - `notes` (TEXT): Optional notes
  - `created_at` (TIMESTAMP)

### Services to Implement

#### 1. CognitiveRestructuringService
- Identify cognitive distortions
- Generate challenging questions
- Suggest balanced thoughts
- Track progress over time

#### 2. ThoughtRecordService
- CRUD operations for thought records
- Analyze patterns in cognitive distortions
- Generate insights and trends
- Export thought records for review

#### 3. BehavioralActivationService
- Create activity schedule
- Track mood vs. activity patterns
- Break avoidance cycles
- Generate activity recommendations

#### 4. ExposureHierarchyService
- Build exposure hierarchy
- Rank situations by difficulty
- Track exposure progress
- Celebrate milestones

---

## Phase 4.2: Psychology Expert Mode Enhancement

### System Prompt Updates
Add CBT techniques to Psychology Expert mode prompts:
- Cognitive restructuring guidance
- Thought record creation guidance
- Behavioral activation principles
- Exposure hierarchy building
- Safety and crisis protocols

### Chat API Integration
- Detect when user is discussing mental health topics
- Offer to create thought records
- Suggest behavioral activation activities
- Guide through exposure exercises
- Track CBT progress

### New API Endpoints

#### Thought Records
- `POST /thought-records` - Create new thought record
- `GET /thought-records` - List user's thought records
- `GET /thought-records/{id}` - Get specific thought record
- `PUT /thought-records/{id}` - Update thought record
- `DELETE /thought-records/{id}` - Delete thought record
- `GET /thought-records/insights` - Get patterns and insights

#### Behavioral Activation
- `POST /behavioral-activation` - Create activity entry
- `GET /behavioral-activation` - List activities
- `GET /behavioral-activation/trends` - Get mood vs. activity trends
- `POST /behavioral-activation/schedule` - Create activity schedule

#### Exposure Hierarchy
- `POST /exposure-hierarchy` - Create exposure step
- `GET /exposure-hierarchy` - List hierarchy
- `PUT /exposure-hierarchy/{id}` - Update exposure step
- `GET /exposure-hierarchy/progress` - Get progress report

---

## Phase 4.3: Safety Layers

### High-Risk Keyword Detection
Keywords to detect:
- Suicide, self-harm, kill myself
- Depression, hopeless, worthless
- Abuse, trauma, violence

### Crisis Resource Responses
- National Suicide Prevention Lifeline: 1-800-273-8255
- Crisis Text Line: Text HOME to 741741
- 988 Suicide & Crisis Lifeline
- Professional help recommendations

### Safety Protocols
- Immediate disclaimer for Psychology Expert mode
- Automatic detection of high-risk topics
- Prioritize safety over techniques
- Encourage professional help
- Never diagnose or prescribe

---

## Phase 4.4: Testing & Deployment

### Test Suite
- Test thought record CRUD operations
- Test cognitive distortion detection
- Test behavioral activation tracking
- Test exposure hierarchy management
- Test high-risk keyword detection
- Test crisis resource responses

### Testing Checklist
- [ ] All CBT models create correctly
- [ ] Thought record insights generate correctly
- [ ] Behavioral activation trends accurate
- [ ] Exposure hierarchy builds correctly
- [ ] High-risk keywords trigger safety responses
- [ ] Crisis resources display correctly
- [ ] Psychology Expert mode uses CBT techniques
- [ ] Chat API integrates with CBT services
- [ ] No breaking changes to existing features

### Deployment Steps
1. Create database migration for CBT tables
2. Run migration on production
3. Commit and push changes
4. Monitor deployment logs
5. Test in production environment
6. Monitor for errors and issues

---

## Implementation Order

1. **Step 1**: Create database models (ThoughtRecord, BehavioralActivation, ExposureHierarchy)
2. **Step 2**: Create migration script for CBT tables
3. **Step 3**: Implement CBT services
4. **Step 4**: Create API schemas
5. **Step 5**: Create API endpoints
6. **Step 6**: Update Psychology Expert mode prompts
7. **Step 7**: Integrate CBT services into chat API
8. **Step 8**: Implement safety layers
9. **Step 9**: Create test suite
10. **Step 10**: Deploy and monitor

---

## Success Metrics

- Thought records created per user
- Behavioral activation entries per user
- Exposure hierarchy completion rate
- High-risk topic detection accuracy
- Crisis resource display rate
- User satisfaction with Psychology Expert mode
- CBT technique application rate

---

## Rollback Plan

If issues arise:
1. Disable CBT features in config: `CBT_ENABLED = False`
2. Comment out CBT endpoints in main.py
3. Revert commit: `git revert <commit-hash>`

---

## Notes

- All CBT features scoped to Psychology Expert mode only
- No CBT techniques used in other modes
- Safety layers always active, regardless of mode
- Professional help always recommended for serious issues
- Legal disclaimer prominent in Psychology Expert mode

---

**Prepared by**: SuperNinja  
**Based on**: ACCOUNTABILITY_LAYER_STRATEGY_V2.md  
**Date**: 2025-01-18  
**Phase**: 4.0