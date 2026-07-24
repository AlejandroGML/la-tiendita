import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { MessageService } from 'primeng/api';
import { SharedModule } from '../../../shared/shared-module';
import { authGuard } from '../../../core/guards/auth.guard';
import { ProfileView } from './profile-view';

@NgModule({
  declarations: [ProfileView],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    ButtonModule,
    SharedModule,
    RouterModule.forChild([
      { path: '', component: ProfileView, canActivate: [authGuard] },
    ]),
  ],
  providers: [MessageService],
})
export class ProfileViewModule {}
