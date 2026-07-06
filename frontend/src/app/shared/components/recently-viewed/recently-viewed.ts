import { Component, signal, OnInit } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';

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
  imports: [CommonModule, RouterLink, DecimalPipe],
  templateUrl: './recently-viewed.html',
})
export class RecentlyViewedComponent implements OnInit {
  products = signal<RecentProduct[]>([]);
  visible = signal(false);

  ngOnInit(): void {
    const raw = localStorage.getItem('recently_viewed');
    if (!raw) return;

    const items: RecentProduct[] = JSON.parse(raw);
    const thirtyDays = 30 * 24 * 60 * 60 * 1000;
    const recent = items
      .filter((i) => Date.now() - i.viewedAt < thirtyDays)
      .slice(0, 6);

    this.products.set(recent);
    this.visible.set(recent.length > 0);
  }
}
