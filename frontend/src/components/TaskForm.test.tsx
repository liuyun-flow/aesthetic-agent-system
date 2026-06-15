import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nProvider } from "@/i18n";
import TaskForm, { type UserJudgment, type ImageData } from "@/components/TaskForm";

type Submit = (
  description: string,
  type: "analyze" | "critique" | "iterate",
  judgment: UserJudgment | null,
  image: ImageData | null,
) => void;

function renderForm(
  onSubmit: Submit = vi.fn(),
  prefill: { description: string; taskType: "analyze" | "critique" | "iterate"; key: number } | null = null,
) {
  render(
    <I18nProvider>
      <TaskForm onSubmit={onSubmit} loading={false} prefill={prefill} />
    </I18nProvider>,
  );
  return onSubmit;
}

const LONG = "这是一段足够长的作品描述内容";

describe("TaskForm", () => {
  it("disables Run with a hint until the description is long enough", async () => {
    const user = userEvent.setup();
    renderForm();

    const run = screen.getByRole("button", { name: /运行/ });
    expect(run).toBeDisabled();
    expect(screen.getByText(/描述不足 10 字/)).toBeInTheDocument();

    await user.type(screen.getByLabelText("作品描述"), LONG);
    expect(run).toBeEnabled();
  });

  it("submits on Ctrl+Enter", async () => {
    const user = userEvent.setup();
    const onSubmit = renderForm();

    const textarea = screen.getByLabelText("作品描述");
    await user.type(textarea, LONG);
    await user.keyboard("{Control>}{Enter}{/Control}");

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(LONG, "analyze", null, null);
  });

  it("loads a description from prefill (再练一次)", () => {
    renderForm(vi.fn(), { description: "历史作品描述内容", taskType: "critique", key: 1 });
    expect(screen.getByDisplayValue("历史作品描述内容")).toBeInTheDocument();
  });
});
