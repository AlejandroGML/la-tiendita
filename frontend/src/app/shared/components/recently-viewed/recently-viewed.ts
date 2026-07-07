import { Component, computed, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { CurrencyService } from '../../../core/services/currency.service';
import { SharedPipesModule } from '../../shared-pipes.module';

interface RecentProduct {
  id: string;
  slug: string;
  name: string;
  image_url: string;
  price: number;
  viewedAt: number;
}

@Component({
  selector: 'app-recently-viewed',
  standalone: true,
  imports: [CommonModule, RouterLink, SharedPipesModule],
  templateUrl: './recently-viewed.html',
})
export class RecentlyViewedComponent implements OnInit {
  private readonly currencyService = inject(CurrencyService);
  readonly currency = this.currencyService.currency;
  products = signal<RecentProduct[]>([]);
  visible = signal(false);

  ngOnInit(): void {
    const raw = localStorage.getItem('recently_viewed');
    if (!raw) return;

    let items: RecentProduct[] = [];
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) items = parsed;
    } catch {
      localStorage.removeItem('recently_viewed');
      return;
    }

    const thirtyDays = 30 * 24 * 60 * 60 * 1000;
    const recent = items
      .filter((i) => Date.now() - i.viewedAt < thirtyDays)
      .slice(0, 6);

    this.products.set(recent);
    this.visible.set(recent.length > 0);
  }
}
