import { Component, inject, OnInit, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { MessageService } from 'primeng/api';

interface Category {
  id: number;
  slug: string;
  name: string;
  image_url?: string;
  translations?: { lang: string; name: string }[];
}

@Component({
  selector: 'app-admin-categories',
  templateUrl: './admin-categories.html',
  standalone: false,
  providers: [MessageService],
})
export class AdminCategories implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly messageService = inject(MessageService);

  readonly categories = signal<Category[]>([]);
  readonly loading = signal(false);
  readonly error = signal(false);

  // Modal state
  dialogVisible = false;
  editingCategory: Category | null = null;
  saving = signal(false);

  // Form fields
  formSlug = '';
  formImageUrl = '';
  formNameEs = '';
  formNameEn = '';
  formNameSv = '';

  ngOnInit(): void {
    this.loadCategories();
  }

  loadCategories(): void {
    this.loading.set(true);
    this.error.set(false);

    this.http.get<Category[]>('/api/v1/categories', { params: { lang: 'es' } }).subscribe({
      next: (data) => {
        this.categories.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.categories.set([]);
        this.loading.set(false);
        this.error.set(true);
      },
    });
  }

  // ── Create ──

  openCreate(): void {
    this.editingCategory = null;
    this.formSlug = '';
    this.formImageUrl = '';
    this.formNameEs = '';
    this.formNameEn = '';
    this.formNameSv = '';
    this.dialogVisible = true;
  }

  // ── Edit ──

  openEdit(cat: Category): void {
    this.editingCategory = cat;
    this.formSlug = cat.slug;
    this.formImageUrl = cat.image_url || '';
    this.formNameEs = cat.name || '';
    this.formNameEn = '';
    this.formNameSv = '';
    // Fetch full translations for edit
    this.http.get<Category>(`/api/v1/admin/categories/${cat.id}`).subscribe({
      next: (full) => {
        if (full.translations) {
          for (const t of full.translations) {
            if (t.lang === 'en') this.formNameEn = t.name;
            else if (t.lang === 'sv') this.formNameSv = t.name;
            else if (t.lang === 'es') this.formNameEs = t.name;
          }
        }
      },
      error: () => { /* keep current values */ },
    });
    this.dialogVisible = true;
  }

  closeDialog(): void {
    this.dialogVisible = false;
    this.editingCategory = null;
  }

  // ── Save (create or update) ──

  saveCategory(): void {
    if (!this.formSlug.trim() || !this.formNameEs.trim()) {
      this.messageService.add({ severity: 'warn', detail: 'Slug y nombre en español son obligatorios', life: 3000 });
      return;
    }

    const payload = {
      slug: this.formSlug.trim(),
      image_url: this.formImageUrl.trim() || null,
      translations: [
        { lang: 'es', name: this.formNameEs.trim() },
        { lang: 'en', name: this.formNameEn.trim() || this.formNameEs.trim() },
        { lang: 'sv', name: this.formNameSv.trim() || this.formNameEs.trim() },
      ],
    };

    this.saving.set(true);

    const request = this.editingCategory
      ? this.http.put(`/api/v1/admin/categories/${this.editingCategory.id}`, payload)
      : this.http.post('/api/v1/admin/categories', payload);

    request.subscribe({
      next: () => {
        this.saving.set(false);
        this.closeDialog();
        this.loadCategories();
        this.messageService.add({
          severity: 'success',
          detail: this.editingCategory ? 'Categoría actualizada' : 'Categoría creada',
          life: 3000,
        });
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err?.error?.detail || 'Error al guardar categoría';
        this.messageService.add({ severity: 'error', detail, life: 4000 });
      },
    });
  }

  // ── Delete ──

  deleteCategory(cat: Category): void {
    if (!confirm(`¿Eliminar categoría "${cat.name}"?`)) return;
    this.http.delete(`/api/v1/admin/categories/${cat.id}`).subscribe({
      next: () => {
        this.loadCategories();
        this.messageService.add({ severity: 'success', detail: `Categoría "${cat.name}" eliminada`, life: 3000 });
      },
      error: (err) => {
        const detail = err?.error?.detail || 'Error al eliminar categoría';
        this.messageService.add({ severity: 'error', detail, life: 4000 });
      },
    });
  }
}
