import { computed } from "vue";
import { useStorage } from "@vueuse/core";
import { useCopy } from "~/composables/use-copy";
import { alert } from "~/composables/use-toast";
import type { ShoppingListItemOut } from "~/lib/api/types/household";

export interface GoogleKeepSyncOptions {
  onlyUnchecked: boolean;
  groupByLabel: boolean;
  autoGroupWithAI?: boolean;
}

export function useGoogleKeepSync() {
  const i18n = useI18n();
  const { copyText } = useCopy();

  // Persist target Google Keep note title in user's browser across sessions
  const targetListName = useStorage("mealie:keep_target_list_name", "Groceries");

  // User preference options
  const onlyUnchecked = useStorage("mealie:keep_only_unchecked", true);
  const groupByLabel = useStorage("mealie:keep_group_by_label", false);
  const useOnDeviceAI = useStorage("mealie:keep_use_ondevice_ai", false);

  // Detect on-device AI capabilities (e.g. Gemini Nano on Google Pixel via window.ai)
  const hasOnDeviceAI = computed(() => {
    if (typeof window === "undefined") return false;
    return Boolean((window as unknown as { ai?: { languageModel?: unknown } }).ai?.languageModel);
  });

  // Detect native Web Share API
  const canNativeShare = computed(() => {
    if (typeof navigator === "undefined") return false;
    return typeof navigator.share === "function";
  });

  /**
   * Format items for Google Keep checklist syntax
   */
  function formatListForKeep(
    itemsByLabel: { [key: string]: ShoppingListItemOut[] },
    options: GoogleKeepSyncOptions,
  ): string {
    const lines: string[] = [];

    Object.entries(itemsByLabel).forEach(([label, items]) => {
      const filteredItems = items.filter(item => (options.onlyUnchecked ? !item.checked : true));
      if (filteredItems.length === 0) return;

      if (options.groupByLabel && label && label !== "no-category" && label !== "null") {
        if (lines.length > 0) lines.push("");
        lines.push(`[${label}]`);
      }

      filteredItems.forEach((item) => {
        const text = item.display || item.note || item.food?.name || "";
        if (text.trim()) {
          // Google Keep understands markdown checkboxes or hyphenated lines
          lines.push(`- [ ] ${text.trim()}`);
        }
      });
    });

    return lines.join("\n");
  }

  /**
   * Optional Gemini Nano On-Device AI formatting to categorize items by supermarket aisle
   */
  async function organizeWithOnDeviceAI(formattedText: string): Promise<string> {
    if (!hasOnDeviceAI.value) return formattedText;

    try {
      const ai = (window as unknown as { ai: { languageModel: { create: () => Promise<{ prompt: (msg: string) => Promise<string> }> } } }).ai;
      const session = await ai.languageModel.create();
      const prompt = `You are a grocery shopping assistant. Reorganize these shopping list items by physical supermarket aisle (e.g. Produce, Dairy, Bakery, Pantry, Meat, Frozen). Keep the exact format "- [ ] Item" for each item, and use "[Aisle Name]" as group headers. Return ONLY the reorganized checklist without markdown code block backticks:\n\n${formattedText}`;
      const response = await session.prompt(prompt);
      if (response && response.trim()) {
        return response.trim();
      }
    }
    catch (e) {
      console.warn("On-device AI categorization fallback to default:", e);
    }

    return formattedText;
  }

  /**
   * Perform the export action: Web Share to Keep or Clipboard + Launch Keep
   */
  async function exportToGoogleKeep(
    itemsByLabel: { [key: string]: ShoppingListItemOut[] },
    options: GoogleKeepSyncOptions,
  ): Promise<boolean> {
    let text = formatListForKeep(itemsByLabel, options);

    if (options.autoGroupWithAI && hasOnDeviceAI.value) {
      text = await organizeWithOnDeviceAI(text);
    }

    if (!text.trim()) {
      alert.info(i18n.t("shopping-list.no-items-to-export") || "No items to export");
      return false;
    }

    const title = targetListName.value.trim() || "Groceries";

    // 1. If Web Share API is available (Pixel / Android / iOS native)
    if (canNativeShare.value) {
      try {
        await navigator.share({
          title,
          text,
        });
        return true;
      }
      catch (err: unknown) {
        // If user cancelled the share sheet, do nothing
        if ((err as Error)?.name === "AbortError") {
          return false;
        }
        console.warn("navigator.share failed, falling back to clipboard:", err);
      }
    }

    // 2. Fallback: Copy to clipboard and open Google Keep web/app
    copyText(text);
    window.open("https://keep.google.com/", "_blank");
    return true;
  }

  return {
    targetListName,
    onlyUnchecked,
    groupByLabel,
    useOnDeviceAI,
    hasOnDeviceAI,
    canNativeShare,
    formatListForKeep,
    exportToGoogleKeep,
  };
}
