import { describe, expect, it } from "vitest";

import { schemasPackage } from "./index";

describe("schemas package boundary", () => {
  it("exports the Round 00 placeholder", () => {
    expect(schemasPackage.name).toBe("@branchlab/schemas");
  });
});
