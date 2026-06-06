import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../../../shared/shared-module';
import { AdminPromotionsComponent } from './admin-promotions';

@NgModule({
  declarations: [AdminPromotionsComponent],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    SharedModule,
    RouterModule.forChild([{ path: '', component: AdminPromotionsComponent }]),
  ],
})
export class AdminPromotionsModule {}
