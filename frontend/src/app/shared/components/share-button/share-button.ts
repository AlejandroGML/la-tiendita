import { Component, Input, signal } from '@angular/core';

@Component({
  selector: 'app-share-button',
  standalone: true,
  templateUrl: './share-button.html',
  styles: []
})
export class ShareButtonComponent {
  @Input() title: string = 'Mira este producto';
  @Input() url: string = '';
  @Input() image: string = '';

  open = signal(false);

  get shareUrl() { return this.url || (typeof window !== 'undefined' ? window.location.href : ''); }

  get whatsappUrl() { return `https://wa.me/?text=${encodeURIComponent(this.title + ' — ' + this.shareUrl)}`; }
  get facebookUrl() { return `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(this.shareUrl)}`; }
  get pinterestUrl() {
    return `https://pinterest.com/pin/create/button/?url=${encodeURIComponent(this.shareUrl)}&media=${encodeURIComponent(this.image || '')}&description=${encodeURIComponent(this.title)}`;
  }

  async nativeShare() {
    if (navigator.share) {
      try {
        await navigator.share({ title: this.title, url: this.shareUrl });
      } catch {}
    } else {
      this.open.set(!this.open());
    }
  }

  copyLink() {
    navigator.clipboard.writeText(this.shareUrl);
    this.open.set(false);
  }
}
