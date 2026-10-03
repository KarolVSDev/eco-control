import {
  Component,
  Input,
} from '@angular/core';

import {
  ChartDatum,
} from '../../models/common';


@Component({
  selector: 'app-donut-chart',
  templateUrl: './donut-chart.component.html',
  styleUrls: ['./donut-chart.component.css'],
})
export class DonutChartComponent {

  @Input()
  data: ChartDatum[] = [];


  readonly colors = [
    '#e7194a',
    '#3b82f6',
    '#22c55e',
    '#f59e0b',
    '#ff8a65',
    '#9c27b0',
    '#00bcd4',
    '#ffc107',
    '#795548',
    '#607d8b',
  ];


  // =====================================================
  // TOOLTIP
  // =====================================================

  tooltipVisible = false;

  tooltipX = 0;

  tooltipY = 0;

  tooltipName = '';

  tooltipValue = 0;

  tooltipPercent = '0.0';


  // =====================================================
  // TOTAL
  // =====================================================

  get total(): number {

    return this.data.reduce(
      (
        sum,
        item,
      ) => {
        return (
          sum
          +
          item.value
        );
      },
      0,
    );
  }


  // =====================================================
  // GRADIENTE DO DONUT
  // =====================================================

  get gradient(): string {

    if (
      !this.total
    ) {

      return 'transparent';
    }


    let position = 0;


    const segments =
      this.data.map(
        (
          item,
          index,
        ) => {

          const start =
            position;


          const portion =
            (
              item.value
              /
              this.total
            )
            *
            360;


          position +=
            portion;


          const color =
            this.colors[
              index
              %
              this.colors.length
            ];


          return (
            `${color} `
            +
            `${start}deg `
            +
            `${position}deg`
          );
        },
      );


    return (
      `conic-gradient(`
      +
      `${segments.join(', ')}`
      +
      `)`
    );
  }


  // =====================================================
  // IDENTIFICAR SEGMENTO SOB O MOUSE
  // =====================================================

  onDonutMove(
    event: MouseEvent,
  ): void {

    if (
      !this.total
    ) {

      this.hideTooltip();

      return;
    }


    const target =
      event.currentTarget;


    /*
     * currentTarget é tipado pelo navegador
     * como EventTarget | null.
     *
     * Precisamos garantir que realmente
     * seja um HTMLElement antes de chamar
     * getBoundingClientRect().
     */

    if (
      !(target instanceof HTMLElement)
    ) {

      this.hideTooltip();

      return;
    }


    const rect =
      target
        .getBoundingClientRect();


    const centerX =
      rect.left
      +
      rect.width / 2;


    const centerY =
      rect.top
      +
      rect.height / 2;


    const dx =
      event.clientX
      -
      centerX;


    const dy =
      event.clientY
      -
      centerY;


    const radius =
      Math.sqrt(
        dx * dx
        +
        dy * dy,
      );


    const outerRadius =
      Math.min(
        rect.width,
        rect.height,
      )
      /
      2;


    /*
     * O furo do donut possui
     * aproximadamente metade
     * do raio externo.
     */

    const innerRadius =
      outerRadius
      *
      0.5;


    // Mouse está no furo ou fora do donut.

    if (
      radius < innerRadius
      ||
      radius > outerRadius
    ) {

      this.hideTooltip();

      return;
    }


    /*
     * atan2 começa no eixo X.
     *
     * O conic-gradient começa no topo,
     * então aplicamos +90 graus.
     */

    let angle =
      (
        Math.atan2(
          dy,
          dx,
        )
        *
        180
        /
        Math.PI
      )
      +
      90;


    if (
      angle < 0
    ) {

      angle +=
        360;
    }


    // =================================================
    // DESCOBRIR QUAL FATIA CONTÉM O ÂNGULO
    // =================================================

    let accumulated =
      0;


    for (
      let index = 0;
      index < this.data.length;
      index++
    ) {

      const item =
        this.data[index];


      const segmentAngle =
        (
          item.value
          /
          this.total
        )
        *
        360;


      const segmentEnd =
        accumulated
        +
        segmentAngle;


      const isLast =
        index
        ===
        this.data.length - 1;


      if (
        angle >= accumulated
        &&
        (
          angle < segmentEnd
          ||
          isLast
        )
      ) {

        this.showTooltip(
          event,
          item,
        );

        return;
      }


      accumulated =
        segmentEnd;
    }


    this.hideTooltip();
  }


  // =====================================================
  // MOSTRAR TOOLTIP
  // =====================================================

  private showTooltip(
    event: MouseEvent,
    item: ChartDatum,
  ): void {

    this.tooltipName =
      item.name;


    this.tooltipValue =
      item.value;


    this.tooltipPercent =
      (
        (
          item.value
          /
          this.total
        )
        *
        100
      )
        .toFixed(1);


    this.tooltipVisible =
      true;


    this.moveTooltip(
      event
    );
  }


  // =====================================================
  // POSICIONAR TOOLTIP
  // =====================================================

  moveTooltip(
    event: MouseEvent,
  ): void {

    const tooltipWidth =
      210;


    const tooltipHeight =
      65;


    const offset =
      14;


    let x =
      event.clientX
      +
      offset;


    let y =
      event.clientY
      +
      offset;


    // Evita sair pela direita da tela.

    if (
      x
      +
      tooltipWidth
      >
      window.innerWidth
    ) {

      x =
        event.clientX
        -
        tooltipWidth
        -
        offset;
    }


    // Evita sair pela parte inferior.

    if (
      y
      +
      tooltipHeight
      >
      window.innerHeight
    ) {

      y =
        event.clientY
        -
        tooltipHeight
        -
        offset;
    }


    this.tooltipX =
      x;


    this.tooltipY =
      y;
  }


  // =====================================================
  // ESCONDER TOOLTIP
  // =====================================================

  hideTooltip(): void {

    this.tooltipVisible =
      false;

    this.tooltipName =
      '';

    this.tooltipValue =
      0;

    this.tooltipPercent =
      '0.0';
  }
}