import { Directive, ElementRef, HostListener, Renderer2 } from '@angular/core';

@Directive({ selector: '[appImageZoom]', standalone: true })
export class ImageZoomDirective {
  private img: HTMLImageElement;

  constructor(private el: ElementRef, private renderer: Renderer2) {
    this.img = el.nativeElement;
    this.renderer.setStyle(this.img, 'transition', 'transform 0.3s ease');
    this.renderer.setStyle(this.img, 'cursor', 'zoom-in');
  }

  @HostListener('mousemove', ['$event'])
  onMouseMove(e: MouseEvent) {
    const rect = this.img.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    this.renderer.setStyle(this.img, 'transformOrigin', `${x}% ${y}%`);
    this.renderer.setStyle(this.img, 'transform', 'scale(2)');
    this.renderer.setStyle(this.img, 'cursor', 'zoom-out');
  }

  @HostListener('mouseleave')
  onMouseLeave() {
    this.renderer.setStyle(this.img, 'transform', 'scale(1)');
    this.renderer.setStyle(this.img, 'cursor', 'zoom-in');
  }
}
