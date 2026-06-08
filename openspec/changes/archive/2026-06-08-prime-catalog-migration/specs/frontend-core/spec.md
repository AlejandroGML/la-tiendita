# Delta for frontend-core

## MODIFIED Requirements

### Requirement: R2 — Angular Material Integration

The system MUST install `@angular/material@22` and configure one prebuilt theme (`indigo-pink`). A `SharedModule` SHALL re-export commonly used Material modules (`MatButtonModule`, `MatToolbarModule`, `MatIconModule`, `MatGridListModule`, `MatChipsModule`, `MatSliderModule`, `MatTabsModule`) and SHALL import `PrimeNgModule` for coexistence. Material and PrimeNG SHALL coexist without conflicts; no Material modules are removed. Phase 2 PrimeNgModule expansion (7 added modules: SelectModule, InputTextModule, InputNumberModule, IconFieldModule, InputIconModule, PaginatorModule, ProgressBarModule) is transparent to SharedModule — no import changes required.

(Previously: SharedModule only exported Material modules; no PrimeNG coexistence. Phase 1 added 3 PrimeNG modules through SharedModule re-export.)

#### Scenario: Material button renders correctly

- GIVEN `SharedModule` is imported in the target component's module
- WHEN `<button mat-raised-button color="primary">Click</button>` is used in a template
- THEN the button renders with Material Design styling and ripple effect

#### Scenario: New Material modules render correctly

- GIVEN `SharedModule` exports `MatGridListModule`, `MatChipsModule`, `MatSliderModule`, `MatTabsModule`
- WHEN these components are used in product catalog templates
- THEN grid lists, chips, sliders, and tabs render with Material Design styling

#### Scenario: Material and PrimeNG coexist in SharedModule

- GIVEN `SharedModule` imports and re-exports `PrimeNgModule`
- WHEN `ng build` compiles the application
- THEN Material components still render identically
- AND no CSS or template conflicts occur between the two libraries
- AND Phase 2 PrimeNG components are available in addition to Phase 1 components
