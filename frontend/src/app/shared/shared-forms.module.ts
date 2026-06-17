import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ReactiveFormsModule } from '@angular/forms';

// PrimeNG form-related modules
import { CheckboxModule } from 'primeng/checkbox';
import { DatePickerModule } from 'primeng/datepicker';
import { FloatLabelModule } from 'primeng/floatlabel';
import { InputGroupModule } from 'primeng/inputgroup';
import { InputGroupAddonModule } from 'primeng/inputgroupaddon';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextModule } from 'primeng/inputtext';
import { MultiSelectModule } from 'primeng/multiselect';
import { SelectModule } from 'primeng/select';
import { ToggleSwitchModule } from 'primeng/toggleswitch';

const FORM_MODULES = [
  FormsModule,
  ReactiveFormsModule,
];

const PRIME_NG_FORMS = [
  CheckboxModule,
  DatePickerModule,
  FloatLabelModule,
  InputGroupModule,
  InputGroupAddonModule,
  InputNumberModule,
  InputTextModule,
  MultiSelectModule,
  SelectModule,
  ToggleSwitchModule,
];

@NgModule({
  imports: [...FORM_MODULES, ...PRIME_NG_FORMS],
  exports: [...FORM_MODULES, ...PRIME_NG_FORMS],
})
export class SharedFormsModule {}
