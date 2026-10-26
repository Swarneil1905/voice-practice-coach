import { Component } from "@angular/core";
import { PracticeComponent } from "./practice";
@Component({
  selector: "app-root",
  standalone: true,
  imports: [PracticeComponent],
  template: `<a class="skip-link" href="#workspace">Skip to workspace</a>
    <main id="workspace"><practice-room /></main>`,
})
export class AppComponent {}
