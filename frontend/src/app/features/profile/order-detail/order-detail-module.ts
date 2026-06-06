import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../../../shared/shared-module';
import { OrderDetailComponent } from './order-detail';

@NgModule({
  declarations: [OrderDetailComponent],
  imports: [
    CommonModule,
    SharedModule,
    RouterModule.forChild([
      { path: ':id', component: OrderDetailComponent },
    ]),
  ],
})
export class OrderDetailModule {}
