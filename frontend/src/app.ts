import { Component, signal } from "@angular/core";
import { PracticeComponent } from "./practice";
import { DesignComponent } from "./design";
@Component({
  selector: "app-root",
  standalone: true,
  imports: [PracticeComponent, DesignComponent],
  template: ` <a class="skip-link" href="#workspace">Skip to workspace</a>
    <header class="global-header">
      <a class="wordmark" href="#home" (click)="notes.set(false)"
        ><span class="brand-mark"><i></i><i></i><i></i></span>Voice<span
          class="studio-label"
          >PRACTICE COACH</span
        ></a
      >
      <nav aria-label="Workspace navigation">
        <a
          href="#home"
          (click)="notes.set(false)"
          [class.active]="!notes()"
          [attr.aria-current]="!notes() ? 'page' : null"
          >Practice workspace</a
        ><a
          href="#design"
          (click)="notes.set(true)"
          [class.active]="notes()"
          [attr.aria-current]="notes() ? 'page' : null"
          >Design & system notes</a
        >
      </nav>
      <span class="design-link">PORTFOLIO DEMO</span>
    </header>
    <main id="workspace" tabindex="-1">
      @if (notes()) {
        <design-notes />
      } @else {
        <practice-room />
      }
    </main>
    <footer class="global-footer">
      <span>Built by Swarneil Pradhan</span
      ><span>Original interface · Public demo</span
      ><a href="#design" (click)="notes.set(true)">Research & implementation</a>
    </footer>`,
})
export class AppComponent {
  notes = signal(location.hash === "#design");
  constructor() {
    window.addEventListener("hashchange", () =>
      this.notes.set(location.hash === "#design"),
    );
  }
}
