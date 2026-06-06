import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../../shared/shared-module';
import { AdminLayoutComponent } from './admin-layout';

@NgModule({
  declarations: [AdminLayoutComponent],
  imports: [CommonModule, RouterModule, SharedModule],
  exports: [AdminLayoutComponent],
})
export class AdminLayoutModule {}
