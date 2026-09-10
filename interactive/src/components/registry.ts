// The single place every component is wired into the runtime. `main.ts` asks
// this registry for a component by config `type`; it never branches on the type
// itself.

import { ComponentRegistry } from "./types";
import { runtimeSmokeComponent } from "./runtime-smoke";
import { histogramComponent } from "./histogram";
import { retentionComponent } from "./retention";
import { correlationComponent } from "./correlation";
import { tableInspectionComponent } from "./table-inspection";
import { regressionCompareComponent } from "./regression-compare";

export const registry = new ComponentRegistry();
registry.register(runtimeSmokeComponent);
registry.register(histogramComponent);
registry.register(retentionComponent);
registry.register(correlationComponent);
registry.register(tableInspectionComponent);
registry.register(regressionCompareComponent);
