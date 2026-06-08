import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../shared/shared-module';
import { Header } from './header/header';
import { Footer } from './footer/footer';

@NgModule({
  declarations: [Header, Footer],
  imports: [CommonModule, SharedModule, RouterModule],
  exports: [Header, Footer],
})
export class LayoutModule {}
