import { describe, expect, it } from "vitest";

import { formatUsd } from "@/helpers/formatting";

describe("formatUsd", () => {
  it("formats with two decimals", () => {
    expect(formatUsd(1.2)).toBe("$1.20");
  });
});
