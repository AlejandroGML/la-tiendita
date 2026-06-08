import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import {
  AbstractControl,
  FormArray,
  FormBuilder,
  FormGroup,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { HttpClient } from '@angular/common/http';
import { Subject, takeUntil } from 'rxjs';
import type { Product } from '../../../shared/models/product.model';
import type { Category } from '../../../shared/models/category.model';
import { AdminProductService } from '../../../core/services/admin-product.service';
import type { CreateProductPayload } from '../../../core/services/admin-product.service';

function esNameRequired(group: AbstractControl): ValidationErrors | null {
  const translations = group.get('translations') as FormArray;
  if (!translations) return null;
  const esGroup = translations.controls.find(
    (ctrl) => ctrl.get('lang')?.value === 'es',
  );
  const name = esGroup?.get('name')?.value?.trim();
  return name ? null : { esNameRequired: true };
}

@Component({
  selector: 'app-admin-product-form',
  templateUrl: './admin-product-form.html',
  styleUrls: ['./admin-product-form.scss'],
  standalone: false,
  providers: [MessageService],
})
export class AdminProductForm implements OnInit, OnDestroy {
  private readonly destroy$ = new Subject<void>();

  readonly form: FormGroup;
  readonly editingProduct = signal<Product | null>(null);
  readonly loading = signal(false);
  readonly submitting = signal(false);
  readonly categories = signal<Category[]>([]);
  readonly imagePreviewUrls = signal<string[]>([]);
  readonly imageFiles = signal<File[]>([]);

  readonly conditions = ['new', 'like_new', 'good', 'fair'];
  readonly sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];

  private editSlug: string | null = null;

  get translations(): FormArray {
    return this.form.get('translations') as FormArray;
  }

  get selectedTabIndex(): number {
    return this.form.get('selectedTab')?.value ?? 0;
  }

  constructor(
    private readonly fb: FormBuilder,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly adminProductService: AdminProductService,
    private readonly http: HttpClient,
    private readonly messageService: MessageService,
  ) {
    this.form = this.fb.group(
      {
        price: [null, [Validators.required, Validators.min(1)]],
        category_id: [null, Validators.required],
        size: [''],
        brand: [''],
        condition: ['good'],
        stock: [1, [Validators.required, Validators.min(0)]],
        selectedTab: [0],
        translations: this.fb.array([
          this.createTranslationGroup('es'),
          this.createTranslationGroup('en'),
          this.createTranslationGroup('sv'),
        ]),
      },
      { validators: esNameRequired },
    );
  }

  private createTranslationGroup(lang: string): FormGroup {
    return this.fb.group({
      lang: [lang],
      name: ['', lang === 'es' ? Validators.required : []],
      description: [''],
    });
  }

  private createEmptyTranslations(): FormArray {
    return this.fb.array([
      this.createTranslationGroup('es'),
      this.createTranslationGroup('en'),
      this.createTranslationGroup('sv'),
    ]);
  }

  ngOnInit(): void {
    this.loadCategories();
    this.editSlug = this.route.snapshot.paramMap.get('slug');

    if (this.editSlug) {
      this.loadProduct(this.editSlug);
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();

    // Revoke blob URLs
    for (const url of this.imagePreviewUrls()) {
      URL.revokeObjectURL(url);
    }
  }

  private loadCategories(): void {
    this.http
      .get<Category[]>('/api/categories')
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (cats) => this.categories.set(cats),
        error: () => {
          /* categories are optional for form */
        },
      });
  }

  private loadProduct(slug: string): void {
    this.loading.set(true);
    this.adminProductService
      .getAdminProducts({ per_page: 1, search: slug })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => {
          const product = res.data.find((p) => p.slug === slug);
          if (product) {
            this.editingProduct.set(product);
            this.populateForm(product);
          }
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.messageService.add({ severity: 'error', detail: 'catalog.error', life: 3000 });
        },
      });
  }

  private populateForm(product: Product): void {
    this.form.patchValue({
      price: product.price,
      category_id: product.category_id,
      size: product.size,
      brand: product.brand,
      condition: product.condition,
      stock: product.stock,
    });

    // Populate translations
    const translationsArr = this.translations;
    for (const t of product.translations) {
      const group = translationsArr.controls.find(
        (ctrl) => ctrl.get('lang')?.value === t.lang,
      );
      if (group) {
        group.patchValue({ name: t.name, description: t.description });
      }
    }

    // Show existing images as previews
    if (product.image_urls?.length) {
      this.imagePreviewUrls.set([...product.image_urls]);
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const files = input.files;
    if (!files?.length) return;

    const newFiles: File[] = [];
    const newPreviews: string[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files.item(i);
      if (!file) continue;

      // Validate JPEG/PNG/WebP
      const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
      if (!validTypes.includes(file.type)) continue;

      // Validate size (5 MB max)
      if (file.size > 5 * 1024 * 1024) continue;

      newFiles.push(file);
      newPreviews.push(URL.createObjectURL(file));
    }

    if (newFiles.length > 0) {
      this.imageFiles.update((prev) => [...prev, ...newFiles]);
      this.imagePreviewUrls.update((prev) => [...prev, ...newPreviews]);
    }

    // Reset input so the same file can be re-selected
    input.value = '';
  }

  removeImage(index: number): void {
    const urls = this.imagePreviewUrls();
    // If it's a blob URL (new upload), revoke it
    if (urls[index]?.startsWith('blob:')) {
      URL.revokeObjectURL(urls[index]);
    }

    this.imagePreviewUrls.update((prev) => prev.filter((_, i) => i !== index));
    this.imageFiles.update((prev) => prev.filter((_, i) => i !== index));
  }

  onSubmit(): void {
    if (this.form.invalid) {
      // Mark all as touched to show validation errors
      this.form.markAllAsTouched();
      return;
    }

    this.submitting.set(true);

    const formValue = this.form.value;
    const payload: CreateProductPayload = {
      price: formValue.price,
      category_id: formValue.category_id,
      size: formValue.size || undefined,
      brand: formValue.brand || undefined,
      condition: formValue.condition,
      stock: formValue.stock,
      translations: formValue.translations
        .filter((t: { name: string }) => t.name?.trim())
        .map((t: { lang: string; name: string; description: string }) => ({
          lang: t.lang,
          name: t.name.trim(),
          description: t.description?.trim() || undefined,
        })),
    };

    if (this.editSlug) {
        this.adminProductService
          .updateProduct(this.editSlug, payload)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            this.messageService.add({ severity: 'success', detail: 'admin.productSaved', life: 3000 });
            this.router.navigate(['/admin/productos']);
          },
          error: () => {
            this.submitting.set(false);
            this.messageService.add({ severity: 'error', detail: 'catalog.error', life: 3000 });
          },
        });
    } else {
        this.adminProductService
          .createProduct(payload)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            this.messageService.add({ severity: 'success', detail: 'admin.productSaved', life: 3000 });
            this.router.navigate(['/admin/productos']);
          },
          error: () => {
            this.submitting.set(false);
            this.messageService.add({ severity: 'error', detail: 'catalog.error', life: 3000 });
          },
        });
    }
  }

  onCancel(): void {
    this.router.navigate(['/admin/productos']);
  }

  setSelectedTab(index: any): void {
    this.form.patchValue({ selectedTab: index });
  }

  get isEditing(): boolean {
    return !!this.editSlug;
  }

  get pageTitle(): string {
    return this.isEditing ? 'admin.editProduct' : 'admin.createProduct';
  }

  getCategoryName(cat: Category): string {
    return cat.translations?.find((t) => t.lang === 'es')?.name ?? cat.slug;
  }
}
