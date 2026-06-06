import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { PaginationComponent } from './pagination';

describe('PaginationComponent', () => {
  let fixture: ComponentFixture<PaginationComponent>;
  let component: PaginationComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [PaginationComponent],
      imports: [
        MatFormFieldModule,
        MatSelectModule,
        NoopAnimationsModule,
        TranslateModule.forRoot(),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(PaginationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should compute totalPages correctly', () => {
    component.total = 100;
    component.perPage = 12;
    expect(component.totalPages).toBe(9); // ceil(100/12) = 9
  });

  it('should return 1 page when total is 0', () => {
    component.total = 0;
    expect(component.totalPages).toBe(1);
  });

  it('should compute pages window with current page centered', () => {
    component.total = 200;
    component.perPage = 12;
    component.page = 10;
    // 200/12 = 17 pages, current=10, window 5 -> [8,9,10,11,12]
    expect(component.pages).toEqual([8, 9, 10, 11, 12]);
  });

  it('should clamp pages window near start', () => {
    component.total = 200;
    component.perPage = 12;
    component.page = 1;
    expect(component.pages).toEqual([1, 2, 3, 4, 5]);
  });

  it('should clamp pages window near end', () => {
    component.total = 200;
    component.perPage = 12;
    component.page = 17;
    expect(component.pages).toEqual([13, 14, 15, 16, 17]);
  });

  it('should show fewer pages when totalPages < 5', () => {
    component.total = 24;
    component.perPage = 12;
    component.page = 1;
    expect(component.pages).toEqual([1, 2]);
  });

  it('should emit pageChange on goTo', () => {
    const emitted: number[] = [];
    component.pageChange.subscribe((p) => emitted.push(p));

    component.total = 100;
    component.perPage = 12;
    component.page = 1;
    component.goTo(3);
    expect(emitted).toEqual([3]);
  });

  it('should not emit pageChange for invalid page', () => {
    const emitted: number[] = [];
    component.pageChange.subscribe((p) => emitted.push(p));

    component.total = 100;
    component.perPage = 12;
    component.goTo(999); // beyond totalPages
    expect(emitted.length).toBe(0);

    component.goTo(0); // before 1
    expect(emitted.length).toBe(0);
  });

  it('should not emit for same page', () => {
    const emitted: number[] = [];
    component.pageChange.subscribe((p) => emitted.push(p));

    component.total = 100;
    component.perPage = 12;
    component.page = 5;
    component.goTo(5);
    expect(emitted.length).toBe(0);
  });

  it('should emit perPageChange on selection change', () => {
    const emitted: number[] = [];
    component.perPageChange.subscribe((n) => emitted.push(n));

    component.onPerPageChange(24);
    expect(emitted).toEqual([24]);
  });

  it('should disable prev button on first page', () => {
    component.total = 100;
    component.perPage = 12;
    component.page = 1;
    expect(component.hasPrev).toBe(false);
    expect(component.hasNext).toBe(true);
  });

  it('should disable next button on last page', () => {
    component.total = 100;
    component.perPage = 12;
    component.page = 9; // last page
    expect(component.hasPrev).toBe(true);
    expect(component.hasNext).toBe(false);
  });
});
