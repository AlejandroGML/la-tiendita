import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { MessageService } from 'primeng/api';
import { SharedModule } from '../../../shared/shared-module';
import { AdminPromotionsComponent } from './admin-promotions';
import { PromotionFormComponent } from './components/promotion-form.component';
import { PromotionListComponent } from './components/promotion-list.component';

@NgModule({
  declarations: [
    AdminPromotionsComponent,
    PromotionFormComponent,
    PromotionListComponent,
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    SharedModule,
    RouterModule.forChild([{ path: '', component: AdminPromotionsComponent }]),
  ],
  providers: [MessageService],
})
export class AdminPromotionsModule {}
