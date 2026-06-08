import { Component, EventEmitter, Input, Output } from '@angular/core';
import type { PaginatorState } from 'primeng/paginator';

@Component({
  selector: 'app-pagination',
  templateUrl: './pagination.html',
  standalone: false,
})
export class PaginationComponent {
  @Input() page = 1;
  @Input() perPage = 12;
  @Input() total = 0;

  @Output() pageChange = new EventEmitter<number>();
  @Output() perPageChange = new EventEmitter<number>();

  readonly perPageOptions = [12, 24, 48];

  get first(): number {
    return (this.page - 1) * this.perPage;
  }

  onPrimePageChange(event: PaginatorState): void {
    if (event.rows != null && event.rows !== this.perPage) {
      this.perPageChange.emit(event.rows);
    }
    if (event.page != null) {
      const newPage = event.page + 1; // 0-based → 1-based
      if (newPage !== this.page) {
        this.pageChange.emit(newPage);
      }
    }
  }
}
