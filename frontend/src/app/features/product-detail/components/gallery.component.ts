import { Component, Input, signal } from '@angular/core';

@Component({
  selector: 'app-product-detail-gallery',
  templateUrl: './gallery.component.html',
  standalone: false,
})
export class ProductDetailGalleryComponent {
  @Input() images: string[] = [];
  @Input() alt = '';

  readonly activeImageIndex = signal(0);

  readonly galleriaResponsiveOptions = [
    { breakpoint: '1024px', numVisible: 5 },
    { breakpoint: '768px', numVisible: 3 },
    { breakpoint: '560px', numVisible: 2 },
  ];
}
