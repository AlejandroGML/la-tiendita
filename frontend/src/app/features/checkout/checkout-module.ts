import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ReactiveFormsModule } from '@angular/forms';
import { SharedModule } from '../../shared/shared-module';
import { CheckoutComponent } from './checkout';

@NgModule({
  declarations: [CheckoutComponent],
  imports: [
    CommonModule,
    SharedModule,
    ReactiveFormsModule,
    RouterModule.forChild([{ path: '', component: CheckoutComponent }]),
  ],
})
export class CheckoutModule {}
