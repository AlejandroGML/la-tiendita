import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../../../shared/shared-module';
import { AdminOrders } from './admin-orders';

@NgModule({
  declarations: [AdminOrders],
  imports: [
    CommonModule,
    SharedModule,
    RouterModule.forChild([{ path: '', component: AdminOrders }]),
  ],
})
export class AdminOrdersModule {}
