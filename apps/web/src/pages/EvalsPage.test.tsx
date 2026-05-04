import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EvalsPage } from "./EvalsPage";

describe("EvalsPage", () => {
  it("renders golden task scenarios", () => {
    render(<EvalsPage />);
    expect(screen.getByText("评估覆盖场景")).toBeInTheDocument();
    expect(screen.getByText("checkpoint 恢复")).toBeInTheDocument();
  });
});
