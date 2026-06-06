import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../../../shared/shared-module';
import { AdminUsers } from './admin-users';

@NgModule({
  declarations: [AdminUsers],
  imports: [
    CommonModule,
    SharedModule,
    RouterModule.forChild([{ path: '', component: AdminUsers }]),
  ],
})
export class AdminUsersModule {}
