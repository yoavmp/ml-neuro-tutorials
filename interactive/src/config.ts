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

const histogramVariableRef = z
  .object({
    name: z.string().min(1, "variable.name must be a non-empty string"),
    label: z.string().min(1, "variable.label must be a non-empty string"),
  })
  .strict();

const histogramBinSpec = z
  .object({
    min: z.number().int().positive(),
    max: z.number().int().positive(),
    step: z.number().int().positive(),
    default: z.number().int().positive(),
  })
  .strict();

const edaHistogramConfig = z
  .object({
    ...baseFields,
    type: z.literal("eda-histogram"),
    instructions: z.string().min(1, "config.instructions must be a non-empty string"),
    variables: z
      .array(histogramVariableRef)
      .min(1, "config.variables must list at least one variable"),
    defaultVariable: z.string().min(1, "config.defaultVariable must be a non-empty string"),
    bins: histogramBinSpec,
    xAxisLabel: z.string().min(1).optional(),
    yAxisLabel: z.string().min(1).optional(),
    reflectionPrompts: z
      .array(z.string().min(1))
      .min(1, "config.reflectionPrompts must list at least one prompt"),
  })
  .strict();

const retentionVariableRef = z
  .object({
    name: z.string().min(1, "variable.name must be a non-empty string"),
    label: z.string().min(1, "variable.label must be a non-empty string"),
  })
  .strict();

const retentionGroup = z
  .object({
    key: z.string().min(1, "group.key must be a non-empty string"),
    label: z.string().min(1, "group.label must be a non-empty string"),
    variables: z
      .array(retentionVariableRef)
      .min(1, "each group must list at least one variable"),
  })
  .strict();

const edaRetentionConfig = z
  .object({
    ...baseFields,
    type: z.literal("eda-retention"),
    instructions: z.string().min(1, "config.instructions must be a non-empty string"),
    siteField: z.string().min(1, "config.siteField must be a non-empty string"),
    siteLabel: z.string().min(1, "config.siteLabel must be a non-empty string"),
    groups: z
      .array(retentionGroup)
      .min(1, "config.groups must list at least one group"),
    defaultVariables: z
      .array(z.string().min(1))
      .min(1, "config.defaultVariables must list at least one variable"),
    chart: z
      .object({
        // Only one metric today; declared explicitly so a future metric is an
        // additive change, not a silent default flip.
        metric: z.literal("retained-percentage"),
      })
      .strict(),
    lowRetentionWarningPct: z
      .number()
      .positive()
      .max(100)
      .optional(),
    reflectionPrompts: z
      .array(z.string().min(1))
      .min(1, "config.reflectionPrompts must list at least one prompt"),
  })
  .strict();

const correlationVariableRef = z
  .object({
    name: z.string().min(1, "variable.name must be a non-empty string"),
    label: z.string().min(1, "variable.label must be a non-empty string"),
  })
  .strict();

const correlationGroupValue = z
  .object({
    code: z.number().int(),
    label: z.string().min(1, "grouping value.label must be a non-empty string"),
  })
  .strict();

const correlationGrouping = z
  .object({
    key: z.string().min(1, "grouping.key must be a non-empty string"),
    label: z.string().min(1, "grouping.label must be a non-empty string"),
    field: z.string().min(1, "grouping.field must be a non-empty string"),
    values: z
      .array(correlationGroupValue)
      .min(1, "each grouping must list at least one value mapping"),
  })
  .strict();

const edaCorrelationConfig = z
  .object({
    ...baseFields,
    type: z.literal("eda-correlation"),
    instructions: z.string().min(1, "config.instructions must be a non-empty string"),
    variables: z
      .array(correlationVariableRef)
      .min(2, "config.variables must list at least two numeric variables"),
    defaultX: z.string().min(1, "config.defaultX must be a non-empty string"),
    defaultY: z.string().min(1, "config.defaultY must be a non-empty string"),
    defaultMethod: z.enum(["pearson", "spearman"]),
    // Real groupings only (diagnosis, sex, …); the component always offers a
    // "None" option itself, so this list must not be empty of meaning but may
    // be an empty array if only ungrouped exploration is wanted.
    groupings: z.array(correlationGrouping),
    reflectionPrompts: z
      .array(z.string().min(1))
      .min(1, "config.reflectionPrompts must list at least one prompt"),
  })
  .strict();

/**
 * Discriminated union of every known activity config. Add a new activity by
 * adding a member here and registering a component with the same `type`.
 */
export const activityConfigSchema = z.discriminatedUnion("type", [
  runtimeSmokeConfig,
  edaHistogramConfig,
  edaRetentionConfig,
  edaCorrelationConfig,
]);

