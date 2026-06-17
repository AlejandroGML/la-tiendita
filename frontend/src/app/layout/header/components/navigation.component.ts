import {
  Component,
  inject,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  OnInit,
  OnDestroy,
} from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Subscription } from 'rxjs';
import { svgIcon } from '../../../shared/utils/svg-icons';

@Component({
  selector: 'app-navigation',
  templateUrl: './navigation.component.html',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NavigationComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly sanitizer = inject(DomSanitizer);
  private readonly cdr = inject(ChangeDetectorRef);

  currentGender: string | null = null;
  private querySub: Subscription | null = null;

  protected readonly GENDER_TABS = [
    { key: 'women', label: 'gender.women', value: 'women' },
    { key: 'men', label: 'gender.men', value: 'men' },
    { key: 'kids', label: 'gender.kids', value: 'kids' },
    { key: 'unisex', label: 'gender.unisex', value: 'unisex' },
  ] as const;

  ngOnInit(): void {
    this.querySub = this.route.queryParamMap.subscribe((params) => {
      this.currentGender = params.get('gender') || null;
      this.cdr.markForCheck();
    });
  }

  ngOnDestroy(): void {
    this.querySub?.unsubscribe();
  }

  protected isGenderActive(gender: string): boolean {
    return this.currentGender === gender;
  }

  protected navigateByGender(gender: string): void {
    this.router.navigate(['/productos'], {
      queryParams: { gender },
      queryParamsHandling: 'merge',
    });
  }

  protected svg(name: string, className = 'w-5 h-5'): SafeHtml {
    return svgIcon(name, className, this.sanitizer) as SafeHtml;
  }
}
