import { NgModule } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatSliderModule } from '@angular/material/slider';
import { MatToolbarModule } from '@angular/material/toolbar';
import { TranslateModule } from '@ngx-translate/core';

import { CurrencyPipe } from './pipes/currency.pipe';
import { ProductCardComponent } from './components/product-card/product-card';
import { SearchBarComponent } from './components/search-bar/search-bar';
import { PaginationComponent } from './components/pagination/pagination';

const MATERIAL_MODULES = [
  MatButtonModule,
  MatCardModule,
  MatChipsModule,
  MatFormFieldModule,
  MatGridListModule,
  MatIconModule,
  MatInputModule,
  MatListModule,
  MatProgressSpinnerModule,
  MatSelectModule,
  MatSidenavModule,
  MatSliderModule,
  MatToolbarModule,
];

const SHARED_COMPONENTS = [
  CurrencyPipe,
  ProductCardComponent,
  SearchBarComponent,
  PaginationComponent,
];

@NgModule({
  declarations: SHARED_COMPONENTS,
  imports: [...MATERIAL_MODULES, TranslateModule],
  exports: [...MATERIAL_MODULES, TranslateModule, ...SHARED_COMPONENTS],
})
export class SharedModule {}
