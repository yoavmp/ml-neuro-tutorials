// Loader for the Exercise 10 leakage quiz artifact
// (book/_static/widgets/data/leakage_quiz.json). DOM / Plotly free so it can
// be unit tested independently of the rendering component. A single
// multiple-selection question: every option that is `correct: true` is one
// the student must select; the activity never recomputes anything, it only
// compares the student's checkbox selections against these precomputed flags.

import { z } from "zod";
import type { DataResult } from "./components/types";

const optionSchema = z
  .object({
    id: z.string().min(1, "option.id must be a non-empty string"),
    text: z.string().min(1, "option.text must be a non-empty string"),
    correct: z.boolean(),
    feedback: z.string().min(1, "option.feedback must be a non-empty string"),
  })
  .strict();

const schema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("multi-select-quiz"),
    question: z.string().min(1, "question must be a non-empty string"),
    options: z.array(optionSchema).min(2, "options must list at least two choices"),
    successFeedback: z.string().min(1, "successFeedback must be a non-empty string"),
    nuance: z.string().min(1, "nuance must be a non-empty string"),
  })
  .strict();

export type LeakageQuizOption = z.infer<typeof optionSchema>;
export type LeakageQuizData = z.infer<typeof schema>;

export function parseLeakageQuizData(raw: unknown): DataResult<LeakageQuizData> {
  const parsed = schema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid leakage quiz data: ${msg}` };
  }
  const data = parsed.data;

  const ids = data.options.map((o) => o.id);
  const dupIds = [...new Set(ids.filter((id, i) => ids.indexOf(id) !== i))];
  if (dupIds.length > 0) {
    return { ok: false, error: `Invalid leakage quiz data: duplicate option id(s): ${dupIds.join(", ")}` };
  }

  const hasCorrect = data.options.some((o) => o.correct);
  const hasIncorrect = data.options.some((o) => !o.correct);
  if (!hasCorrect || !hasIncorrect) {
    return {
      ok: false,
      error: "Invalid leakage quiz data: options must include at least one correct and one incorrect choice",
    };
  }

  return { ok: true, data };
}
