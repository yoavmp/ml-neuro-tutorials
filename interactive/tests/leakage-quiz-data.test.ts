import { describe, expect, it } from "vitest";
import { parseLeakageQuizData } from "../src/leakage-quiz-data";

function option(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    id: "scaling",
    text: "Calculating the mean and standard deviation for scaling",
    correct: true,
    feedback: "Scaling parameters are learned from whichever rows they are fit on.",
    ...overrides,
  };
}

function validPayload() {
  return {
    schemaVersion: 1,
    activity: "multi-select-quiz",
    question: "Which operations learn quantities or make data-dependent decisions?",
    options: [
      option({ id: "scaling" }),
      option({ id: "feature-selection", text: "Choosing features based on correlation with the target" }),
      option({
        id: "metric-choice",
        text: "Choosing in advance whether success will be summarized with F1 or ROC-AUC",
        correct: false,
        feedback: "A metric choice made in advance does not learn anything from participant data.",
      }),
    ],
    successFeedback: "The first two operations learn from observed data.",
    nuance: "Choosing a metric only after inspecting results is still poor practice.",
  };
}

describe("parseLeakageQuizData", () => {
  it("accepts a well-formed payload", () => {
    const result = parseLeakageQuizData(validPayload());
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.options).toHaveLength(3);
    }
  });

  it("rejects a payload with the wrong schemaVersion", () => {
    const bad = { ...validPayload(), schemaVersion: 2 };
    expect(parseLeakageQuizData(bad).ok).toBe(false);
  });

  it("rejects a payload with the wrong activity literal", () => {
    const bad = { ...validPayload(), activity: "single-select-quiz" };
    expect(parseLeakageQuizData(bad).ok).toBe(false);
  });

  it("rejects duplicate option ids", () => {
    const bad = validPayload();
    bad.options[1] = { ...bad.options[0]! };
    expect(parseLeakageQuizData(bad).ok).toBe(false);
  });

  it("rejects a payload where every option is correct (no distinguishable wrong answer)", () => {
    const bad = validPayload();
    bad.options = bad.options.map((o) => ({ ...o, correct: true }));
    expect(parseLeakageQuizData(bad).ok).toBe(false);
  });

  it("rejects a payload where every option is incorrect (no achievable success state)", () => {
    const bad = validPayload();
    bad.options = bad.options.map((o) => ({ ...o, correct: false }));
    expect(parseLeakageQuizData(bad).ok).toBe(false);
  });

  it("rejects an option missing feedback text", () => {
    const bad = validPayload();
    (bad.options[0] as { feedback?: string }).feedback = "";
    expect(parseLeakageQuizData(bad).ok).toBe(false);
  });

  it("rejects an unknown extra field on an option (strict schema)", () => {
    const bad = validPayload();
    (bad.options[0] as Record<string, unknown>).extra = "nope";
    expect(parseLeakageQuizData(bad).ok).toBe(false);
  });

  it("accepts the shipped data/leakage_quiz.json", async () => {
    const fs = await import("node:fs/promises");
    const url = new URL("../../book/_static/widgets/data/leakage_quiz.json", import.meta.url);
    const text = await fs.readFile(url, "utf-8");
    const r = parseLeakageQuizData(JSON.parse(text));
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });
});
