import { NgModule } from '@angular/core';
import { CurrencyPipe } from './pipes/currency.pipe';
import { SvgIconPipe } from './pipes/svg-icon.pipe';

@NgModule({
  declarations: [CurrencyPipe, SvgIconPipe],
  exports: [CurrencyPipe, SvgIconPipe],
})
export class SharedPipesModule {}
