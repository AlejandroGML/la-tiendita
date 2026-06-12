import { Injectable, inject, Renderer2, RendererFactory2 } from '@angular/core';
import { Meta, Title } from '@angular/platform-browser';
import { DOCUMENT } from '@angular/common';
import type { Product } from '../../shared/models/product.model';

@Injectable({ providedIn: 'root' })
export class SeoService {
  private readonly meta = inject(Meta);
  private readonly title = inject(Title);
  private readonly rendererFactory = inject(RendererFactory2);
  private readonly document = inject(DOCUMENT);

  private renderer: Renderer2;
  private lastJsonLdScript: HTMLScriptElement | null = null;

  constructor() {
    this.renderer = this.rendererFactory.createRenderer(null, null);
  }

  /** Set basic page title and og:title */
  setPageTitle(pageTitle: string): void {
    const fullTitle = pageTitle ? `${pageTitle} | La Tiendita` : 'La Tiendita';
    this.title.setTitle(fullTitle);
    this.meta.updateTag({ property: 'og:title', content: fullTitle });
  }

  /** Set meta description */
  setDescription(desc: string): void {
    if (desc) {
      this.meta.updateTag({ name: 'description', content: desc.slice(0, 160) });
      this.meta.updateTag({ property: 'og:description', content: desc.slice(0, 200) });
    }
  }

  /** Set og:image */
  setOgImage(imageUrl: string): void {
    if (imageUrl) {
      this.meta.updateTag({ property: 'og:image', content: imageUrl });
    }
  }

  /** Inject JSON-LD structured data for a Product */
  setProductStructuredData(product: Product, displayName: string, displayDescription: string): void {
    // Remove previous JSON-LD script if present
    if (this.lastJsonLdScript) {
      this.renderer.removeChild(this.document.head, this.lastJsonLdScript);
      this.lastJsonLdScript = null;
    }

    const mainImage = product.image_urls?.[0] ?? '';
    const availability =
      product.variants?.some((v) => v.stock > 0) ? 'InStock' : 'OutOfStock';

    const structuredData: Record<string, unknown> = {
      '@context': 'https://schema.org',
      '@type': 'Product',
      name: displayName,
      description: displayDescription,
      image: mainImage,
      offers: {
        '@type': 'Offer',
        price: product.sale_price ?? product.price,
        priceCurrency: 'SEK',
        availability: `https://schema.org/${availability}`,
      },
    };

    if (product.brand) {
      structuredData['brand'] = { '@type': 'Brand', name: product.brand };
    }

    const script = this.renderer.createElement('script');
    script.type = 'application/ld+json';
    script.text = JSON.stringify(structuredData);

    this.renderer.appendChild(this.document.head, script);
    this.lastJsonLdScript = script;
  }

  /** Remove structured data (cleanup when leaving product page) */
  removeStructuredData(): void {
    if (this.lastJsonLdScript) {
      this.renderer.removeChild(this.document.head, this.lastJsonLdScript);
      this.lastJsonLdScript = null;
    }
  }
}
