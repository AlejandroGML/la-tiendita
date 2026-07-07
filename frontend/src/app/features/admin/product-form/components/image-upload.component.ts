import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  OnDestroy,
  Output,
} from '@angular/core';

@Component({
  selector: 'app-image-upload',
  templateUrl: './image-upload.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class ImageUploadComponent implements OnDestroy {
  @Input() imageFiles: File[] = [];
  @Input() existingUrls: string[] = [];
  @Input() submitting = false;
  @Output() filesChanged = new EventEmitter<File[]>();

  /** Internal blob URLs created from file additions */
  blobUrls: string[] = [];

  get previewUrls(): string[] {
    return [...this.existingUrls, ...this.blobUrls];
  }

  get existingCount(): number {
    return this.existingUrls.length;
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

      const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
      if (!validTypes.includes(file.type)) continue;

      if (file.size > 5 * 1024 * 1024) continue;

      newFiles.push(file);
      newPreviews.push(URL.createObjectURL(file));
    }

    if (newFiles.length > 0) {
      this.imageFiles = [...this.imageFiles, ...newFiles];
      this.blobUrls = [...this.blobUrls, ...newPreviews];
      this.filesChanged.emit([...this.imageFiles]);
    }

    input.value = '';
  }

  removeImage(index: number): void {
    if (index < this.existingCount) {
      // Existing server URLs cannot be removed from here.
      // Parent handles this when wired.
      return;
    }

    const fileIndex = index - this.existingCount;

    if (this.blobUrls[fileIndex]?.startsWith('blob:')) {
      URL.revokeObjectURL(this.blobUrls[fileIndex]);
    }

    this.blobUrls = this.blobUrls.filter((_, i) => i !== fileIndex);
    this.imageFiles = this.imageFiles.filter((_, i) => i !== fileIndex);
    this.filesChanged.emit([...this.imageFiles]);
  }

  ngOnDestroy(): void {
    for (const url of this.blobUrls) {
      URL.revokeObjectURL(url);
    }
  }
}
