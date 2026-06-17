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

// Pipes used by sub-components
import { SharedPipesModule } from './shared-pipes.module';

// Components
import { ProductCardComponent } from './components/product-card/product-card';
import { ProductConditionBadgeComponent } from './components/product-card/condition-badge.component';
import { ProductColorSwatchesComponent } from './components/product-card/color-swatches.component';
import { ProductRatingComponent } from './components/product-card/product-rating.component';
import { ProductPriceComponent } from './components/product-card/product-price.component';
import { SearchBarComponent } from './components/search-bar/search-bar';
import { PaginationComponent } from './components/pagination/pagination';
import { StarRatingComponent } from './components/star-rating/star-rating';
import { SizingGuideComponent } from './components/sizing-guide/sizing-guide';

const UI_COMPONENTS = [
  ProductCardComponent,
  ProductConditionBadgeComponent,
  ProductColorSwatchesComponent,
  ProductRatingComponent,
  ProductPriceComponent,
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
  imports: [CommonModule, FormsModule, ...PRIME_NG_UI, TranslateModule, SharedPipesModule],
  exports: UI_COMPONENTS,
})
export class SharedUiModule {}
