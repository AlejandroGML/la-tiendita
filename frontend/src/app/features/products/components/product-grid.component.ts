import { Component, Input, Output, EventEmitter } from '@angular/core';
import type { Product } from '../../../shared/models/product.model';

@Component({
  selector: 'app-product-grid',
  templateUrl: './product-grid.component.html',
  styleUrls: ['./product-grid.component.scss'],
  standalone: false,
})
export class ProductGridComponent {
  @Input({ required: true }) products!: Product[];
  @Input({ required: true }) loading!: boolean;
  @Input() error: string | null = null;

  @Output() retry = new EventEmitter<void>();

  onRetry(): void {
    this.retry.emit();
  }
}
