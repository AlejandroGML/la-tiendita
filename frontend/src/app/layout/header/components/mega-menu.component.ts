import {
  Component,
  inject,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  OnInit,
  OnDestroy,
  HostListener,
} from '@angular/core';
import { Subscription } from 'rxjs';
import { CategoryService, type CategoryItem, type CategoryGroup } from '../../../core/services/category.service';

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
  selector: 'app-mega-menu',
  templateUrl: './mega-menu.component.html',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MegaMenuComponent implements OnInit, OnDestroy {
  private readonly categoryService = inject(CategoryService);
  private readonly cdr = inject(ChangeDetectorRef);

  megaOpen = false;
  categories: CategoryItem[] = [];
  private categoriesSub: Subscription | null = null;
  private megaTimeout: ReturnType<typeof setTimeout> | null = null;

  /** Agrupa las categorías en 3 columnas para el mega menú */
  protected get categoryGroups(): CategoryGroup[] {
    const labels = ['Ropa', 'Accesorios', 'Calzado'];
    const groups: CategoryGroup[] = [];
    const size = Math.max(1, Math.ceil(this.categories.length / 3));
    for (let i = 0; i < this.categories.length; i += size) {
      groups.push({
        label: labels[groups.length] || 'Otros',
        items: this.categories.slice(i, i + size),
      });
    }
    return groups;
  }

  ngOnInit(): void {
    this.categoryService.load();
    this.categoriesSub = this.categoryService.categories$.subscribe((data) => {
      if (data) {
        this.categories = data;
        this.cdr.markForCheck();
      }
    });
  }

  ngOnDestroy(): void {
    this.clearMegaTimeout();
    this.categoriesSub?.unsubscribe();
  }

  // ── Hover logic ──

  /** Close when clicking outside the component */
  @HostListener('document:click', ['$event'])
  protected onDocumentClick(event: MouseEvent): void {
    if (this.megaOpen) {
      const target = event.target as HTMLElement;
      if (!target.closest('app-mega-menu')) {
        this.megaOpen = false;
        this.clearMegaTimeout();
        this.cdr.markForCheck();
      }
    }
  }

  /** Open immediately (no delay on enter) */
  protected onMegaEnter(): void {
    this.clearMegaTimeout();
    this.megaOpen = true;
    this.cdr.markForCheck();
  }

  /** Close with 200ms grace period — allows moving to the panel */
  protected onMegaLeave(): void {
    this.megaTimeout = setTimeout(() => {
      this.megaOpen = false;
      this.cdr.markForCheck();
    }, 200);
  }

  /** Close immediately — for when the mouse leaves the panel itself */
  protected closeMegaPanel(): void {
    this.clearMegaTimeout();
    this.megaOpen = false;
    this.cdr.markForCheck();
  }

  private clearMegaTimeout(): void {
    if (this.megaTimeout !== null) {
      clearTimeout(this.megaTimeout);
      this.megaTimeout = null;
    }
  }

  protected getCategoryIcon(slug: string): string {
    return CATEGORY_ICONS[slug] || 'pi-tag';
  }
}
