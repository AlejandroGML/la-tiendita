import { Component, EventEmitter, Output, OnDestroy } from '@angular/core';
import { Subject, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

@Component({
  selector: 'app-search-bar',
  templateUrl: './search-bar.html',
  styleUrls: ['./search-bar.scss'],
  standalone: false,
})
export class SearchBarComponent implements OnDestroy {
  @Output() search = new EventEmitter<string>();

  private searchSubject = new Subject<string>();
  private sub: Subscription;

  constructor() {
    this.sub = this.searchSubject
      .pipe(debounceTime(300), distinctUntilChanged())
      .subscribe((term) => this.search.emit(term));
  }

  onInput(value: string): void {
    this.searchSubject.next(value.trim());
  }

  ngOnDestroy(): void {
    this.sub.unsubscribe();
  }
}
