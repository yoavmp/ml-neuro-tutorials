// The single place every component is wired into the runtime. `main.ts` asks
// this registry for a component by config `type`; it never branches on the type
// itself. Later activities (histogram, retention) register here too.

import { ComponentRegistry } from "./types";
import { runtimeSmokeComponent } from "./runtime-smoke";

export const registry = new ComponentRegistry();
registry.register(runtimeSmokeComponent);
