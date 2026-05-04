import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TaskComposer } from "./TaskComposer";

describe("TaskComposer", () => {
  it("submits normalized mission payload", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<TaskComposer onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText("标题"), { target: { value: "新的任务" } });
    fireEvent.change(screen.getByLabelText("目标"), { target: { value: "完成 API 调用" } });
    fireEvent.click(screen.getByRole("button", { name: "创建任务" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "新的任务",
        goal: "完成 API 调用",
      }),
    );
  });
});
