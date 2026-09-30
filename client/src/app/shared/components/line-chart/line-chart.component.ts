import {
  Component,
  Input,
} from '@angular/core';

import {
  ChartDatum,
} from '../../models/common';


@Component({
  selector: 'app-line-chart',
  templateUrl: './line-chart.component.html',
  styleUrls: ['./line-chart.component.css'],
})
export class LineChartComponent {

  @Input()
  data: ChartDatum[] = [];


  hoverIndex:
    number | null = null;


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


  pointX(
    index: number,
  ): number {

    return (
      30
      +
      (
        index
        *
        (
          520
          /
          Math.max(
            1,
            this.data.length - 1,
          )
        )
      )
    );
  }


  pointY(
    value: number,
  ): number {

    return (
      190
      -
      (
        value
        /
        this.max
        *
        150
      )
    );
  }


  get points(): string {

    if (
      !this.data.length
    ) {

      return '';
    }


    return this.data
      .map(
        (
          item,
          index,
        ) =>
          `
            ${this.pointX(index)},
            ${this.pointY(item.value)}
          `
      )
      .join(' ');
  }


  get hoverX(): number {

    if (
      this.hoverIndex === null
    ) {

      return 0;
    }


    return this.pointX(
      this.hoverIndex
    );
  }


  showTooltip(
    event: MouseEvent,
    item: ChartDatum,
    index: number,
  ): void {

    this.hoverIndex =
      index;


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

    const width = 150;

    const height = 65;


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


    this.tooltipX = x;

    this.tooltipY = y;
  }


  hideTooltip(): void {

    this.tooltipVisible =
      false;

    this.hoverIndex =
      null;
  }
}