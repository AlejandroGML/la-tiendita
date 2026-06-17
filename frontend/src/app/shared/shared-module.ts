import { NgModule } from '@angular/core';

import { SharedUiModule } from './shared-ui.module';
import { SharedPipesModule } from './shared-pipes.module';
import { SharedFormsModule } from './shared-forms.module';
import { HoverDelayDirective } from './directives/hover-delay.directive';

// Legacy imports kept for backwards compatibility
import { PrimeNgModule } from './primeng-module';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSliderModule } from '@angular/material/slider';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSortModule } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';
import { MatTabsModule } from '@angular/material/tabs';
import { MatToolbarModule } from '@angular/material/toolbar';
import { TranslateModule } from '@ngx-translate/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

const MATERIAL_MODULES = [
  MatButtonModule,
  MatCardModule,
  MatChipsModule,
  MatFormFieldModule,
  MatGridListModule,
  MatIconModule,
  MatInputModule,
  MatListModule,
  MatMenuModule,
  MatPaginatorModule,
  MatProgressBarModule,
  MatProgressSpinnerModule,
  MatSelectModule,
  MatSidenavModule,
  MatSlideToggleModule,
  MatSliderModule,
  MatSnackBarModule,
  MatSortModule,
  MatTableModule,
  MatTabsModule,
  MatToolbarModule,
];

@NgModule({
  declarations: [HoverDelayDirective],
  imports: [
    CommonModule,
    SharedUiModule,
    SharedPipesModule,
    SharedFormsModule,
    PrimeNgModule,
    ...MATERIAL_MODULES,
    TranslateModule,
    FormsModule,
  ],
  exports: [
    SharedUiModule,
    SharedPipesModule,
    SharedFormsModule,
    PrimeNgModule,
    HoverDelayDirective,
    ...MATERIAL_MODULES,
    TranslateModule,
    CommonModule,
    FormsModule,
  ],
})
export class SharedModule {}
