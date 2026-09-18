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
import { knnExploreComponent } from "./knn-explore";
import { classificationThresholdComponent } from "./classification-threshold";
import { classificationImbalanceComponent } from "./classification-imbalance";
import { validationStabilityComponent } from "./validation-stability";
import { validationLockTestComponent } from "./validation-lock-test";
import { nestedCvExplorerComponent } from "./nested-cv-explorer";
import { regularizationExploreComponent } from "./regularization-explore";

export const registry = new ComponentRegistry();
registry.register(runtimeSmokeComponent);
registry.register(histogramComponent);
registry.register(retentionComponent);
registry.register(correlationComponent);
registry.register(tableInspectionComponent);
registry.register(regressionCompareComponent);
registry.register(knnExploreComponent);
registry.register(classificationThresholdComponent);
registry.register(classificationImbalanceComponent);
registry.register(validationStabilityComponent);
registry.register(validationLockTestComponent);
registry.register(nestedCvExplorerComponent);
registry.register(regularizationExploreComponent);
