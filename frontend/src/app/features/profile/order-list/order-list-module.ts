import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../../../shared/shared-module';
import { OrderListComponent } from './order-list';

@NgModule({
  declarations: [OrderListComponent],
  imports: [
    CommonModule,
    SharedModule,
    RouterModule.forChild([{ path: '', component: OrderListComponent }]),
  ],
})
export class OrderListModule {}
