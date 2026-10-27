import { Component, signal, OnInit, OnDestroy } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { IconComponent } from "./icon";
import { api } from "./api";
import type { Room } from "livekit-client";

interface Review {
  practice_plan?: {
    topic: string;
    title: string;
    exercise: string;
    example: string;
    priority: string;
  }[];
  comparison?: {
    before_topics: number;
    after_topics: number;
    new_topics: string[];
    lost_topics: string[];
    word_change: number;
    answer_changed: boolean;
    meaning: string;
  } | null;
  speaking_estimate?: {
    min_seconds: number;
    max_seconds: number;
    basis: string;
  };
  coverage: { title: string; covered: boolean; evidence: string }[];
  next_question: string;
  disclaimer: string;
  word_count: number;
  ai_feedback?: string;
  mode?: string;
}
@Component({
  selector: "practice-room",
  standalone: true,
  imports: [FormsModule, IconComponent],
  templateUrl: "./practice.html",
})
export class PracticeComponent implements OnInit, OnDestroy {
  previousAnswer = "";
  transcript = signal("");
  revise() {
    if (!this.result()) return;
    this.previousAnswer = this.reviewedAnswer;
    this.answer = this.reviewedAnswer;
    this.result.set(null);
    this.savedNotice.set("");
    document
      .querySelector("#answer")
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
  }
  useTranscript() {
    this.answer = this.transcript();
    this.result.set(null);
    this.previousAnswer = "";
    this.savedNotice.set("");
    this.stopVoice();
  }
  exportPlan() {
    const review = this.result();
    if (!review) return;
    this.exportReview({
      schema_version: 2,
      scenario: this.scenarios[this.selected].title,
      original_answer: this.previousAnswer || null,
      revised_answer: this.reviewedAnswer,
      next_practice: review.practice_plan,
      comparison: review.comparison,
      review,
    });
  }
  ready = signal(false);
  connecting = signal(true);
  capabilities = signal({ voice: false, ai_review: false });
  useAI = false;
  voiceConsent = false;
  voiceState = signal("idle");
  secondsLeft = signal(480);
  private room?: Room;
  private timer?: ReturnType<typeof setInterval>;
  private audioElements: HTMLMediaElement[] = [];
  private voiceGeneration = 0;
  async ngOnInit() {
    const scenario = Number(
      new URLSearchParams(location.search).get("scenario") || 0,
    );
    if (
      Number.isInteger(scenario) &&
      scenario >= 0 &&
      scenario < this.scenarios.length
    )
      this.selected = scenario;
    try {
      const entries = JSON.parse(
        localStorage.getItem("voice-practice-reviews") || "[]",
      );
      if (Array.isArray(entries))
        this.history.set(
          entries
            .filter(
              (x) =>
                x &&
                typeof x.title === "string" &&
                typeof x.answer === "string" &&
                x.review &&
                Array.isArray(x.review.coverage),
            )
            .slice(0, 20),
        );
    } catch {}
    await this.loadCapabilities();
  }
  async loadCapabilities() {
    this.connecting.set(true);
    this.ready.set(false);
    this.error.set("");
    try {
      this.capabilities.set(
        await api<{ voice: boolean; ai_review: boolean }>("capabilities"),
      );
      this.ready.set(true);
    } catch (e) {
      this.error.set((e as Error).message);
    } finally {
      this.connecting.set(false);
    }
  }
  ngOnDestroy() {
    this.stopVoice();
  }
  async startVoice() {
    const generation = ++this.voiceGeneration;
    this.error.set("");
    this.voiceState.set("Connecting");
    this.transcript.set("");
    try {
      const ticket = await api<{
        url: string;
        token: string;
        max_session_seconds: number;
      }>("voice/token", {
        scenario: this.scenarios[this.selected].id,
        consent: this.voiceConsent,
      });
      if (generation !== this.voiceGeneration) return;
      const { Room, RoomEvent, Track } = await import("livekit-client");
      const room = new Room();
      this.room = room;
      room.on(RoomEvent.DataReceived, (payload, participant, _kind, topic) => {
        if (
          topic !== "practice-transcript" ||
          !participant?.isAgent ||
          payload.length > 40000
        )
          return;
        try {
          const data = JSON.parse(new TextDecoder().decode(payload));
          if (typeof data.text === "string")
            this.transcript.set(data.text.slice(0, 8000));
        } catch {}
      });
      room.on(RoomEvent.TrackSubscribed, (track) => {
        if (track.kind === Track.Kind.Audio) {
          const el = track.attach();
          document.body.appendChild(el);
          this.audioElements.push(el);
        }
      });
      room.on(RoomEvent.Disconnected, () => this.stopVoice());
      await room.connect(ticket.url, ticket.token);
      if (generation !== this.voiceGeneration) {
        await room.disconnect();
        return;
      }
      await room.localParticipant.setMicrophoneEnabled(true);
      await room.startAudio();
      if (generation !== this.voiceGeneration) {
        await room.disconnect();
        return;
      }
      this.voiceState.set("Microphone active");
      const deadline = Date.now() + ticket.max_session_seconds * 1000;
      this.timer = setInterval(() => {
        this.secondsLeft.set(
          Math.max(0, Math.ceil((deadline - Date.now()) / 1000)),
        );
        if (this.secondsLeft() === 0) this.stopVoice();
      }, 1000);
    } catch (e) {
      this.stopVoice();
      this.error.set("Voice could not start. " + (e as Error).message);
    }
  }
  stopVoice() {
    ++this.voiceGeneration;
    if (this.timer) clearInterval(this.timer);
    this.timer = undefined;
    const room = this.room;
    this.room = undefined;
    room?.removeAllListeners();
    void room?.disconnect();
    this.audioElements.forEach((el) => el.remove());
    this.audioElements = [];
    this.voiceState.set("idle");
    this.secondsLeft.set(480);
  }