export type ActivityConfig = z.infer<typeof activityConfigSchema>;
export type RuntimeSmokeConfig = z.infer<typeof runtimeSmokeConfig>;
export type EdaHistogramConfig = z.infer<typeof edaHistogramConfig>;
export type EdaRetentionConfig = z.infer<typeof edaRetentionConfig>;
export type EdaCorrelationConfig = z.infer<typeof edaCorrelationConfig>;

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

/**
 * Cross-field checks the Zod discriminated union cannot express (its members
 * must stay plain objects). Returns an error string or null.
 */
function checkSemantics(config: ActivityConfig): string | null {
  if (config.type === "eda-histogram") {
    const names = config.variables.map((v) => v.name);
    const duplicates = [...new Set(names.filter((n, i) => names.indexOf(n) !== i))];
    if (duplicates.length > 0) {
      return `config.variables has duplicate name(s): ${duplicates.join(", ")}`;
    }
    if (!names.includes(config.defaultVariable)) {
      return (
        `config.defaultVariable "${config.defaultVariable}" is not one of ` +
        `config.variables (${names.join(", ")})`
      );
    }
    const { min, max, step, default: dflt } = config.bins;
    if (min > max) {
      return `config.bins.min (${min}) must not exceed config.bins.max (${max})`;
    }
    if (dflt < min || dflt > max) {
      return `config.bins.default (${dflt}) must be within [${min}, ${max}]`;
    }
    if ((dflt - min) % step !== 0) {
      return `config.bins.default (${dflt}) must be reachable from min ${min} in steps of ${step}`;
    }
  }
  if (config.type === "eda-retention") {
    const groupKeys = config.groups.map((g) => g.key);
    const dupKeys = [...new Set(groupKeys.filter((k, i) => groupKeys.indexOf(k) !== i))];
    if (dupKeys.length > 0) {
      return `config.groups has duplicate key(s): ${dupKeys.join(", ")}`;
    }
    const names = config.groups.flatMap((g) => g.variables.map((v) => v.name));
    const dupNames = [...new Set(names.filter((n, i) => names.indexOf(n) !== i))];
    if (dupNames.length > 0) {
      return `config.groups has duplicate variable name(s) across groups: ${dupNames.join(", ")}`;
    }
    if (names.includes(config.siteField)) {
      return `config.siteField "${config.siteField}" must not also be a selectable variable`;
    }
    const nameSet = new Set(names);
    const unknownDefaults = config.defaultVariables.filter((n) => !nameSet.has(n));
    if (unknownDefaults.length > 0) {
      return (
        `config.defaultVariables contains name(s) not in any group: ` +
        `${unknownDefaults.join(", ")}`
      );
    }
    const dv = config.defaultVariables;
    const dupDefaults = [...new Set(dv.filter((n, i) => dv.indexOf(n) !== i))];
    if (dupDefaults.length > 0) {
      return `config.defaultVariables has duplicate name(s): ${dupDefaults.join(", ")}`;
    }
  }
  if (config.type === "eda-correlation") {
    const names = config.variables.map((v) => v.name);
    const dupNames = [...new Set(names.filter((n, i) => names.indexOf(n) !== i))];
    if (dupNames.length > 0) {
      return `config.variables has duplicate name(s): ${dupNames.join(", ")}`;
    }
    const nameSet = new Set(names);
    if (!nameSet.has(config.defaultX)) {
      return `config.defaultX "${config.defaultX}" is not one of config.variables (${names.join(", ")})`;
    }
    if (!nameSet.has(config.defaultY)) {
      return `config.defaultY "${config.defaultY}" is not one of config.variables (${names.join(", ")})`;
    }
    if (config.defaultX === config.defaultY) {
      return `config.defaultX and config.defaultY must be different variables (both "${config.defaultX}")`;
    }
    const groupKeys = config.groupings.map((g) => g.key);
    const dupKeys = [...new Set(groupKeys.filter((k, i) => groupKeys.indexOf(k) !== i))];
    if (dupKeys.length > 0) {
      return `config.groupings has duplicate key(s): ${dupKeys.join(", ")}`;
    }
    if (groupKeys.includes("none")) {
      return `config.groupings must not define a "none" key; the "None" option is added automatically`;
    }
    for (const g of config.groupings) {
      if (nameSet.has(g.field)) {
        return `config.groupings["${g.key}"].field "${g.field}" must not also be a selectable variable`;
      }
      const codes = g.values.map((v) => v.code);
      const dupCodes = [...new Set(codes.filter((c, i) => codes.indexOf(c) !== i))];
      if (dupCodes.length > 0) {
        return `config.groupings["${g.key}"] has duplicate code(s): ${dupCodes.join(", ")}`;
      }
    }
  }
  return null;
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
  const semantic = checkSemantics(parsed.data);
  if (semantic) {
    return { ok: false, error: `Invalid config: ${semantic}` };
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
