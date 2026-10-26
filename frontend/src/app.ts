import { Component, signal } from "@angular/core";
import { PracticeComponent } from "./practice";
import { IconComponent } from "./icon";

@Component({
  selector: "app-root",
  standalone: true,
  imports: [PracticeComponent, IconComponent],
  templateUrl: "./app.html",
  styleUrl: "./home.css",
})
export class AppComponent {
  skipHref = location.pathname + location.search + "#main";
  workspace = window.location.pathname.replace(/\/$/, "") === "/workspace";
  menu = signal(false);
  example = signal(0);

  examples = [
    {
      title: "Design a cache",
      question:
        "How would you keep a product catalog fast without serving stale prices?",
      answer:
        "I would start with a short TTL, then invalidate the cache when a product changes.",
      followup: "What happens if invalidation fails?",
    },
    {
      title: "Design a queue",
      question: "How would you process orders reliably when traffic spikes?",
      answer:
        "I would acknowledge a message only after processing it, and make the consumer idempotent.",
      followup: "How would you handle a message that keeps failing?",
    },
    {
      title: "Scale an API",
      question: "How would you handle a sudden increase in API traffic?",
      answer:
        "I would measure the bottleneck first, then scale stateless workers behind a load balancer.",
      followup: "Which metric would tell you to scale?",
    },
  ];
}
