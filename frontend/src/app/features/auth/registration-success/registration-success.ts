import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';

@Component({
  selector: 'app-registration-success',
  standalone: true,
  imports: [CommonModule, RouterLink, ButtonModule, CardModule],
  template: `
    <div class="flex justify-center items-center min-h-[70vh] px-4">
      <p-card styleClass="w-full max-w-md text-center p-6">
        <div class="flex flex-col items-center gap-4">
          <!-- Checkmark icon -->
          <div class="w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24"
                 fill="none" stroke="currentColor" stroke-width="2.5"
                 stroke-linecap="round" stroke-linejoin="round"
                 class="text-emerald-500 dark:text-emerald-400">
              <path d="M20 6 9 17l-5-5"/>
            </svg>
          </div>

          <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
            ¡Registro exitoso!
          </h1>

          <p class="text-gray-500 dark:text-gray-400 text-sm max-w-xs">
            Tu cuenta se ha creado correctamente. Bienvenido a La Tiendita.
          </p>

          <p class="text-xs text-gray-400 dark:text-gray-500">
            Serás redirigido al inicio en <strong class="text-emerald-600 dark:text-emerald-400">{{ countdown }}</strong> segundos
          </p>

          <div class="w-full h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
            <div class="h-full bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-full transition-all duration-1000 ease-linear"
                 [style.width.%]="(countdown / 5) * 100"></div>
          </div>

          <a pButton routerLink="/" class="mt-2" severity="primary">
            Volver a la página principal
          </a>
        </div>
      </p-card>
    </div>
  `,
})
export class RegistrationSuccess implements OnInit, OnDestroy {
  private readonly router = inject(Router);

  countdown = 5;
  private timer: ReturnType<typeof setInterval> | null = null;

  ngOnInit(): void {
    this.timer = setInterval(() => {
      this.countdown--;
      if (this.countdown <= 0) {
        this.redirect();
      }
    }, 1000);
  }

  ngOnDestroy(): void {
    if (this.timer !== null) {
      clearInterval(this.timer);
    }
  }

  private redirect(): void {
    if (this.timer !== null) {
      clearInterval(this.timer);
      this.timer = null;
    }
    this.router.navigate(['/']);
  }
}
