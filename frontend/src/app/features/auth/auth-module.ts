import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { CheckboxModule } from 'primeng/checkbox';
import { SharedModule } from '../../shared/shared-module';
import { Login } from './login/login';
import { Register } from './register/register';

@NgModule({
  declarations: [Login, Register],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    SharedModule,
    RouterModule.forChild([
      { path: 'login', component: Login },
      { path: 'register', component: Register },
    ]),
  ],
})
export class AuthModule {}
