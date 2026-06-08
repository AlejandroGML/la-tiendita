import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../../shared/shared-module';
import { Home } from './home';

@NgModule({
  declarations: [Home],
  imports: [
    CommonModule,
    SharedModule,
    RouterModule.forChild([{ path: '', component: Home }]),
  ],
})
export class HomeModule {}
