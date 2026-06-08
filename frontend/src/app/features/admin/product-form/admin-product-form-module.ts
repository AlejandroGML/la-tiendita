import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { MessageService } from 'primeng/api';
import { SharedModule } from '../../../shared/shared-module';
import { AdminProductForm } from './admin-product-form';

@NgModule({
  declarations: [AdminProductForm],
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
