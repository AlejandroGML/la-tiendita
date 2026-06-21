# Delta Spec: promotions (Modified)

## Change Summary
Refactor AdminPromotionsComponent from monolithic god node into three focused components: orchestrator, form, and list. No behavior change — structural improvement only.

## Modified Requirements

### R1: Admin CRUD Promotions (Frontend Component Structure)

**Current State**: Single AdminPromotionsComponent (225 lines) handles form building, validation, submission, table rendering, status computation, and delete confirmation.

**New State**: Three-component hierarchy:
- **AdminPromotionsComponent** (orchestrator, ~50 lines): manages data loading, form visibility toggle, and child component coordination
- **PromotionFormComponent** (~120 lines): owns FormGroup, validation, translation FormArray, submit/cancel events, date conversion helpers
- **PromotionListComponent** (~100 lines): owns table rendering, status computation (`isActive`), usage display, edit/delete row actions

#### Scenario: Create promotion (refactored)
- GIVEN admin clicks "New Promotion"
- WHEN AdminPromotionsComponent sets `showForm=true`
- THEN PromotionFormComponent renders with empty form
- AND on submit, emits `(saved)` event to parent
- AND parent reloads promotions list

#### Scenario: Edit promotion (refactored)
- GIVEN admin clicks edit on a promotion row
- WHEN PromotionListComponent emits `(edit)="promotion"`
- THEN AdminPromotionsComponent passes promotion to PromotionFormComponent via `[promotion]` input
- AND form populates with existing data

#### Scenario: Delete promotion (refactored)
- GIVEN admin clicks delete on a promotion row
- WHEN PromotionListComponent emits `(delete)="promotion"`
- THEN AdminPromotionsComponent handles confirmation dialog and API call
- AND reloads list on success

#### Scenario: Status computation (refactored)
- GIVEN promotion with date range and usage count
- WHEN PromotionListComponent renders status column
- THEN `isActive()` method lives in PromotionListComponent (not parent)
- AND returns boolean based on is_active, date range, and max_uses

## Interface Contract

### PromotionFormComponent
```typescript
@Input() promotion: Promotion | null;  // null = create mode
@Input() saving: boolean;
@Output() saved = new EventEmitter<void>();
@Output() cancelled = new EventEmitter<void>();
```

### PromotionListComponent
```typescript
@Input() promotions: Promotion[];
@Input() loading: boolean;
@Output() edit = new EventEmitter<Promotion>();
@Output() delete = new EventEmitter<Promotion>();
@Output() retry = new EventEmitter<void>();
```

## Testing Impact
- Existing test scenarios remain valid
- Tests split across 3 spec files
- PromotionFormComponent tests: form validation, submission, translation array
- PromotionListComponent tests: table rendering, status badges, action emissions
- AdminPromotionsComponent tests: data loading, visibility toggle, child coordination
