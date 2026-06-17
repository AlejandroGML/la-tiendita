import { NgModule } from '@angular/core';
import { CurrencyPipe } from './pipes/currency.pipe';

@NgModule({
  declarations: [CurrencyPipe],
  exports: [CurrencyPipe],
})
export class SharedPipesModule {}
