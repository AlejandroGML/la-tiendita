import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../../../shared/shared-module';
import { authGuard } from '../../../core/guards/auth.guard';
import { WishlistComponent } from './wishlist';

@NgModule({
  declarations: [WishlistComponent],
  imports: [
    CommonModule,
    SharedModule,
    RouterModule.forChild([
      { path: '', component: WishlistComponent, canActivate: [authGuard] },
    ]),
  ],
})
export class WishlistModule {}
