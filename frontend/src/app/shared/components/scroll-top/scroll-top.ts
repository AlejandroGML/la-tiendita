import { Component, HostListener, signal } from '@angular/core';

@Component({
  selector: 'app-scroll-top',
  standalone: true,
  template: `
    @if (visible()) {
      <button (click)="scrollTop()"
        class="fixed bottom-24 md:bottom-6 right-4 z-50 w-10 h-10 bg-white/80 backdrop-blur shadow-lg rounded-full flex items-center justify-center text-gray-600 hover:text-emerald-600 hover:bg-white transition-all duration-200 border border-gray-200"
        aria-label="Volver arriba">
        <i class="pi pi-arrow-up"></i>
      </button>
    }
  `,
  styles: []
})
export class ScrollTopComponent {
  visible = signal(false);

  @HostListener('window:scroll')
  onScroll() {
    this.visible.set(window.scrollY > 500);
  }

  scrollTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}
