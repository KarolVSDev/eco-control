import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GapReportRoutingModule } from './gap-report-routing.module';
import { GapReportComponent } from './gap-report.component';

@NgModule({
  declarations: [GapReportComponent],
  imports: [CommonModule, FormsModule, GapReportRoutingModule],
})
export class GapReportModule {}
