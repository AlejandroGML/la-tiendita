import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormArray, FormBuilder, FormGroup, Validators } from '@angular/forms';
import type {
  CreatePromotionPayload,
  Promotion,
  PromotionTranslation,
} from '../../../../shared/models/promotion.model';

interface EditingPromotion extends Promotion {
  _editing?: boolean;
}

function pad(n: number): string {
  return n.toString().padStart(2, '0');
}

@Component({
  selector: 'app-promotion-form',
  templateUrl: './promotion-form.component.html',
  styleUrls: ['./promotion-form.component.scss'],
  standalone: false,
})
export class PromotionFormComponent implements OnInit {
  @Input() promotion: Promotion | EditingPromotion | null = null;
  @Input() saving = false;
  @Output() saved = new EventEmitter<CreatePromotionPayload>();
  @Output() cancelled = new EventEmitter<void>();

  form!: FormGroup;

  readonly langOptions = [
    { label: 'ES', value: 'es' },
    { label: 'EN', value: 'en' },
    { label: 'SV', value: 'sv' },
  ];

  constructor(private readonly fb: FormBuilder) {}

  ngOnInit(): void {
    this.buildForm();
  }

  private buildForm(): void {
    const p = this.promotion;
    this.form = this.fb.group({
      code: [p?.code ?? '', [Validators.required, Validators.maxLength(50)]],
      discount_percent: [
        p?.discount_percent ?? 10,
        [Validators.required, Validators.min(1), Validators.max(100)],
      ],
      product_id: [p?.product_id ?? null],
      max_uses: [p?.max_uses ?? null, [Validators.min(1)]],
      start_date: [p?.start_date ?? ''],
      end_date: [p?.end_date ?? ''],
      is_active: [p?.is_active ?? true],
      translations: this.fb.array(
        (p?.translations?.length
          ? p.translations
          : [
              { lang: 'es', title: '', description: '' },
              { lang: 'en', title: '', description: '' },
              { lang: 'sv', title: '', description: '' },
            ]
        ).map((t) => this.createTranslationGroup(t)),
      ),
    });
  }

  private createTranslationGroup(t?: PromotionTranslation): FormGroup {
    return this.fb.group({
      lang: [t?.lang ?? 'es', Validators.required],
      title: [
        t?.title ?? '',
        [Validators.required, Validators.maxLength(255)],
      ],
      description: [t?.description ?? ''],
    });
  }

  get translationsArray(): FormArray {
    return this.form.get('translations') as FormArray;
  }

  submitForm(): void {
    if (this.form.invalid) return;
    const raw = this.form.value as CreatePromotionPayload;
    const payload: CreatePromotionPayload = {
      ...raw,
      max_uses: raw.max_uses || null,
      product_id: raw.product_id || null,
      start_date: raw.start_date || null,
      end_date: raw.end_date || null,
    };
    this.saved.emit(payload);
  }

  cancelForm(): void {
    this.cancelled.emit();
  }

  toDate(isoString: string | null): Date | null {
    if (!isoString) return null;
    return new Date(isoString);
  }

  fromDate(date: Date | null): string | null {
    if (!date) return null;
    const y = date.getFullYear();
    const mo = pad(date.getMonth() + 1);
    const d = pad(date.getDate());
    const h = pad(date.getHours());
    const mi = pad(date.getMinutes());
    return `${y}-${mo}-${d}T${h}:${mi}`;
  }
}
