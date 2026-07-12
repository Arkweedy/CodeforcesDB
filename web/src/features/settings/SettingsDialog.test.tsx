import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SettingsDialog } from "./SettingsDialog";

const apiMocks = vi.hoisted(() => ({
  settings: vi.fn(),
  patchSettings: vi.fn(),
  syncCodeforces: vi.fn()
}));

vi.mock("../../api", () => ({ api: apiMocks }));

describe("SettingsDialog", () => {
  it("requires saving changed settings before syncing", async () => {
    apiMocks.settings.mockResolvedValue({
      codeforces_handle: "tourist",
      locale: "zh",
      page_size: 50,
      density: "comfortable",
      last_submission_id: null,
      last_sync_at: null,
      last_sync_error: null
    });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <SettingsDialog open onOpenChange={vi.fn()} locale="zh" onApplied={vi.fn()} />
      </QueryClientProvider>
    );
    const input = await screen.findByDisplayValue("tourist");
    fireEvent.change(input, { target: { value: "new-handle" } });
    fireEvent.click(screen.getByText("增量同步"));
    expect(await screen.findByText("请先保存设置，再开始同步")).toBeInTheDocument();
    expect(apiMocks.syncCodeforces).not.toHaveBeenCalled();
  });
});
