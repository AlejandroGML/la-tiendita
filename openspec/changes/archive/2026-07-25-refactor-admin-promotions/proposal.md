# Proposal: Refactor AdminPromotionsComponent

## Intent
AdminPromotionsComponent is a god node (19 edges) handling promotions CRUD, form validation, date pickers, translations, and status logic in a single 225-line class. This violates SRP and makes testing difficult. Split into focused components to improve maintainability and testability.

## Scope

### In Scope
- Extract PromotionFormComponent (form logic, validation, translations)
- Extract PromotionListComponent (table, status badges, actions)
- Reduce AdminPromotionsComponent to orchestrator (~50 lines)
- Preserve all existing functionality and test coverage

### Out of Scope
- Backend API changes
- Public promotions listing
- New promotion features

## Capabilities

### Modified Capabilities
- `promotions`: Refactor admin component structure (no behavior change)

## Approach
Extract two child components: PromotionFormComponent handles form state and submission, PromotionListComponent handles table rendering and row actions. Parent orchestrates visibility and data flow via Input/Output.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/app/features/admin/promotions/` | Modified | Split into 3 components |
| `admin-promotions.spec.ts` | Modified | Update tests for new structure |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Form state sync issues | Medium | Use reactive forms with @Input/@Output |
| Test coverage gaps | Low | Maintain existing test scenarios |

## Rollback Plan
Revert to monolithic component if child components introduce bugs. No data migration needed.

## Dependencies
None

## Success Criteria
- [ ] AdminPromotionsComponent < 60 lines
- [ ] PromotionFormComponent handles all form logic
- [ ] PromotionListComponent renders table with actions
- [ ] All existing tests pass
- [ ] No functional regression
