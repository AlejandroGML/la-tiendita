import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { MessageService } from 'primeng/api';
import { SharedModule } from '../../../shared/shared-module';
import { AdminProductForm } from './admin-product-form';
import { ImageUploadComponent } from './components/image-upload.component';
import { ProductBasicInfoComponent } from './components/product-basic-info.component';
import { ProductTranslationsComponent } from './components/product-translations.component';
import { ProductVariantsComponent } from './components/product-variants.component';

@NgModule({
  declarations: [
    AdminProductForm,
    ImageUploadComponent,
    ProductBasicInfoComponent,
    ProductTranslationsComponent,
    ProductVariantsComponent,
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    SharedModule,
    RouterModule.forChild([
      { path: '', component: AdminProductForm },
    ]),
  ],
  providers: [MessageService],
})
export class AdminProductFormModule {}
