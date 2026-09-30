import {
  Component,
  Input,
} from '@angular/core';

import {
  ChartDatum,
} from '../../models/common';


@Component({
  selector: 'app-delay-bar-chart',
  templateUrl: './delay-bar-chart.component.html',
  styleUrls: ['./delay-bar-chart.component.css'],
})
export class DelayBarChartComponent {

  @Input()
  data: ChartDatum[] = [];


  colors = [
    '#22c55e',
    '#f59e0b',
    '#ff8a65',
    '#e7194a',
  ];


  tooltipVisible = false;

  tooltipX = 0;

  tooltipY = 0;

  tooltipName = '';

  tooltipValue = 0;


  get max(): number {

    return Math.max(
      1,
      ...this.data.map(
        item =>
          item.value
      ),
    );
  }


  showTooltip(
    event: MouseEvent,
    item: ChartDatum,
  ): void {

    this.tooltipName =
      item.name;


    this.tooltipValue =
      item.value;


    this.tooltipVisible =
      true;


    this.moveTooltip(
      event
    );
  }


  moveTooltip(
    event: MouseEvent,
  ): void {

    const width =
      170;


    const height =
      65;


    let x =
      event.clientX + 14;


    let y =
      event.clientY + 14;


    if (
      x + width
      >
      window.innerWidth
    ) {

      x =
        event.clientX
        -
        width
        -
        14;
    }


    if (
      y + height
      >
      window.innerHeight
    ) {

      y =
        event.clientY
        -
        height
        -
        14;
    }


    this.tooltipX =
      x;


    this.tooltipY =
      y;
  }


  hideTooltip(): void {

    this.tooltipVisible =
      false;
  }
}