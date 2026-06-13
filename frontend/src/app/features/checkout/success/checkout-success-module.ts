import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../../../shared/shared-module';
import { CheckoutSuccessComponent } from './checkout-success';

@NgModule({
  declarations: [CheckoutSuccessComponent],
  imports: [
    CommonModule,
    SharedModule,
    RouterModule.forChild([
      { path: '', component: CheckoutSuccessComponent },
    ]),
  ],
})
export class CheckoutSuccessModule {}
