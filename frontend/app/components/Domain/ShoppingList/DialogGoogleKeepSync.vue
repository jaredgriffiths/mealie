<template>
  <BaseDialog
    v-model="dialog"
    :title="$t('shopping-list.send-to-google-keep') || 'Send to Google Keep'"
    :icon="$globals.icons.googleKeep"
    submit-color="primary"
    :submit-text="actionButtonText"
    can-submit
    @submit="handleExport"
    @cancel="dialog = false"
  >
    <v-container class="py-2">
      <!-- Target Google Keep List Name -->
      <v-text-field
        v-model="targetListName"
        :label="$t('shopping-list.google-keep-list-name') || 'Google Keep List / Note Name'"
        :prepend-inner-icon="$globals.icons.googleKeep"
        variant="outlined"
        density="comfortable"
        persistent-hint
        :hint="$t('shopping-list.google-keep-hint') || 'Stored on this device and confirmed with each export'"
        class="mb-4"
      />

      <!-- Options -->
      <v-row dense>
        <v-col cols="12" sm="6">
          <v-switch
            v-model="onlyUnchecked"
            color="primary"
            density="compact"
            hide-details
            :label="$t('shopping-list.only-unchecked-items') || 'Only unchecked items'"
          />
        </v-col>
        <v-col cols="12" sm="6">
          <v-switch
            v-model="groupByLabel"
            color="primary"
            density="compact"
            hide-details
            :label="$t('shopping-list.group-by-labels') || 'Group by categories'"
          />
        </v-col>
      </v-row>

      <!-- Pixel / On-Device AI Supermarket Aisle Grouping -->
      <v-fade-transition>
        <v-card
          v-if="hasOnDeviceAI"
          variant="tonal"
          color="accent"
          class="my-3 pa-2"
        >
          <div class="d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <v-icon :icon="$globals.icons.robot" class="mr-2" />
              <div>
                <div class="text-subtitle-2 font-weight-bold">
                  {{ $t('shopping-list.on-device-ai-title') || 'Pixel On-Device AI' }}
                </div>
                <div class="text-caption text-medium-emphasis">
                  {{ $t('shopping-list.on-device-ai-desc') || 'Organize items by supermarket aisle with Gemini Nano' }}
                </div>
              </div>
            </div>
            <v-switch
              v-model="useOnDeviceAI"
              color="accent"
              density="compact"
              hide-details
            />
          </div>
        </v-card>
      </v-fade-transition>

      <!-- Preview of items to export -->
      <div class="mt-4">
        <div class="text-caption text-medium-emphasis mb-1">
          {{ $t('shopping-list.preview') || 'Preview' }} ({{ previewLinesCount }} {{ $t('shopping-list.items') || 'items' }}):
        </div>
        <v-card
          variant="outlined"
          max-height="160"
          style="overflow-y: auto;"
          class="pa-2 bg-grey-darken-4 font-mono text-body-2"
        >
          <pre style="white-space: pre-wrap; font-family: monospace; margin: 0;">{{ previewText || 'No items selected' }}</pre>
        </v-card>
      </div>
    </v-container>
  </BaseDialog>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ShoppingListItemOut } from "~/lib/api/types/household";
import { useGoogleKeepSync } from "~/composables/shopping-list-page/sub-composables/use-google-keep-sync";

const props = defineProps<{
  itemsByLabel: { [key: string]: ShoppingListItemOut[] };
}>();

const dialog = defineModel<boolean>({ default: false });

const {
  targetListName,
  onlyUnchecked,
  groupByLabel,
  useOnDeviceAI,
  hasOnDeviceAI,
  canNativeShare,
  formatListForKeep,
  exportToGoogleKeep,
} = useGoogleKeepSync();

const previewText = computed(() => {
  return formatListForKeep(props.itemsByLabel, {
    onlyUnchecked: onlyUnchecked.value,
    groupByLabel: groupByLabel.value,
  });
});

const previewLinesCount = computed(() => {
  if (!previewText.value) return 0;
  return previewText.value.split("\n").filter(line => line.startsWith("- [ ]")).length;
});

const actionButtonText = computed(() => {
  if (canNativeShare.value) {
    return "Share to Keep";
  }
  return "Open in Google Keep";
});

async function handleExport() {
  const success = await exportToGoogleKeep(props.itemsByLabel, {
    onlyUnchecked: onlyUnchecked.value,
    groupByLabel: groupByLabel.value,
    autoGroupWithAI: useOnDeviceAI.value,
  });

  if (success) {
    dialog.value = false;
  }
}
</script>
