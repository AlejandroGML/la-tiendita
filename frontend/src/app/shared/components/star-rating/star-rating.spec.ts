import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RatingModule } from 'primeng/rating';
import { StarRatingComponent } from './star-rating';

describe('StarRatingComponent', () => {
  let fixture: ComponentFixture<StarRatingComponent>;
  let component: StarRatingComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [StarRatingComponent],
      imports: [CommonModule, FormsModule, RatingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(StarRatingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // ── Defaults ─────────────────────────────────────────────────

  it('should default rating to 0', () => {
    expect(component.rating).toBe(0);
  });

  it('should default readonly to true', () => {
    expect(component.readonly).toBe(true);
  });

  // ── onRate ────────────────────────────────────────────────────

  it('should emit ratingChange when onRate is called', () => {
    const spy = vi.spyOn(component.ratingChange, 'emit');
    component.onRate({ value: 3 });
    expect(spy).toHaveBeenCalledWith(3);
  });

  it('should emit ratingChange with value 5', () => {
    const spy = vi.spyOn(component.ratingChange, 'emit');
    component.onRate({ value: 5 });
    expect(spy).toHaveBeenCalledWith(5);
  });

  // ── Template rendering ────────────────────────────────────────

  it('should render p-rating element', () => {
    const ratingEl = fixture.nativeElement.querySelector('p-rating');
    expect(ratingEl).toBeTruthy();
  });

  it('should set readonly binding on p-rating', () => {
    component.readonly = true;
    fixture.detectChanges();
    const ratingEl = fixture.nativeElement.querySelector('p-rating');
    expect(ratingEl.getAttribute('ng-reflect-readonly')).toBe('true');
  });
});
