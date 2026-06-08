import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PaginatorModule } from 'primeng/paginator';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { PaginationComponent } from './pagination';

describe('PaginationComponent', () => {
  let fixture: ComponentFixture<PaginationComponent>;
  let component: PaginationComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [PaginationComponent],
      imports: [PaginatorModule, NoopAnimationsModule],
    }).compileComponents();

    fixture = TestBed.createComponent(PaginationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should compute first as 0 when page=1 perPage=12', () => {
    component.page = 1;
    component.perPage = 12;
    expect(component.first).toBe(0);
  });

  it('should compute first as (page-1) * perPage', () => {
    component.page = 3;
    component.perPage = 24;
    expect(component.first).toBe(48); // (3-1)*24
  });

  it('should emit pageChange when onPrimePageChange receives new page', () => {
    const emitted: number[] = [];
    component.pageChange.subscribe((p) => emitted.push(p));

    component.page = 1;
    component.onPrimePageChange({ page: 2, rows: 12, first: 24, pageCount: 10 });

    expect(emitted).toEqual([3]); // 0-based 2 → 1-based 3
  });

  it('should emit perPageChange when rows differ from current perPage', () => {
    const emitted: number[] = [];
    component.perPageChange.subscribe((n) => emitted.push(n));

    component.perPage = 12;
    component.onPrimePageChange({ page: 0, rows: 24, first: 0, pageCount: 5 });

    expect(emitted).toEqual([24]);
  });

  it('should not emit pageChange when page is unchanged', () => {
    const emitted: number[] = [];
    component.pageChange.subscribe((p) => emitted.push(p));

    component.page = 1;
    component.onPrimePageChange({ page: 0, rows: 12, first: 0, pageCount: 10 });

    expect(emitted.length).toBe(0);
  });

  it('should not emit perPageChange when rows are unchanged', () => {
    const emitted: number[] = [];
    component.perPageChange.subscribe((n) => emitted.push(n));

    component.perPage = 12;
    component.onPrimePageChange({ page: 1, rows: 12, first: 12, pageCount: 10 });

    expect(emitted.length).toBe(0);
  });

  it('should emit both pageChange and perPageChange when both change', () => {
    const pages: number[] = [];
    const rows: number[] = [];
    component.pageChange.subscribe((p) => pages.push(p));
    component.perPageChange.subscribe((n) => rows.push(n));

    component.page = 1;
    component.perPage = 12;
    component.onPrimePageChange({ page: 3, rows: 48, first: 144, pageCount: 3 });

    expect(pages).toEqual([4]); // 0-based 3 → 1-based 4
    expect(rows).toEqual([48]);
  });
});
