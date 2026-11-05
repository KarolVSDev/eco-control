import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { GapReportComponent } from './gap-report.component';

const routes: Routes = [{ path: '', component: GapReportComponent }];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class GapReportRoutingModule {}
