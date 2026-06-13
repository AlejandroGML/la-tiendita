import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MessageService } from 'primeng/api';
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
  providers: [MessageService],
})
export class OrderDetailModule {}
