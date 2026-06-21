# Design: Refactor AdminPromotionsComponent

## Architecture Overview

```
AdminPromotionsComponent (Orchestrator)
├── PromotionListComponent (Presentation)
└── PromotionFormComponent (Form State)
```

## Component Responsibilities

### AdminPromotionsComponent (Orchestrator)
**Lines**: ~50
**State**: `promotions`, `loading`, `error`, `showForm`, `editingId`
**Methods**: `loadPromotions()`, `openCreateForm()`, `openEditForm()`, `cancelForm()`, `deletePromotion()`
**Template**: Header with "New" button, conditional rendering of child components, toast container

### PromotionFormComponent (Form State)
**Lines**: ~120
**Inputs**: `promotion: Promotion | null`, `saving: boolean`
**Outputs**: `saved: EventEmitter<void>`, `cancelled: EventEmitter<void>`
**State**: `form: FormGroup`, internal `translationsArray: FormArray`
**Methods**: `buildForm()`, `createTranslationGroup()`, `submitForm()`, `cancelForm()`, `toDate()`, `fromDate()`
**Template**: Complete form UI (code, discount, product, dates, active toggle, translations, actions)

### PromotionListComponent (Presentation)
**Lines**: ~100
**Inputs**: `promotions: Promotion[]`, `loading: boolean`, `error: boolean`
**Outputs**: `edit: EventEmitter<Promotion>`, `delete: EventEmitter<Promotion>`, `retry: EventEmitter<void>`
**Methods**: `isActive()`, `getUsageInfo()`
**Template**: Progress bar, error state, empty state, table with status badges and action buttons

## Data Flow

### Create Flow
1. User clicks "New Promotion" → AdminPromotionsComponent sets `showForm=true`, `editingId=null`
2. PromotionFormComponent receives `promotion=null`, builds empty form
3. User submits → PromotionFormComponent emits `saved`
4. AdminPromotionsComponent calls API, reloads list, sets `showForm=false`

### Edit Flow
1. User clicks edit → PromotionListComponent emits `edit(promotion)`
2. AdminPromotionsComponent sets `editingId=promotion.id`, `showForm=true`
3. PromotionFormComponent receives `promotion`, populates form
4. User submits → same as create flow

### Delete Flow
1. User clicks delete → PromotionListComponent emits `delete(promotion)`
2. AdminPromotionsComponent shows confirmation dialog
3. On confirm, calls API, reloads list

## State Management
- **Parent owns**: data fetching, form visibility, editing context
- **Form owns**: FormGroup state, validation, submission
- **List owns**: presentation logic (status computation, usage formatting)

## Testing Strategy
- **AdminPromotionsComponent**: test data loading, visibility toggle, API calls
- **PromotionFormComponent**: test form validation, submission payload, translation array
- **PromotionListComponent**: test table rendering, status badges, event emissions

## Migration Path
1. Create PromotionFormComponent with form logic extracted
2. Create PromotionListComponent with table logic extracted
3. Update AdminPromotionsComponent to use child components
4. Delete old monolithic code
5. Update tests

## Rollback
If issues arise, revert to monolithic component. No data migration needed — pure frontend refactor.
