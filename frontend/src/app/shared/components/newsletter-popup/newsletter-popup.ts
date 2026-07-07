import { Component, signal, inject, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NewsletterService } from '../../../core/services/newsletter.service';

const DISMISSED_KEY = 'newsletter_dismissed';
const SUBSCRIBED_KEY = 'newsletter_subscribed';
const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000;

@Component({
  selector: 'app-newsletter-popup',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './newsletter-popup.html',
})
export class NewsletterPopupComponent implements AfterViewInit {
  private readonly newsletterService = inject(NewsletterService);

  visible = signal(false);
  submitted = signal(false);
  email = signal('');
  loading = signal(false);
  error = signal<string | null>(null);

  ngAfterViewInit(): void {
    this.checkInitialState();
  }

  private checkInitialState(): void {
    if (localStorage.getItem(SUBSCRIBED_KEY) === 'true') return;

    const dismissed = localStorage.getItem(DISMISSED_KEY);
    if (dismissed) {
      const dismissedAt = parseInt(dismissed, 10);
      if (Date.now() - dismissedAt < SEVEN_DAYS_MS) return;
    }

    setTimeout(() => this.visible.set(true), 20000);
  }

  submit(): void {
    const emailValue = this.email().trim();
    if (!emailValue) return;

    this.loading.set(true);
    this.error.set(null);

    this.newsletterService.subscribe(emailValue).subscribe({
      next: () => {
        localStorage.setItem(SUBSCRIBED_KEY, 'true');
        this.submitted.set(true);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Error al suscribir. Intenta de nuevo.');
        this.loading.set(false);
      },
    });
  }

  dismiss(): void {
    localStorage.setItem(DISMISSED_KEY, String(Date.now()));
    this.visible.set(false);
  }
}
