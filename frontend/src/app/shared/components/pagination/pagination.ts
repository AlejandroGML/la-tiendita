import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-pagination',
  templateUrl: './pagination.html',
  styleUrls: ['./pagination.scss'],
  standalone: false,
})
export class PaginationComponent {
  @Input() page = 1;
  @Input() perPage = 12;
  @Input() total = 0;

  @Output() pageChange = new EventEmitter<number>();
  @Output() perPageChange = new EventEmitter<number>();

  readonly perPageOptions = [12, 24, 48];

  get totalPages(): number {
    return Math.ceil(this.total / this.perPage) || 1;
  }

  get pages(): number[] {
    const total = this.totalPages;
    const current = this.page;
    const maxVisible = 5;
    const pages: number[] = [];

    let start = Math.max(1, current - Math.floor(maxVisible / 2));
    let end = Math.min(total, start + maxVisible - 1);
    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    return pages;
  }

  get hasPrev(): boolean {
    return this.page > 1;
  }

  get hasNext(): boolean {
    return this.page < this.totalPages;
  }

  goTo(p: number): void {
    if (p >= 1 && p <= this.totalPages && p !== this.page) {
      this.pageChange.emit(p);
    }
  }

  onPerPageChange(value: number): void {
    this.perPageChange.emit(value);
  }
}
