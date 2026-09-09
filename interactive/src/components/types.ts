// Component contract + typed registry.
//
// A component is the only place that touches Plotly / the DOM container. It
// declares:
//   - `type`      : matches the config discriminator
//   - `parseData` : validates an unknown parsed-JSON value into its data shape
//   - `mount`     : renders into a container and returns a handle
//
// The runtime (src/main.ts) never branches on `type` directly; it looks the
// component up in the registry below.

import type { ActivityConfig } from "../config";

export interface MountArgs<TConfig extends ActivityConfig, TData> {
  container: HTMLElement;
  config: TConfig;
  data: TData;
}

export interface MountHandle {
  /** Tear down timers / Plotly instances. Safe to call more than once. */
  destroy(): void;
}

export type DataResult<TData> =
  | { ok: true; data: TData }
  | { ok: false; error: string };

export interface WidgetComponent<
  TConfig extends ActivityConfig = ActivityConfig,
  TData = unknown,
> {
  readonly type: TConfig["type"];
  parseData(raw: unknown): DataResult<TData>;
  mount(args: MountArgs<TConfig, TData>): MountHandle;
}

// A registry entry erases the concrete generic parameters so heterogeneous
// components can live in one map; `main.ts` re-narrows via the config union.
export type AnyWidgetComponent = WidgetComponent<ActivityConfig, unknown>;

export class ComponentRegistry {
  private readonly components = new Map<string, AnyWidgetComponent>();

  register(component: AnyWidgetComponent): void {
    if (this.components.has(component.type)) {
      throw new Error(`Duplicate component registration for type "${component.type}"`);
    }
    this.components.set(component.type, component);
  }

  get(type: string): AnyWidgetComponent | undefined {
    return this.components.get(type);
  }

  knownTypes(): string[] {
    return [...this.components.keys()];
  }
}
