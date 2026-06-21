import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../../shared/shared-module';
import { ProductList } from './product-list';
import { ProductFilterSidebarComponent } from './components/product-filter-sidebar.component';
import { ProductGridComponent } from './components/product-grid.component';

@NgModule({
  declarations: [ProductList, ProductFilterSidebarComponent, ProductGridComponent],
  imports: [
    CommonModule,
    SharedModule,
    RouterModule.forChild([{ path: '', component: ProductList }]),
  ],
})
export class ProductListModule {}
