import { Component } from '@angular/core';

@Component({
  selector: 'app-header',
  templateUrl: './header.html',
  standalone: false,
  styleUrl: './header.scss',
})
export class Header {
  protected readonly title = 'La Tiendita';
}
