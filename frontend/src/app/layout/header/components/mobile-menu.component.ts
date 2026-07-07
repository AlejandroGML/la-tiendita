import {
  Component,
  inject,
  Input,
  Output,
  EventEmitter,
  ChangeDetectionStrategy,
  HostListener,
} from '@angular/core';
import { Router } from '@angular/router';

import { type CategoryItem } from '../../../core/services/category.service';

const CATEGORY_ICONS: Record<string, string> = {
  accessories: 'pi-box',
  bag: 'pi-briefcase',
  belt: 'pi-tag',
  blazer: 'pi-tag',
  blouse: 'pi-heart',
  boots: 'pi-box',
  cardigan: 'pi-sun',
  coat: 'pi-tag',
  dress: 'pi-image',
  hat: 'pi-box',
  heels: 'pi-box',
  jacket: 'pi-tag',
  jeans: 'pi-ticket',
  jumpsuit: 'pi-box',
  pants: 'pi-ticket',
  playsuit: 'pi-box',
  poncho: 'pi-box',
  sandals: 'pi-box',
  scarf: 'pi-box',
  shirt: 'pi-briefcase',
  shoes: 'pi-box',
  shorts: 'pi-box',
  skirt: 'pi-image',
  sneakers: 'pi-box',
  sweater: 'pi-sun',
  't-shirt': 'pi-ticket',
  'tank-top': 'pi-th-large',
  top: 'pi-heart',
  tunic: 'pi-heart',
  vest: 'pi-box',
};

@Component({
  selector: 'app-mobile-menu',
  templateUrl: './mobile-menu.component.html',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MobileMenuComponent {
  @Input() isOpen = false;
  @Input() categories: CategoryItem[] = [];
  @Output() closed = new EventEmitter<void>();

  private readonly router = inject(Router);

  searchTerm = '';

  protected onSearch(term: string): void {
    if (term.trim()) {
      this.router.navigate(['/productos'], { queryParams: { q: term } });
      this.closed.emit();
    }
  }

  protected getCategoryIcon(slug: string): string {
    return CATEGORY_ICONS[slug] || 'pi-tag';
  }

  /** Close when clicking outside the component */
  @HostListener('document:click', ['$event'])
  protected onDocumentClick(event: MouseEvent): void {
    if (this.isOpen) {
      const target = event.target as HTMLElement;
      if (!target.closest('[data-mobile-menu]')) {
        this.closed.emit();
      }
    }
  }
}