  busy = signal(false);
  error = signal("");
  result = signal<Review | null>(null);
  answer = "";
  reviewedAnswer = "";
  selected = 0;
  view = signal<"studio" | "history">("studio");
  savedNotice = signal("");
  history = signal<
    {
      id: string;
      title: string;
      date: string;
      answer: string;
      review: Review;
    }[]
  >([]);
  saveReview() {
    const review = this.result();
    if (!review) return;
    const entries = [
      {
        id: crypto.randomUUID(),
        title: this.scenarios[this.selected].title,
        date: new Date().toISOString(),
        answer: this.reviewedAnswer,
        review,
      },
      ...this.history(),
    ].slice(0, 20);
    try {
      localStorage.setItem("voice-practice-reviews", JSON.stringify(entries));
      this.history.set(entries);
      this.savedNotice.set("Saved on this device.");
    } catch {
      this.savedNotice.set(
        "Browser storage is unavailable. Export your review instead.",
      );
    }
  }
  deleteReview(id: string) {
    const entries = this.history().filter((x) => x.id !== id);
    try {
      localStorage.setItem("voice-practice-reviews", JSON.stringify(entries));
      this.history.set(entries);
    } catch {
      this.error.set("Could not update browser storage.");
    }
  }
  exportReview(data: unknown) {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "practice-review.json";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  covered(review: Review) {
    return review.coverage.filter((x) => x.covered).length;
  }
  displayDate(date: string) {
    return new Date(date).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    });
  }

  descriptions = [
    "Frame the problem before proposing a solution.",
    "Compare practical choices and their consequences.",
    "Make the failure path as clear as the happy path.",
  ];
  scenarios = [
    {
      id: "cache",
      title: "When a cache becomes a problem",
      description:
        "Design a product catalog that stays fast without showing items that are no longer available.",
      level: "Intermediate",
      prompt:
        "Your catalog serves 10,000 products. Inventory changes every few seconds. How would you cache recommendations while preventing a customer from purchasing an unavailable item?",
      points: [
        "Freshness and TTL",
        "Invalidation and consistency",
        "Failure and recovery",
      ],
    },
    {
      id: "queue",
      title: "A queue that never loses an order",
      description:
        "Think through retries, duplicate events, and a worker that can fail halfway through a job.",
      level: "Intermediate",
      prompt:
        "A payment webhook can arrive more than once, and your worker can crash after creating an order. How would you prevent duplicates and recover safely?",
      points: ["Idempotency", "Retry strategy", "Failure and recovery"],
    },
    {
      id: "scale",
      title: "The morning your traffic doubles",
      description:
        "Find the bottleneck before you add another server. Build a system you can understand under load.",
      level: "Foundations",
      prompt:
        "Response time rises as your traffic doubles. How would you identify the bottleneck, distribute requests, and verify that your fix works?",
      points: ["Measurement", "Load distribution", "Failure and recovery"],
    },
  ];
  select(i: number) {
    if (this.busy()) return;
    this.stopVoice();
    this.selected = i;
    this.savedNotice.set("");
    this.result.set(null);
    this.answer = "";
    this.previousAnswer = "";
    this.transcript.set("");
    this.error.set("");
  }
  async review() {
    if (!this.ready() || this.busy()) return;
    this.savedNotice.set("");
    this.reviewedAnswer = this.answer;
    this.result.set(null);
    this.busy.set(true);
    this.error.set("");
    try {
      this.result.set(
        await api<Review>("practice/review", {
          scenario: this.scenarios[this.selected].id,
          answer: this.answer,
          mode: this.useAI ? "ai" : "baseline",
          consent: this.useAI,
          previous_answer: this.previousAnswer || undefined,
        }),
      );
    } catch (e) {
      this.error.set((e as Error).message);
    } finally {
      this.busy.set(false);
    }
  }
}
