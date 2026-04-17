import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import QueryForm from "@/components/customer/QueryForm";

describe("QueryForm", () => {
  it("renders submit button", () => {
    render(<QueryForm isLoading={false} onSubmit={vi.fn()} />);
    expect(screen.getByRole("button", { name: /submit query/i })).toBeInTheDocument();
  });
});
