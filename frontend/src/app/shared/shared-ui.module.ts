import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';

// PrimeNG modules needed by UI components
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { DialogModule } from 'primeng/dialog';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { InputTextModule } from 'primeng/inputtext';
import { PaginatorModule } from 'primeng/paginator';
import { RatingModule } from 'primeng/rating';

// Components
import { ProductCardComponent } from './components/product-card/product-card';
import { SearchBarComponent } from './components/search-bar/search-bar';
import { PaginationComponent } from './components/pagination/pagination';
import { StarRatingComponent } from './components/star-rating/star-rating';
import { SizingGuideComponent } from './components/sizing-guide/sizing-guide';

const UI_COMPONENTS = [
  ProductCardComponent,
  SearchBarComponent,
  PaginationComponent,
  StarRatingComponent,
  SizingGuideComponent,
];

const PRIME_NG_UI = [
  ButtonModule,
  CardModule,
  DialogModule,
  IconFieldModule,
  InputIconModule,
  InputTextModule,
  PaginatorModule,
  RatingModule,
];

@NgModule({
  declarations: UI_COMPONENTS,
  imports: [CommonModule, FormsModule, ...PRIME_NG_UI, TranslateModule],
  exports: UI_COMPONENTS,
})
export class SharedUiModule {}
