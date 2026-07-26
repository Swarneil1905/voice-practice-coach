import { Component, signal, OnInit, OnDestroy } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { IconComponent } from "./icon";
import { api } from "./api";
import type { Room } from "livekit-client";

interface Review {
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
  template: ` <section class="workspace practice">
    <div class="location-row">
      <span>Practice room</span
      ><span class="status-label"
        ><span class="status-dot"></span>Text rehearsal available</span
      >
    </div>
    <div class="page-heading">
      <div>
        <p class="eyebrow">A LITTLE PRACTICE. A CLEARER ANSWER.</p>
        <h1>Make your thinking heard.</h1>
        <p class="lede">
          A quiet place to work through technical decisions, one conversation at
          a time.
        </p>
      </div>
      <span class="edition">01 / PRACTICE</span>
    </div>
    <div class="practice-layout">
      <section class="session-card">
        <div class="session-top">
          <span class="caps">TODAY’S SESSION</span
          ><span class="pill">System design</span>
        </div>
        <h2>{{ scenarios[selected].title }}</h2>
        <p class="session-description">{{ scenarios[selected].description }}</p>
        <div class="session-meta">
          <span><app-icon name="clock" /> 8 minute exercise</span
          ><span><app-icon name="book" /> {{ scenarios[selected].level }}</span>
        </div>
        <div class="waveform" aria-hidden="true">
          @for (h of wave; track $index) {
            <span [style.height.px]="h"></span>
          }
        </div>
        <div class="room-state">
          <span class="outline-dot"></span
          >{{
            started() ? "Your turn to think it through" : "Your space is ready"
          }}
        </div>
        @if (!started()) {
          <button class="primary accent" (click)="started.set(true)">
            Start text rehearsal <app-icon name="arrow" />
          </button>
          <p class="micro">
            {{
              capabilities().voice
                ? "Voice is available below."
                : "Voice sessions will open after LiveKit is connected."
            }}
          </p>
        } @else {
          <div class="prompt-block">
            <span class="caps">COACH’S PROMPT</span>
            <p>{{ scenarios[selected].prompt }}</p>
          </div>
          <label class="sr-only" for="answer">Your answer</label
          ><textarea
            id="answer"
            [(ngModel)]="answer"
            placeholder="Start with the requirements. Explain your choices and their tradeoffs."
            rows="5"
            maxlength="8000"
          ></textarea>
          @if (capabilities().ai_review) {
            <label class="consent-label"
              ><input type="checkbox" [(ngModel)]="useAI" />Include AI feedback
              and send this answer to the configured model provider.</label
            >
          }
          <div class="answer-actions">
            <span class="micro">{{ answer.length }} / 8000 characters</span
            ><button
              class="primary accent"
              [disabled]="busy() || answer.trim().length < 20"
              (click)="review()"
            >
              {{ busy() ? "Reviewing…" : "Review coverage" }}
              <app-icon name="arrow" />
            </button>
          </div>
        }
        @if (capabilities().voice) {
          <div class="voice-controls">
            <label class="consent-label"
              ><input
                type="checkbox"
                [(ngModel)]="voiceConsent"
                [disabled]="voiceState() !== 'idle'"
              />I agree to send microphone audio to LiveKit and configured
              speech and AI providers. No recording is saved by this
              application.</label
            >
            @if (voiceState() === "idle") {
              <button
                class="primary green"
                [disabled]="!voiceConsent"
                (click)="startVoice()"
              >
                <app-icon name="mic" />Start voice rehearsal
              </button>
            } @else {
              <p class="voice-status" role="status">
                {{ voiceState() }} · {{ secondsLeft() }} seconds remaining
              </p>
              <button class="secondary" (click)="stopVoice()">
                End voice session
              </button>
            }
          </div>
        }
        @if (error()) {
          <p class="error" role="alert">{{ error() }}</p>
        }
      </section>
      <aside class="session-sidebar">
        <div class="section-label">
          <h3>What you’ll work on</h3>
          <span>03</span>
        </div>
        @for (
          point of scenarios[selected].points;
          track point;
          let i = $index
        ) {
          <div class="learning-point">
            <span class="index">0{{ i + 1 }}</span>
            <div>
              <h4>{{ point }}</h4>
              <p>{{ descriptions[i] }}</p>
            </div>
          </div>
        }
        <div class="coach-note">
          <span class="caps">A NOTE BEFORE YOU BEGIN</span>
          <p>
            There is rarely one right architecture. Explain what you would
            choose, and what would change your mind.
          </p>
          <span class="note-signature">Your reasoning matters.</span>
        </div>
        <div class="privacy-note">
          <app-icon name="info" />
          <p>
            Answers are not saved by this application. Baseline reviews run on
            the local API. AI feedback and voice require your consent before
            using external providers.
          </p>
        </div>
      </aside>
    </div>
    @if (result()) {
      <section class="review-panel" aria-live="polite">
        <div class="section-label">
          <h3>Your coverage review</h3>
          <span>{{
            result()!.ai_feedback ? "AI assisted review" : "Rule based baseline"
          }}</span>
        </div>
        <div class="coverage-grid">
          @for (item of result()!.coverage; track item.title) {
            <article>
              <span class="pill" [class.positive]="item.covered">{{
                item.covered ? "Mentioned" : "Explore next"
              }}</span>
              <h4>{{ item.title }}</h4>
              <p>{{ item.evidence }}</p>
            </article>
          }
        </div>
        @if (result()!.ai_feedback) {
          <p class="ai-feedback">{{ result()!.ai_feedback }}</p>
        }
        <p class="follow-up">{{ result()!.next_question }}</p>
        <p class="micro">{{ result()!.disclaimer }}</p>
      </section>
    }
    <section class="practice-library">
      <div class="section-label">
        <h3>Find your next conversation</h3>
        <span>Three focused scenarios</span>
      </div>
      <div class="scenario-grid">
        @for (s of scenarios; track s.id; let i = $index) {
          <button
            class="scenario"
            [class.selected]="selected === i"
            (click)="select(i)"
          >
            <span class="scenario-number">0{{ i + 1 }}</span>
            <h4>{{ s.title }}</h4>
            <p>{{ s.level }} · 8 minutes</p>
            <app-icon [name]="selected === i ? 'check' : 'arrow'" />
          </button>
        }
      </div>
    </section>
  </section>`,
})
export class PracticeComponent implements OnInit, OnDestroy {
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
    try {
      this.capabilities.set(
        await api<{ voice: boolean; ai_review: boolean }>("capabilities"),
      );
    } catch (e) {
      this.error.set((e as Error).message);
    }
  }
  ngOnDestroy() {
    this.stopVoice();
  }
  async startVoice() {
    const generation = ++this.voiceGeneration;
    this.error.set("");
    this.voiceState.set("Connecting");
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

  started = signal(false);
  busy = signal(false);
  error = signal("");
  result = signal<Review | null>(null);
  answer = "";
  selected = 0;
  descriptions = [
    "Frame the problem before proposing a solution.",
    "Compare practical choices and their consequences.",
    "Make the failure path as clear as the happy path.",
  ];
  wave = Array.from(
    { length: 43 },
    (_, i) =>
      12 +
      Math.round(
        (1 - Math.abs(i - 21) / 22) * (18 + 35 * Math.abs(Math.sin(i * 1.83))),
      ),
  );
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
    this.stopVoice();
    this.selected = i;
    this.started.set(false);
    this.result.set(null);
    this.answer = "";
    this.error.set("");
  }
  async review() {
    this.busy.set(true);
    this.error.set("");
    try {
      this.result.set(
        await api<Review>("practice/review", {
          scenario: this.scenarios[this.selected].id,
          answer: this.answer,
          mode: this.useAI ? "ai" : "baseline",
          consent: this.useAI,
        }),
      );
    } catch (e) {
      this.error.set((e as Error).message);
    } finally {
      this.busy.set(false);
    }
  }
}
