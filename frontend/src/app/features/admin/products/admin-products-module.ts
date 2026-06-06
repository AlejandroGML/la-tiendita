import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../../../shared/shared-module';
import { AdminProducts } from './admin-products';

@NgModule({
  declarations: [AdminProducts],
  imports: [
    CommonModule,
    SharedModule,
    RouterModule.forChild([{ path: '', component: AdminProducts }]),
  ],
})
export class AdminProductsModule {}
