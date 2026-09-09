// Activity configuration schema + validation.
//
// Pure: given an unknown parsed-JSON value, return either a typed config or a
// readable error. No DOM / fetch / Plotly here so it can be unit tested.
//
// Versioning: every config carries an explicit integer `schemaVersion`. The
// runtime only understands CONFIG_SCHEMA_VERSION; anything else is rejected
// rather than best-effort parsed. The activity `type` is a discriminated union
// tag so new activities are added as new members, not new `if` branches.

import { z } from "zod";

export const CONFIG_SCHEMA_VERSION = 1 as const;

const baseFields = {
  schemaVersion: z.literal(CONFIG_SCHEMA_VERSION),
  title: z.string().min(1, "config.title must be a non-empty string"),
  description: z.string().optional(),
  // Relative (same-origin) URL of the data file, resolved against the config
  // file URL by src/urls.ts#resolveDataUrl.
  data: z.string().min(1, "config.data must be a non-empty URL string"),
};

const runtimeSmokeConfig = z
  .object({
    ...baseFields,
    type: z.literal("runtime-smoke"),
  })
  .strict();

/**
 * Discriminated union of every known activity config. Add a new activity by
 * adding a member here and registering a component with the same `type`.
 */
export const activityConfigSchema = z.discriminatedUnion("type", [
  runtimeSmokeConfig,
]);

export type ActivityConfig = z.infer<typeof activityConfigSchema>;
export type RuntimeSmokeConfig = z.infer<typeof runtimeSmokeConfig>;

export type ConfigResult =
  | { ok: true; config: ActivityConfig }
  | { ok: false; error: string };

function formatIssues(err: z.ZodError): string {
  return err.issues
    .map((i) => {
      const path = i.path.join(".");
      return path ? `${path}: ${i.message}` : i.message;
    })
    .join("; ");
}

/** Validate an already-JSON-parsed value as an activity config. */
export function parseActivityConfig(raw: unknown): ConfigResult {
  if (raw === null || typeof raw !== "object") {
    return { ok: false, error: "Config must be a JSON object." };
  }
  const versioned = raw as { schemaVersion?: unknown };
  if (versioned.schemaVersion !== CONFIG_SCHEMA_VERSION) {
    return {
      ok: false,
      error:
        `Unsupported config schemaVersion ${JSON.stringify(versioned.schemaVersion)}; ` +
        `this runtime understands schemaVersion ${CONFIG_SCHEMA_VERSION}.`,
    };
  }
  const parsed = activityConfigSchema.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: `Invalid config: ${formatIssues(parsed.error)}` };
  }
  return { ok: true, config: parsed.data };
}

/** Parse a raw JSON string and validate it as an activity config. */
export function parseActivityConfigJson(text: string): ConfigResult {
  let json: unknown;
  try {
    json = JSON.parse(text);
  } catch (e) {
    return { ok: false, error: `Config is not valid JSON: ${(e as Error).message}` };
  }
  return parseActivityConfig(json);
}
