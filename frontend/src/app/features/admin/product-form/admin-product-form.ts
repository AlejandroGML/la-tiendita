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
import type { Product, ProductVariant } from '../../../shared/models/product.model';
import type { Category } from '../../../shared/models/category.model';
import { AdminProductService } from '../../../core/services/admin-product.service';
import type {
  CreateProductPayload,
  VariantPayload,
} from '../../../core/services/admin-product.service';

function esNameRequired(group: AbstractControl): ValidationErrors | null {
  const translations = group.get('translations') as FormArray;
  if (!translations) return null;
  const esGroup = translations.controls.find(
    (ctrl) => ctrl.get('lang')?.value === 'es',
  );
  const name = esGroup?.get('name')?.value?.trim();
  return name ? null : { esNameRequired: true };
}

export interface VariantFormEntry {
  id?: string;
  size: string | null;
  color: string | null;
  color_hex: string | null;
  stock: number;
  sku: string;
}

function emptyVariant(): VariantFormEntry {
  return { size: null, color: null, color_hex: null, stock: 1, sku: '' };
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

  /** Dynamic variant rows */
  readonly variants = signal<VariantFormEntry[]>([]);

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
        brand: [''],
        condition: ['good'],
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

  ngOnInit(): void {
    this.loadCategories();
    this.editSlug = this.route.snapshot.paramMap.get('slug');

    if (this.editSlug) {
      this.loadProduct(this.editSlug);
    } else {
      // New product: start with one empty variant row
      this.variants.set([emptyVariant()]);
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();

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
          /* categories are optional */
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
          this.messageService.add({
            severity: 'error',
            detail: 'catalog.error',
            life: 3000,
          });
        },
      });
  }

  private populateForm(product: Product): void {
    this.form.patchValue({
      price: product.price,
      category_id: product.category_id,
      brand: product.brand,
      condition: product.condition,
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

    // Populate variants
    if (product.variants?.length) {
      this.variants.set(
        product.variants.map((v: ProductVariant) => ({
          id: v.id,
          size: v.size,
          color: v.color,
          color_hex: v.color_hex,
          stock: v.stock,
          sku: v.sku,
        })),
      );
    } else {
      this.variants.set([emptyVariant()]);
    }

    // Show existing images as previews
    if (product.image_urls?.length) {
      this.imagePreviewUrls.set([...product.image_urls]);
    }
  }

  // ── Variant management ──

  addVariant(): void {
    this.variants.update((arr) => [...arr, emptyVariant()]);
  }

  removeVariant(index: number): void {
    this.variants.update((arr) => arr.filter((_, i) => i !== index));
  }

  updateVariant(index: number, field: keyof VariantFormEntry, value: unknown): void {
    this.variants.update((arr) =>
      arr.map((v, i) => (i === index ? { ...v, [field]: value } : v)),
    );
  }

  // ── Image handling ──

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const files = input.files;
    if (!files?.length) return;

    const newFiles: File[] = [];
    const newPreviews: string[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files.item(i);
      if (!file) continue;

      const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
      if (!validTypes.includes(file.type)) continue;

      if (file.size > 5 * 1024 * 1024) continue;

      newFiles.push(file);
      newPreviews.push(URL.createObjectURL(file));
    }

    if (newFiles.length > 0) {
      this.imageFiles.update((prev) => [...prev, ...newFiles]);
      this.imagePreviewUrls.update((prev) => [...prev, ...newPreviews]);
    }

    input.value = '';
  }

  removeImage(index: number): void {
    const urls = this.imagePreviewUrls();
    if (urls[index]?.startsWith('blob:')) {
      URL.revokeObjectURL(urls[index]);
    }

    this.imagePreviewUrls.update((prev) => prev.filter((_, i) => i !== index));
    this.imageFiles.update((prev) => prev.filter((_, i) => i !== index));
  }

  // ── Submit ──

  async onSubmit(): Promise<void> {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.submitting.set(true);

    const formValue = this.form.value;

    // Upload new images
    let imageUrls: string[] = [];

    for (const url of this.imagePreviewUrls()) {
      if (!url.startsWith('blob:')) {
        imageUrls.push(url);
      }
    }

    const filesToUpload = this.imageFiles();
    if (filesToUpload.length > 0) {
      try {
        const uploadResults = await Promise.all(
          filesToUpload.map((file) => {
            const formData = new FormData();
            formData.append('data', file);
            return this.http
              .post<{ image_url: string; thumbnail_url: string }>(
                '/api/upload',
                formData,
              )
              .toPromise();
          }),
        );

        for (const result of uploadResults) {
          if (result?.image_url) {
            imageUrls.push(result.image_url);
          }
        }
      } catch {
        this.messageService.add({
          severity: 'error',
          detail: 'Error al subir imágenes',
          life: 4000,
        });
        this.submitting.set(false);
        return;
      }
    }

    // Build variant payload
    const variantsPayload: VariantPayload[] = this.variants().map((v) => ({
      size: v.size || undefined,
      color: v.color || undefined,
      color_hex: v.color_hex || undefined,
      stock: v.stock ?? 1,
      sku: v.sku || undefined,
    }));

    const payload: CreateProductPayload = {
      price: formValue.price,
      category_id: formValue.category_id,
      brand: formValue.brand || undefined,
      condition: formValue.condition,
      image_urls: imageUrls,
      translations: formValue.translations
        .filter((t: { name: string }) => t.name?.trim())
        .map((t: { lang: string; name: string; description: string }) => ({
          lang: t.lang,
          name: t.name.trim(),
          description: t.description?.trim() || undefined,
        })),
      variants: variantsPayload,
    };

    const request = this.editSlug
      ? this.adminProductService.updateProduct(this.editSlug, payload)
      : this.adminProductService.createProduct(payload);

    request.pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          detail: 'admin.productSaved',
          life: 3000,
        });
        this.router.navigate(['/admin/productos']);
      },
      error: () => {
        this.submitting.set(false);
        this.messageService.add({
          severity: 'error',
          detail: 'catalog.error',
          life: 3000,
        });
      },
    });
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
