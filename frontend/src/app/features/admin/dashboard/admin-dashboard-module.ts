import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../../../shared/shared-module';
import { AdminDashboard } from './admin-dashboard';

@NgModule({
  declarations: [AdminDashboard],
  imports: [
    CommonModule,
    SharedModule,
    RouterModule.forChild([{ path: '', component: AdminDashboard }]),
  ],
})
export class AdminDashboardModule {}
