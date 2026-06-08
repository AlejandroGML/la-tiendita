import { ComponentFixture, TestBed } from '@angular/core/testing';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { InputTextModule } from 'primeng/inputtext';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { SearchBarComponent } from './search-bar';

describe('SearchBarComponent', () => {
  let fixture: ComponentFixture<SearchBarComponent>;
  let component: SearchBarComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [SearchBarComponent],
      imports: [
        IconFieldModule,
        InputIconModule,
        InputTextModule,
        NoopAnimationsModule,
        TranslateModule.forRoot(),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SearchBarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  function setInputAndDispatch(value: string): void {
    const input = fixture.nativeElement.querySelector('input') as HTMLInputElement;
    input.value = value;
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
  }

  it('should emit search event after 300ms debounce', async () => {
    const emitted: string[] = [];
    component.search.subscribe((term) => emitted.push(term));

    setInputAndDispatch('denim');

    // Should not emit immediately — wait for debounce
    await new Promise((r) => setTimeout(r, 400));
    expect(emitted.length).toBe(1);
    expect(emitted[0]).toBe('denim');
  });

  it('should emit distinct values only', async () => {
    const emitted: string[] = [];
    component.search.subscribe((term) => emitted.push(term));

    setInputAndDispatch('denim');
    await new Promise((r) => setTimeout(r, 400));
    expect(emitted.length).toBe(1);

    // Same value again
    setInputAndDispatch('denim');
    await new Promise((r) => setTimeout(r, 400));
    // distinctUntilChanged blocks duplicate
    expect(emitted.length).toBe(1);
  });

  it('should emit different values after debounce', async () => {
    const emitted: string[] = [];
    component.search.subscribe((term) => emitted.push(term));

    setInputAndDispatch('denim');
    await new Promise((r) => setTimeout(r, 400));
    expect(emitted[0]).toBe('denim');

    setInputAndDispatch('jacket');
    await new Promise((r) => setTimeout(r, 400));
    expect(emitted.length).toBe(2);
    expect(emitted[1]).toBe('jacket');
  });

  it('should trim whitespace from search input', async () => {
    const emitted: string[] = [];
    component.search.subscribe((term) => emitted.push(term));

    setInputAndDispatch('  denim  ');
    await new Promise((r) => setTimeout(r, 400));
    expect(emitted[0]).toBe('denim');
  });
});
