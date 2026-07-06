import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../../shared/shared-module';
import { ImageZoomDirective } from '../../shared/directives/image-zoom.directive';
import { ShareButtonComponent } from '../../shared/components/share-button/share-button';
import { ProductDetail } from './product-detail';
import { ProductDetailGalleryComponent } from './components/gallery.component';
import { ProductDetailAttributesComponent } from './components/attributes.component';
import { ProductDetailReviewsComponent } from './components/reviews.component';

@NgModule({
  declarations: [
    ProductDetail,
    ProductDetailGalleryComponent,
    ProductDetailAttributesComponent,
    ProductDetailReviewsComponent,
  ],
  imports: [
    CommonModule,
    SharedModule,
    ImageZoomDirective,
    ShareButtonComponent,
    RouterModule.forChild([
      { path: '', component: ProductDetail },
    ]),
  ],
})
export class ProductDetailModule {}
