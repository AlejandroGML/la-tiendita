import { Component, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-cookie-consent',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './cookie-consent.html',
  styleUrls: ['./cookie-consent.scss']
})
export class CookieConsentComponent {
  visible = signal(!localStorage.getItem('cookie_consent'));

  accept() {
    localStorage.setItem('cookie_consent', 'true');
    this.visible.set(false);
  }
}
