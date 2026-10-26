import { AfterViewInit, Directive, ElementRef, HostListener, Input, OnChanges, OnDestroy } from '@angular/core';

@Directive({ selector: 'textarea[appNoteAutoResize]' })
export class NoteAutoResizeDirective implements AfterViewInit, OnChanges, OnDestroy {
  @Input() appNoteAutoResize = '';
  private frame?: number;

  constructor(private readonly element: ElementRef<HTMLTextAreaElement>) {}

  ngAfterViewInit(): void { this.scheduleResize(); }
  ngOnChanges(): void { this.scheduleResize(); }

  private scheduleResize(): void {
    if (this.frame !== undefined) cancelAnimationFrame(this.frame);
    this.frame = requestAnimationFrame(() => {
      this.frame = undefined;
      this.resize();
    });
  }

  @HostListener('input')
  @HostListener('window:resize')
  resize(): void {
    const textarea = this.element.nativeElement;
    textarea.style.height = '0px';
    const contentHeight = textarea.scrollHeight + textarea.offsetHeight - textarea.clientHeight;
    textarea.style.height = `${Math.min(130, Math.max(42, contentHeight))}px`;
    textarea.style.overflowY = contentHeight > 130 ? 'auto' : 'hidden';
  }

  ngOnDestroy(): void {
    if (this.frame !== undefined) cancelAnimationFrame(this.frame);
  }
}
