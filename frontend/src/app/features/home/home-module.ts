import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Home } from './home';

@NgModule({
  declarations: [Home],
  imports: [
    CommonModule,
    RouterModule.forChild([{ path: '', component: Home }]),
  ],
})
export class HomeModule {}
