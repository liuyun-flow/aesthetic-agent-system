import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { I18nProvider } from "@/i18n";
import ResultCard from "@/components/ResultCard";

type CardProps = Parameters<typeof ResultCard>[0];

function renderCard(props: CardProps) {
  return render(
    <I18nProvider>
      <ResultCard {...props} />
    </I18nProvider>,
  );
}

describe("ResultCard", () => {
  it("renders critique score, dimensions and issue lists", () => {
    renderCard({
      taskType: "critique",
      data: {
        total_score: 6.5,
        dimensions: { color: 7 },
        main_issues: ["对比度不足"],
        cheapness_sources: [],
        priority_fixes: ["提高对比度"],
      },
    });
    expect(screen.getByText("评分结果")).toBeInTheDocument();
    expect(screen.getByText("6.5")).toBeInTheDocument();
    expect(screen.getByText("对比度不足")).toBeInTheDocument();
    expect(screen.getByText("提高对比度")).toBeInTheDocument();
  });

  it("renders the judgment-gap card when judgment_gap is present", () => {
    renderCard({
      taskType: "critique",
      data: {
        total_score: 5,
        dimensions: {},
        main_issues: ["x"],
        cheapness_sources: [],
        priority_fixes: ["y"],
        judgment_gap: {
          short_summary: "你低估了字体问题",
          missed_issues: ["字体层级对比不足"],
        },
      },
    });
    expect(screen.getByText("你的判断 vs AI")).toBeInTheDocument();
    expect(screen.getByText("你低估了字体问题")).toBeInTheDocument();
    expect(screen.getByText("字体层级对比不足")).toBeInTheDocument();
  });
});
