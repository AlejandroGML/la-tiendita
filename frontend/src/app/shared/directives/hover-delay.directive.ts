import {
  Directive,
  EventEmitter,
  Input,
  Output,
  HostListener,
  OnDestroy,
} from '@angular/core';

/**
 * Reusable directive that encapsulates the hover-with-delay pattern.
 *
 * The directive manages two configurable timers:
 * - **openDelay** (default 150ms): grace period before setting the open state
 *   when the cursor enters the host element.
 * - **closeDelay** (default 200ms): grace period before clearing the open
 *   state when the cursor leaves.
 *
 * Use with two-way binding for a clean component contract:
 * ```html
 * <div [(appHoverDelayOpen)]="isOpen" [openDelay]="150" [closeDelay]="200">
 * ```
 *
 * Both timers auto-cancel on rapid enter/leave (e.g. the user accidentally
 * passing over the trigger area), preventing flicker.
 */
@Directive({
  selector: '[appHoverDelay]',
  standalone: false,
})
export class HoverDelayDirective implements OnDestroy {
  /**
   * Two-way bindable open state. Set `true` to open, `false` to close.
   * Emits `appHoverDelayOpenChange` when the internal timer fires.
   */
  @Input() appHoverDelayOpen = false;

  /** Emits the new open state when the internal timer fires. */
  @Output() readonly appHoverDelayOpenChange = new EventEmitter<boolean>();

  /** Delay in milliseconds before opening when the cursor enters. */
  @Input() openDelay = 150;

  /** Delay in milliseconds before closing when the cursor leaves. */
  @Input() closeDelay = 200;

  private openTimer: ReturnType<typeof setTimeout> | null = null;
  private closeTimer: ReturnType<typeof setTimeout> | null = null;

  /** Mouse enters the host element — schedule the open after `openDelay`. */
  @HostListener('mouseenter')
  protected onMouseEnter(): void {
    this.clearCloseTimer();
    if (this.openTimer === null) {
      this.openTimer = setTimeout(() => {
        this.openTimer = null;
        this.appHoverDelayOpen = true;
        this.appHoverDelayOpenChange.emit(true);
      }, this.openDelay);
    }
  }

  /** Mouse leaves the host element — schedule the close after `closeDelay`. */
  @HostListener('mouseleave')
  protected onMouseLeave(): void {
    this.clearOpenTimer();
    if (this.closeTimer === null) {
      this.closeTimer = setTimeout(() => {
        this.closeTimer = null;
        this.appHoverDelayOpen = false;
        this.appHoverDelayOpenChange.emit(false);
      }, this.closeDelay);
    }
  }

  /** Clean up all pending timers on destroy to prevent memory leaks. */
  ngOnDestroy(): void {
    this.clearOpenTimer();
    this.clearCloseTimer();
  }

  private clearOpenTimer(): void {
    if (this.openTimer !== null) {
      clearTimeout(this.openTimer);
      this.openTimer = null;
    }
  }

  private clearCloseTimer(): void {
    if (this.closeTimer !== null) {
      clearTimeout(this.closeTimer);
      this.closeTimer = null;
    }
  }
}
