import { Component, Input } from '@angular/core';

const COLOR_MAP: Record<string, string> = {
  black: '#000000',
  white: '#FFFFFF',
  red: '#DC2626',
  green: '#16A34A',
  blue: '#2563EB',
  yellow: '#EAB308',
  purple: '#7C3AED',
  pink: '#EC4899',
  gray: '#6B7280',
  grey: '#6B7280',
  orange: '#EA580C',
  brown: '#92400E',
  beige: '#F5E6D3',
  navy: '#1E3A5F',
};

export interface ColorSwatch {
  hex: string;
  color: string;
}

@Component({
  selector: 'app-product-color-swatches',
  templateUrl: './color-swatches.component.html',
  standalone: false,
})
export class ProductColorSwatchesComponent {
  @Input({ required: true }) colors!: ColorSwatch[];
  @Input() maxVisible = 4;

  get visibleColors(): ColorSwatch[] {
    return this.colors.slice(0, this.maxVisible);
  }

  get overflowCount(): number {
    return Math.max(0, this.colors.length - this.maxVisible);
  }

  get isVisible(): boolean {
    return this.colors.length > 0;
  }

  /** Resolve hex color: use hex value, fallback to COLOR_MAP, finally #ccc */
  resolveHex(swatch: ColorSwatch): string {
    if (swatch.hex) return swatch.hex;
    const key = swatch.color.toLowerCase().trim();
    return COLOR_MAP[key] ?? '#ccc';
  }
}
