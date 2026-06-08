import { Component, inject, OnInit } from '@angular/core';
import { Title, Meta } from '@angular/platform-browser';
import { Router, NavigationEnd } from '@angular/router';
import { filter, map } from 'rxjs/operators';
import { TranslateService } from '@ngx-translate/core';

const SITE_NAME = 'La Tiendita';

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  standalone: false,
  styleUrl: './app.scss',
})
export class App implements OnInit {
  private router = inject(Router);
  private titleService = inject(Title);
  private meta = inject(Meta);
  private translate = inject(TranslateService);

  ngOnInit(): void {
    this.translate.setDefaultLang('es');
    this.translate.use('es');
    this.router.events
      .pipe(
        filter((event): event is NavigationEnd => event instanceof NavigationEnd),
        map((event) => event.urlAfterRedirects),
      )
      .subscribe((url) => {
        const routeTitle = this.getRouteTitle(url);
        const fullTitle = routeTitle
          ? `${routeTitle} | ${SITE_NAME}`
          : SITE_NAME;
        this.titleService.setTitle(fullTitle);
        this.meta.updateTag({
          property: 'og:title',
          content: fullTitle,
        });
      });
  }

  private getRouteTitle(url: string): string {
    // Strip leading slash, query params, and trailing slash
    const clean = url.replace(/^\/+|\/+$/g, '').split('?')[0];

    const titleMap: Record<string, string> = {
      '': 'Inicio',
      productos: 'Productos',
      carrito: 'Carrito',
      checkout: 'Checkout',
      login: 'Iniciar Sesión',
      register: 'Registro',
      admin: 'Administración',
      perfil: 'Mi Perfil',
    };

    // Exact match for known routes
    if (titleMap[clean]) return titleMap[clean];

    // Nested routes — use the first segment
    const segment = clean.split('/')[0];
    return titleMap[segment] ?? '';
  }
}
