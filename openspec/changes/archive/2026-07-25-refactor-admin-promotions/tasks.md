# Tasks: Refactor AdminPromotionsComponent

## Phase 1: Extract Components (3 tasks)

### Task 1.1: Create PromotionFormComponent
**File**: `frontend/src/app/features/admin/promotions/promotion-form/promotion-form.component.ts`
**Description**: Extract form logic from AdminPromotionsComponent into new PromotionFormComponent. Include FormGroup building, validation, translation FormArray, date conversion helpers, and submit/cancel methods. Add @Input for promotion (null=create mode) and saving state. Add @Output for saved and cancelled events.
**Acceptance Criteria**:
- PromotionFormComponent compiles without errors
- Form validation works (code required, discount 1-100, dates)
- Translation FormArray supports 3 languages (ES, EN, SV)
- Submit emits `saved` event with payload
- Cancel emits `cancelled` event

### Task 1.2: Create PromotionListComponent
**File**: `frontend/src/app/features/admin/promotions/promotion-list/promotion-list.component.ts`
**Description**: Extract table rendering and status logic from AdminPromotionsComponent into new PromotionListComponent. Include table template, status badge computation (`isActive`), usage display (`getUsageInfo`), and action buttons (edit, delete). Add @Input for promotions, loading, error. Add @Output for edit, delete, retry events.
**Acceptance Criteria**:
- PromotionListComponent renders table with all columns
- Status badges show active/inactive correctly
- Usage info displays (e.g., "5 / 10" or "5 / ∞")
- Edit button emits `edit` event with promotion
- Delete button emits `delete` event with promotion
- Retry button emits `retry` event on error state

### Task 1.3: Create component templates and styles
**Files**: 
- `promotion-form/promotion-form.component.html`
- `promotion-form/promotion-form.component.scss`
- `promotion-list/promotion-list.component.html`
- `promotion-list/promotion-list.component.scss`
**Description**: Extract HTML templates and SCSS styles from admin-promotions.html and admin-promotions.scss into the two new components. Move form-related markup to promotion-form, table-related markup to promotion-list. Preserve all PrimeNG components, data-testid attributes, and Tailwind classes.
**Acceptance Criteria**:
- Form template includes all fields (code, discount, product, dates, active, translations)
- List template includes table with all columns and action buttons
- All data-testid attributes preserved
- Styles compile without errors

## Phase 2: Wire Up Orchestrator (2 tasks)

### Task 2.1: Refactor AdminPromotionsComponent to orchestrator
**File**: `frontend/src/app/features/admin/promotions/admin-promotions.ts`
**Description**: Reduce AdminPromotionsComponent to ~50 lines. Remove form logic, table rendering, and status computation. Keep data loading (`loadPromotions`), form visibility toggle (`openCreateForm`, `openEditForm`, `cancelForm`), and delete confirmation (`deletePromotion`). Add child component selectors to template. Pass inputs and listen to outputs.
**Acceptance Criteria**:
- AdminPromotionsComponent < 60 lines
- Child components render correctly
- Form visibility toggle works
- Data loading works
- Delete confirmation works

### Task 2.2: Update admin-promotions.html template
**File**: `frontend/src/app/features/admin/promotions/admin-promotions.html`
**Description**: Replace monolithic template with orchestrator template. Keep header with "New Promotion" button and toast container. Conditionally render PromotionFormComponent when `showForm()=true`. Conditionally render PromotionListComponent when `showForm()=false`. Bind inputs and outputs to parent methods.
**Acceptance Criteria**:
- Header renders with "New Promotion" button
- PromotionFormComponent shows when creating/editing
- PromotionListComponent shows when listing
- Form outputs trigger parent methods
- List outputs trigger parent methods

## Phase 3: Clean Up and Test (3 tasks)

### Task 3.1: Update admin-promotions-module.ts
**File**: `frontend/src/app/features/admin/promotions/admin-promotions-module.ts`
**Description**: Add PromotionFormComponent and PromotionListComponent to declarations and exports. Import PrimeNG modules used by child components (Forms, InputText, InputNumber, FloatLabel, DatePicker, ToggleSwitch, Select, Button, Table, ProgressBar, Toast).
**Acceptance Criteria**:
- Module compiles without errors
- All child components declared
- All PrimeNG modules imported

### Task 3.2: Split and update tests
**Files**:
- `admin-promotions.spec.ts` (orchestrator tests)
- `promotion-form/promotion-form.component.spec.ts` (form tests)
- `promotion-list/promotion-list.component.spec.ts` (list tests)
**Description**: Split existing test suite into three focused test files. AdminPromotionsComponent tests: data loading, visibility toggle, delete confirmation. PromotionFormComponent tests: form validation, submission, translation array. PromotionListComponent tests: table rendering, status badges, event emissions. Preserve all existing test scenarios.
**Acceptance Criteria**:
- All existing tests pass
- Test coverage maintained
- Each component has focused tests

### Task 3.3: Delete old monolithic code
**Files**: Remove extracted methods and template sections from admin-promotions.ts and admin-promotions.html
**Description**: Remove all form-building logic, table rendering, and status computation from AdminPromotionsComponent. Verify component is now a thin orchestrator. Run full test suite to confirm no regressions.
**Acceptance Criteria**:
- AdminPromotionsComponent < 60 lines
- No dead code remains
- All tests pass
- No functional regression

## Task Summary
- **Phase 1**: 3 tasks (extract components)
- **Phase 2**: 2 tasks (wire up orchestrator)
- **Phase 3**: 3 tasks (clean up and test)
- **Total**: 8 tasks
