import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../../shared/shared-module';
import { Sale } from './sale';

@NgModule({
  declarations: [Sale],
  imports: [
    CommonModule,
    SharedModule,
    RouterModule.forChild([
      { path: '', component: Sale },
    ]),
  ],
})
export class SaleModule {}
