import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../../../shared/shared-module';
import { AdminCategories } from './admin-categories';

@NgModule({
  declarations: [AdminCategories],
  imports: [
    CommonModule,
    SharedModule,
    RouterModule.forChild([{ path: '', component: AdminCategories }]),
  ],
})
export class AdminCategoriesModule {}
