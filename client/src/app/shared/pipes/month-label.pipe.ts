import {
  Pipe,
  PipeTransform,
} from '@angular/core';

import {
  monthLabel,
} from '../utils/month-label';


@Pipe({
  name: 'monthLabel',
  pure: true,
})
export class MonthLabelPipe
  implements PipeTransform {

  transform(value: unknown): string {
    return monthLabel(value);
  }
}
