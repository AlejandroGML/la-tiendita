import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { CheckboxModule } from 'primeng/checkbox';
import { SharedModule } from '../../shared/shared-module';
import { Login } from './login/login';
import { Register } from './register/register';
import { GoogleCallback } from './google-callback/google-callback';

@NgModule({
  declarations: [Login, Register, GoogleCallback],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    SharedModule,
    RouterModule.forChild([
      { path: 'login', component: Login },
      { path: 'register', component: Register },
      { path: 'google/callback', component: GoogleCallback },
    ]),
  ],
})
export class AuthModule {}
