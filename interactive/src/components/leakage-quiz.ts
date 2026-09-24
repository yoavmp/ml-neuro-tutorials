// Production activity: Exercise 10's "Which steps must not see the test
// participants?" multi-selection quiz. Pure DOM/CSS/ARIA -- no Plotly, no
// network call beyond the config/data fetch main.ts already performs, and no
// client-side persistence: refreshing the page always restores the untouched
// initial state.
//
// Interaction: any number of checkboxes may be selected before "Check
// answer" is pressed. Pressing it reveals, per option, whether it was
// correctly selected, incorrectly selected, or a correct option the student
// missed, plus that option's own feedback sentence. Only an exact match (every
// correct option selected, no incorrect option selected) shows the
// success/nuance text from the data file. "Try again" clears every mark and
// selection back to the initial state.

import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { MultiSelectQuizConfig } from "../config";
import { parseLeakageQuizData, type LeakageQuizData } from "../leakage-quiz-data";

type Mark = "correct" | "incorrect" | "missed" | null;

function mount(args: MountArgs<MultiSelectQuizConfig, LeakageQuizData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  let checked = false;

  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  const fieldset = document.createElement("fieldset");
  fieldset.className = "widget-quiz-fieldset";
  const legend = document.createElement("legend");
  legend.className = "widget-quiz-question";
  legend.textContent = data.question;
  fieldset.appendChild(legend);

  interface OptionRow {
    id: string;
    input: HTMLInputElement;
    row: HTMLDivElement;
    feedback: HTMLParagraphElement;
    mark: HTMLSpanElement;
  }
  const rows: OptionRow[] = [];
  const rowById = new Map<string, OptionRow>();

  for (const option of data.options) {
    const row = document.createElement("div");
    row.className = "widget-checkbox widget-quiz-option";
    row.setAttribute("data-testid", `quiz-option-${option.id}`);

    const label = document.createElement("label");
    const inputId = `quiz-checkbox-${option.id}`;
    label.setAttribute("for", inputId);

    const input = document.createElement("input");
    input.type = "checkbox";
    input.id = inputId;
    input.setAttribute("data-testid", inputId);
    input.setAttribute(
      "aria-describedby",
      `quiz-mark-${option.id} quiz-feedback-${option.id}`,
    );

    const text = document.createElement("span");
    text.textContent = option.text;

    label.append(input, text);
    row.appendChild(label);

    const mark = document.createElement("span");
    mark.className = "widget-quiz-mark";
    mark.setAttribute("data-testid", `quiz-mark-${option.id}`);
    mark.hidden = true;
    row.appendChild(mark);

    const feedback = document.createElement("p");
    feedback.className = "widget-quiz-feedback";
    feedback.setAttribute("data-testid", `quiz-feedback-${option.id}`);
    feedback.textContent = option.feedback;
    feedback.hidden = true;
    row.appendChild(feedback);

    fieldset.appendChild(row);
    const entry: OptionRow = { id: option.id, input, row, feedback, mark };
    rows.push(entry);
    rowById.set(option.id, entry);
  }
  container.appendChild(fieldset);

  const actionRow = document.createElement("div");
  actionRow.className = "widget-controls";
  const checkBtn = document.createElement("button");
  checkBtn.type = "button";
  checkBtn.textContent = "Check answer";
  checkBtn.setAttribute("data-testid", "quiz-check-button");
  const resetBtn = document.createElement("button");
  resetBtn.type = "button";
  resetBtn.textContent = "Try again";
  resetBtn.setAttribute("data-testid", "quiz-reset-button");
  resetBtn.hidden = true;
  actionRow.append(checkBtn, resetBtn);
  container.appendChild(actionRow);

  const outcome = document.createElement("p");
  outcome.className = "widget-stats";
  outcome.setAttribute("role", "status");
  outcome.setAttribute("aria-live", "polite");
  outcome.setAttribute("data-testid", "quiz-outcome");
  container.appendChild(outcome);

  const successPanel = document.createElement("div");
  successPanel.className = "widget-quiz-success";
  successPanel.setAttribute("data-testid", "quiz-success");
  successPanel.hidden = true;
  const successText = document.createElement("p");
  successText.textContent = data.successFeedback;
  const nuanceText = document.createElement("p");
  nuanceText.className = "widget-note";
  nuanceText.textContent = data.nuance;
  successPanel.append(successText, nuanceText);
  container.appendChild(successPanel);

  function markLabel(mark: Mark): string {
    if (mark === "correct") return "Correct.";
    if (mark === "incorrect") return "Not correct.";
    if (mark === "missed") return "Missed -- this should have been selected.";
    return "";
  }

  function render(): void {
    for (const [i, option] of data.options.entries()) {
      const row = rows[i]!;
      row.row.classList.remove("is-correct", "is-incorrect", "is-missed");
      if (!checked) {
        row.mark.hidden = true;
        row.mark.textContent = "";
        row.feedback.hidden = true;
        continue;
      }
      const selected = row.input.checked;
      let mark: Mark = null;
      if (option.correct && selected) mark = "correct";
      else if (!option.correct && selected) mark = "incorrect";
      else if (option.correct && !selected) mark = "missed";

      if (mark) row.row.classList.add(`is-${mark}`);
      row.mark.hidden = mark === null;
      row.mark.textContent = markLabel(mark);
      row.feedback.hidden = false;
    }

    checkBtn.disabled = checked;
    resetBtn.hidden = !checked;
    for (const row of rows) row.input.disabled = checked;

    if (!checked) {
      outcome.textContent = "";
      successPanel.hidden = true;
      return;
    }

    const allCorrectSelected = data.options.every((o) => !o.correct || rowById.get(o.id)!.input.checked);
    const anyIncorrectSelected = data.options.some((o) => !o.correct && rowById.get(o.id)!.input.checked);
    const exact = allCorrectSelected && !anyIncorrectSelected;

    successPanel.hidden = !exact;
    outcome.textContent = exact
      ? "Fully correct -- every option you needed is selected, with no extra ones."
      : "Not fully correct yet. Review the marked answers below, then try again.";

    container.dataset.quizOutcome = exact ? "correct" : "incorrect";
  }

  checkBtn.addEventListener("click", () => {
    checked = true;
    render();
  });
  resetBtn.addEventListener("click", () => {
    checked = false;
    for (const row of rows) row.input.checked = false;
    container.dataset.quizOutcome = "";
    render();
  });

  render();

  return {
    destroy() {
      // No timers, no Plotly instances, no subscriptions to tear down.
    },
  };
}

export const leakageQuizComponent: WidgetComponent<MultiSelectQuizConfig, LeakageQuizData> = {
  type: "multi-select-quiz",
  parseData: (raw) => parseLeakageQuizData(raw),
  mount,
};
