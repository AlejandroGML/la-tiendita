import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CommonModule } from '@angular/common';
import { StarRatingComponent } from './star-rating';

describe('StarRatingComponent', () => {
  let fixture: ComponentFixture<StarRatingComponent>;
  let component: StarRatingComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [StarRatingComponent],
      imports: [CommonModule],
    }).compileComponents();

    fixture = TestBed.createComponent(StarRatingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // ── Component Logic (pure methods) ───────────────────────────

  describe('starFill', () => {
    it('should return full when rating >= star index', () => {
      component.rating = 4;
      expect(component.starFill(1)).toBe('full');
      expect(component.starFill(4)).toBe('full');
    });

    it('should return empty when rating < star index - 1', () => {
      component.rating = 2;
      expect(component.starFill(4)).toBe('empty');
      expect(component.starFill(5)).toBe('empty');
    });

    it('should return half when rating is fractional between star indexes', () => {
      component.rating = 2.5;
      expect(component.starFill(1)).toBe('full');
      expect(component.starFill(2)).toBe('full');
      expect(component.starFill(3)).toBe('half');
      expect(component.starFill(4)).toBe('empty');
    });

    it('should handle rating=0 (all empty)', () => {
      component.rating = 0;
      expect(component.starFill(1)).toBe('empty');
      expect(component.starFill(5)).toBe('empty');
    });

    it('should handle rating=5 (all full)', () => {
      component.rating = 5;
      expect(component.starFill(1)).toBe('full');
      expect(component.starFill(5)).toBe('full');
    });
  });

  describe('starIcon', () => {
    it('should return star for full', () => {
      component.rating = 5;
      expect(component.starIcon(1)).toBe('star');
    });

    it('should return star_half for half', () => {
      component.rating = 0.5;
      expect(component.starIcon(1)).toBe('star_half');
    });

    it('should return star_border for empty', () => {
      component.rating = 0;
      expect(component.starIcon(1)).toBe('star_border');
    });
  });

  describe('stars getter', () => {
    it('should return array of 1-5', () => {
      expect(component.stars).toEqual([1, 2, 3, 4, 5]);
    });

    it('should always have length 5', () => {
      expect(component.stars.length).toBe(5);
    });
  });

  // ── Interactive behavior ─────────────────────────────────────

  describe('handleClick', () => {
    it('should update rating and emit on click when not readonly', () => {
      component.readonly = false;
      const spy = vi.spyOn(component.ratingChange, 'emit');
      component.handleClick(3);
      expect(component.rating).toBe(3);
      expect(spy).toHaveBeenCalledWith(3);
    });

    it('should not update rating or emit when readonly', () => {
      component.readonly = true;
      component.rating = 2;
      const spy = vi.spyOn(component.ratingChange, 'emit');
      component.handleClick(5);
      expect(component.rating).toBe(2); // unchanged
      expect(spy).not.toHaveBeenCalled();
    });
  });

  describe('handleKeydown', () => {
    it('should handle Enter key when not readonly', () => {
      component.readonly = false;
      const spy = vi.spyOn(component.ratingChange, 'emit');
      component.handleKeydown(new KeyboardEvent('keydown', { key: 'Enter' }), 4);
      expect(component.rating).toBe(4);
      expect(spy).toHaveBeenCalledWith(4);
    });

    it('should handle Space key when not readonly', () => {
      component.readonly = false;
      const spy = vi.spyOn(component.ratingChange, 'emit');
      component.handleKeydown(new KeyboardEvent('keydown', { key: ' ' }), 1);
      expect(component.rating).toBe(1);
      expect(spy).toHaveBeenCalledWith(1);
    });

    it('should ignore non-activation keys', () => {
      component.readonly = false;
      component.rating = 3;
      const spy = vi.spyOn(component.ratingChange, 'emit');
      component.handleKeydown(new KeyboardEvent('keydown', { key: 'Tab' }), 5);
      expect(component.rating).toBe(3); // unchanged
      expect(spy).not.toHaveBeenCalled();
    });

    it('should not handle keys when readonly', () => {
      component.readonly = true;
      component.rating = 2;
      const spy = vi.spyOn(component.ratingChange, 'emit');
      component.handleKeydown(new KeyboardEvent('keydown', { key: 'Enter' }), 5);
      expect(component.rating).toBe(2); // unchanged
      expect(spy).not.toHaveBeenCalled();
    });
  });

  // ── Defaults ─────────────────────────────────────────────────

  it('should default rating to 0', () => {
    expect(component.rating).toBe(0);
  });

  it('should default readonly to true', () => {
    expect(component.readonly).toBe(true);
  });

  it('should default size to medium', () => {
    expect(component.size).toBe('medium');
  });
});
