<template>
  <v-container
    fluid
    class="narrow-container"
  >
    <!-- Image -->
    <BasePageTitle divider>
      <template #header>
        <v-img
          width="100%"
          max-height="200"
          max-width="150"
          src="/svgs/admin-site-settings.svg"
        />
      </template>
      <template #title>
        {{ $t("settings.site-settings") }}
      </template>
    </BasePageTitle>

    <!-- Bug Report -->
    <BaseDialog
      v-model="bugReportDialog"
      :title="$t('settings.bug-report')"
      :width="800"
      :icon="$globals.icons.github"
    >
      <v-card-text>
        <div class="pb-4">
          {{ $t('settings.bug-report-information') }}
        </div>
        <v-textarea
          v-model="bugReportText"
          variant="outlined"
          rows="18"
          readonly
        />
        <div
          class="d-flex justify-end"
          style="gap: 5px"
        >
          <BaseButton
            color="gray"
            secondary
            target="_blank"
            href="https://github.com/mealie-recipes/mealie/issues/new/choose"
          >
            <template #icon>
              {{ $globals.icons.github }}
            </template>
            {{ $t('settings.tracker') }}
          </BaseButton>
          <AppButtonCopy
            :copy-text="bugReportText"
            color="info"
            :icon="false"
          />
        </div>
      </v-card-text>
    </BaseDialog>

    <div class="d-flex justify-end">
      <BaseButton
        color="info"
        @click="
          bugReportDialog = true;
        "
      >
        <template #icon>
          {{ $globals.icons.github }}
        </template>
        {{ $t('settings.bug-report') }}
      </BaseButton>
    </div>

    <!-- Configuration -->
    <section>
      <BaseCardSectionTitle
        class="pb-0"
        :icon="$globals.icons.cog"
        :title="$t('settings.configuration')"
      />
      <v-card class="mb-4">
        <template
          v-for="(check, idx) in simpleChecks"
          :key="`list-item-${idx}`"
        >
          <v-list-item :title="check.text">
            <template #prepend>
              <v-icon :color="check.color" class="opacity-100">
                {{ check.icon }}
              </v-icon>
            </template>
            <v-list-item-subtitle class="wrap-word">
              {{ check.status ? check.successText : check.errorText }}
            </v-list-item-subtitle>
          </v-list-item>
          <v-divider />
        </template>
      </v-card>
    </section>

    <!-- Email -->
    <section>
      <BaseCardSectionTitle
        class="pt-2"
        :icon="$globals.icons.email"
        :title="$t('user.email')"
      />
      <v-alert
        border="start"
        :border-color="appConfig.emailReady ? 'success' : 'error'"
        variant="text"
        elevation="2"
      >
        <template #prepend>
          <v-icon :color="appConfig.emailReady ? 'success' : 'warning'">
            {{ appConfig.emailReady ? $globals.icons.checkboxMarkedCircle : $globals.icons.alertCircle }}
          </v-icon>
        </template>
        <div class="font-weight-medium">
          {{ $t('settings.email-configuration-status') }}
        </div>
        <div>
          {{ appConfig.emailReady ? $t('settings.ready') : $t('settings.not-ready') }}
        </div>
        <div>
          <v-text-field
            v-model="state.address"
            class="mr-4"
            :label="$t('user.email')"
            :rules="[validators.email]"
          />
          <BaseButton
            color="info"
            variant="elevated"
            :disabled="!appConfig.emailReady || !validEmail"
            :loading="state.loading"
            class="opacity-100"
            @click="testEmail"
          >
            <template #icon>
              {{ $globals.icons.email }}
            </template>
            {{ $t("general.test") }}
          </BaseButton>
          <template v-if="state.tested">
            <v-divider class="my-x mt-6" />
            <v-card-text class="px-0">
              <h4> {{ $t("settings.email-test-results") }}</h4>
              <span class="pl-4">
                {{ state.success ? $t('settings.succeeded') : $t('settings.failed') }}
              </span>
            </v-card-text>
          </template>
        </div>
      </v-alert>
    </section>

    <!-- Firebase Sync Bridge -->
    <section class="mt-4">
      <BaseCardSectionTitle
        class="pt-2"
        :icon="$globals.icons.database"
        :title="'Firebase Sync Bridge'"
      />
      <v-card class="mb-4 pa-4">
        <v-row class="mb-2">
          <v-col cols="12" md="6">
            <v-list-item title="Sync Worker Status">
              <template #prepend>
                <v-icon :color="syncStatus.syncWorkerStatus === 'online' ? 'success' : 'error'">
                  {{ syncStatus.syncWorkerStatus === 'online' ? $globals.icons.checkboxMarkedCircle : $globals.icons.alertCircle }}
                </v-icon>
              </template>
              <v-list-item-subtitle>
                {{ (syncStatus.syncWorkerStatus || 'offline').toUpperCase() }}
              </v-list-item-subtitle>
            </v-list-item>
          </v-col>
          <v-col cols="12" md="6" class="d-flex align-center justify-end" style="gap: 10px;">
            <BaseButton
              color="info"
              :loading="state.syncing"
              @click="triggerSync"
            >
              Force Sync Now
            </BaseButton>
            <BaseButton
              color="success"
              :loading="state.saving"
              @click="saveFirebaseSettings"
            >
              Save Settings
            </BaseButton>
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="12" md="6">
            <v-switch
              v-model="firebaseForm.enabled"
              label="Enable Firebase Bridge"
              color="success"
              hide-details
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-select
              v-model="firebaseForm.syncStrategy"
              :items="['Hybrid Sync (LAN + Cloud Fallback)', 'LAN-Only (No Cloud)']"
              label="Sync Strategy"
              density="comfortable"
            />
          </v-col>
        </v-row>

        <v-text-field
          v-model="firebaseForm.mealieHostUrl"
          label="Mealie Host URL (For LAN Mode)"
          variant="outlined"
          placeholder="http://192.168.50.107:9925"
        />

        <v-textarea
          v-model="firebaseForm.credentialsJson"
          label="Firebase Service Account Private Key JSON"
          variant="outlined"
          rows="5"
          placeholder="{ ... }"
          hint="Paste the downloaded JSON private key credentials here."
          persistent-hint
        />

        <div class="mt-4 d-flex align-center" style="gap: 10px;">
          <BaseButton
            color="secondary"
            :loading="state.testing"
            @click="testFirebaseCredentials"
          >
            Test Credentials format
          </BaseButton>
          <span v-if="testResult.tested" :class="testResult.success ? 'text-success' : 'text-error'">
            {{ testResult.success ? 'Format Valid!' : 'Error: ' + testResult.error }}
          </span>
        </div>

        <v-divider class="my-6" />

        <h4 class="mb-2">Local Database Cache Sync Statistics</h4>
        <v-row>
          <v-col cols="4">
            <v-card variant="tonal" class="pa-3 text-center">
              <div class="text-h6">{{ syncStatus.recipeCount }}</div>
              <div class="text-caption">Recipes</div>
            </v-card>
          </v-col>
          <v-col cols="4">
            <v-card variant="tonal" class="pa-3 text-center">
              <div class="text-h6">{{ syncStatus.shoppingListCount }}</div>
              <div class="text-caption">Shopping Lists</div>
            </v-card>
          </v-col>
          <v-col cols="4">
            <v-card variant="tonal" class="pa-3 text-center">
              <div class="text-h6">{{ syncStatus.mealPlanCount }}</div>
              <div class="text-caption">Meal Plans</div>
            </v-card>
          </v-col>
        </v-row>

        <v-divider class="my-6" />

        <div class="d-flex justify-space-between align-center mb-2">
          <h4>Sync Daemon Logs (Last 50 lines)</h4>
          <BaseButton
            variant="text"
            density="compact"
            @click="fetchLogs"
          >
            Refresh Logs
          </BaseButton>
        </div>
        <pre class="bg-grey-darken-4 text-green-accent-3 pa-3 rounded text-caption overflow-x-auto" style="max-height: 250px; font-family: monospace;">{{ bridgeLogs.join('\n') }}</pre>
      </v-card>
    </section>

    <!-- General App Info -->
    <section class="mt-4">
      <BaseCardSectionTitle
        class="pb-0"
        :icon="$globals.icons.cog"
        :title="$t('settings.general-about')"
      />
      <v-card class="mb-4">
        <template v-if="appInfo && appInfo.length">
          <template
            v-for="(property, idx) in appInfo"
            :key="property.name"
          >
            <v-list-item
              :title="property.name"
              :prepend-icon="property.icon || $globals.icons.user"
            >
              <template v-if="property.slot === 'recipe-scraper'">
                <v-list-item-subtitle>
                  <a
                    class="text-primary"
                    target="_blank"
                    :href="`https://github.com/hhursev/recipe-scrapers/releases/tag/${property.value}`"
                  >
                    {{ property.value }}
                  </a>
                </v-list-item-subtitle>
              </template>
              <template v-else-if="property.slot === 'build'">
                <v-list-item-subtitle>
                  <a
                    class="text-primary"
                    target="_blank"
                    :href="`https://github.com/mealie-recipes/mealie/commit/${property.value}`"
                  >
                    {{ property.value }}
                  </a>
                </v-list-item-subtitle>
              </template>
              <template v-else-if="property.slot === 'version' && property.value !== 'develop' && property.value !== 'nightly'">
                <v-list-item-subtitle>
                  <a
                    class="text-primary"
                    target="_blank"
                    :href="`https://github.com/mealie-recipes/mealie/releases/tag/${property.value}`"
                  >
                    {{ property.value }}
                  </a>
                </v-list-item-subtitle>
              </template>
              <template v-else>
                <v-list-item-subtitle>
                  {{ property.value }}
                </v-list-item-subtitle>
              </template>
            </v-list-item>
            <v-divider
              v-if="appInfo && idx !== appInfo.length - 1"
              :key="`divider-${property.name}`"
            />
          </template>
        </template>
        <template v-else>
          <div class="mb-3 text-center">
            <AppLoader :waiting-text="$t('general.loading')" />
          </div>
        </template>
      </v-card>
    </section>
  </v-container>
</template>

<script setup lang="ts">
import type { TranslateResult } from "vue-i18n";
import { useAdminApi, useUserApi } from "~/composables/api";
import { useRequests } from "~/composables/api/api-client";
import { validators } from "~/composables/use-validators";
import { useAsyncKey } from "~/composables/use-utils";
import type { CheckAppConfig } from "~/lib/api/types/admin";
import AppLoader from "~/components/global/AppLoader.vue";

interface SimpleCheck {
  id: string;
  text: TranslateResult;
  status: boolean | undefined;
  successText: TranslateResult;
  errorText: TranslateResult;
  color: string;
  icon: string;
}

interface CheckApp extends CheckAppConfig {
  isSiteSecure?: boolean;
}

definePageMeta({
  layout: "admin",
});

// For some reason the layout is not set automatically, so we set it here,
// even though it's defined above in the page meta.
onMounted(() => {
  setPageLayout("admin");
});

const { $globals } = useNuxtApp();
const i18n = useI18n();

const state = reactive({
  loading: false,
  address: "",
  success: false,
  error: "",
  tested: false,
});

// Set page title
useSeoMeta({
  title: i18n.t("settings.site-settings"),
});

const appConfig = ref<CheckApp>({
  emailReady: true,
  baseUrlSet: true,
  isSiteSecure: true,
  isUpToDate: false,
  ldapReady: false,
  oidcReady: false,
});
function isLocalHostOrHttps() {
  return window.location.hostname === "localhost" || window.location.protocol === "https:";
}
const api = useUserApi();
const adminApi = useAdminApi();
onMounted(async () => {
  const { data } = await adminApi.about.checkApp();
  if (data) {
    appConfig.value = { ...data, isSiteSecure: false };
  }
  appConfig.value.isSiteSecure = isLocalHostOrHttps();
});
const simpleChecks = computed<SimpleCheck[]>(() => {
  const goodIcon = $globals.icons.checkboxMarkedCircle;
  const badIcon = $globals.icons.alert;
  const warningIcon = $globals.icons.alertCircle;
  const goodColor = "success";
  const badColor = "error";
  const warningColor = "warning";
  const data: SimpleCheck[] = [
    {
      id: "application-version",
      text: i18n.t("settings.application-version"),
      status: appConfig.value.isUpToDate,
      errorText: i18n.t("settings.application-version-error-text", [rawAppInfo.value.version, rawAppInfo.value.versionLatest]),
      successText: i18n.t("settings.mealie-is-up-to-date"),
      color: appConfig.value.isUpToDate ? goodColor : warningColor,
      icon: appConfig.value.isUpToDate ? goodIcon : warningIcon,
    },
    {
      id: "secure-site",
      text: i18n.t("settings.secure-site"),
      status: appConfig.value.isSiteSecure,
      errorText: i18n.t("settings.secure-site-error-text"),
      successText: i18n.t("settings.secure-site-success-text"),
      color: appConfig.value.isSiteSecure ? goodColor : badColor,
      icon: appConfig.value.isSiteSecure ? goodIcon : badIcon,
    },
    {
      id: "server-side-base-url",
      text: i18n.t("settings.server-side-base-url"),
      status: appConfig.value.baseUrlSet,
      errorText: i18n.t("settings.server-side-base-url-error-text"),
      successText: i18n.t("settings.server-side-base-url-success-text"),
      color: appConfig.value.baseUrlSet ? goodColor : badColor,
      icon: appConfig.value.baseUrlSet ? goodIcon : badIcon,
    },
    {
      id: "ldap-ready",
      text: appConfig.value.ldapReady ? i18n.t("settings.ldap-ready") : i18n.t("settings.ldap-not-ready"),
      status: appConfig.value.ldapReady,
      errorText: i18n.t("settings.ldap-ready-error-text"),
      successText: i18n.t("settings.ldap-ready-success-text"),
      color: appConfig.value.ldapReady ? goodColor : warningColor,
      icon: appConfig.value.ldapReady ? goodIcon : warningIcon,
    },
    {
      id: "oidc-ready",
      text: appConfig.value.oidcReady ? i18n.t("settings.oidc-ready") : i18n.t("settings.oidc-not-ready"),
      status: appConfig.value.oidcReady,
      errorText: i18n.t("settings.oidc-ready-error-text"),
      successText: i18n.t("settings.oidc-ready-success-text"),
      color: appConfig.value.oidcReady ? goodColor : warningColor,
      icon: appConfig.value.oidcReady ? goodIcon : warningIcon,
    },
  ];
  return data;
});
const requests = useRequests();

const firebaseForm = ref({
  enabled: false,
  syncStrategy: "Hybrid Sync (LAN + Cloud Fallback)",
  mealieHostUrl: "http://localhost:9925",
  credentialsJson: ""
});

const syncStatus = ref({
  syncWorkerStatus: "offline",
  firebaseAuthStatus: false,
  firestoreDbStatus: false,
  mealieApiStatus: true,
  lastHeartbeat: null,
  recipeCount: 0,
  shoppingListCount: 0,
  mealPlanCount: 0
});

const testResult = ref({
  tested: false,
  success: false,
  error: ""
});

const bridgeLogs = ref<string[]>([]);

async function loadFirebaseSettings() {
  try {
    const { data } = await requests.get<any>("/api/admin/settings/firebase-bridge");
    if (data) {
      firebaseForm.value.enabled = data.enabled;
      firebaseForm.value.syncStrategy = data.syncStrategy;
      firebaseForm.value.mealieHostUrl = data.mealieHostUrl;
    }
  } catch (err) {
    console.error("Failed to load Firebase settings", err);
  }
}

async function fetchStatus() {
  try {
    const { data } = await requests.get<any>("/api/admin/settings/firebase-bridge/status");
    if (data) {
      syncStatus.value = data;
    }
  } catch (err) {
    console.error("Failed to load sync worker status", err);
  }
}

async function fetchLogs() {
  try {
    const { data } = await requests.get<string[]>("/api/admin/settings/firebase-bridge/logs");
    if (data) {
      bridgeLogs.value = data;
    }
  } catch (err) {
    console.error("Failed to fetch logs", err);
  }
}

async function saveFirebaseSettings() {
  state.saving = true;
  try {
    await requests.post("/api/admin/settings/firebase-bridge", firebaseForm.value);
    await loadFirebaseSettings();
    await fetchStatus();
  } catch (err: any) {
    console.error("Failed to save settings", err);
  } finally {
    state.saving = false;
  }
}

async function testFirebaseCredentials() {
  state.testing = true;
  testResult.value.tested = false;
  try {
    const { data } = await requests.post<any>("/api/admin/settings/firebase-bridge/test", {
      credentialsJson: firebaseForm.value.credentialsJson
    });
    if (data) {
      testResult.value.success = data.success;
      testResult.value.error = data.error || "";
    }
  } catch (err: any) {
    testResult.value.success = false;
    testResult.value.error = err.message || "Request failed";
  } finally {
    testResult.value.tested = true;
    state.testing = false;
  }
}

async function triggerSync() {
  state.syncing = true;
  try {
    await requests.post("/api/admin/settings/firebase-bridge/sync");
  } catch (err) {
    console.error("Failed to trigger sync", err);
  } finally {
    state.syncing = false;
  }
}

onMounted(async () => {
  await loadFirebaseSettings();
  await fetchStatus();
  await fetchLogs();
});

async function testEmail() {
  state.loading = true;
  state.tested = false;
  const { data } = await api.email.test({ email: state.address });
  if (data) {
    if (data.success) {
      state.success = true;
    }
    else {
      state.error = data.error ?? "";
      state.success = false;
    }
  }
  state.loading = false;
  state.tested = true;
}
const validEmail = computed(() => {
  if (state.address === "") {
    return false;
  }
  const valid = validators.email(state.address);
  // Explicit bool check because validators.email sometimes returns a string
  if (valid === true) {
    return true;
  }
  return false;
});
// ============================================================
// General About Info
const rawAppInfo = ref({
  version: "null",
  versionLatest: "null",
});
function getAppInfo() {
  const { data: statistics } = useAsyncData(useAsyncKey(), async () => {
    const { data } = await adminApi.about.about();
    if (data) {
      rawAppInfo.value.version = data.version;
      rawAppInfo.value.versionLatest = data.versionLatest;
      const prettyInfo = [
        {
          slot: "version",
          name: i18n.t("about.version"),
          icon: $globals.icons.information,
          value: data.version,
        },
        {
          slot: "build",
          name: i18n.t("settings.build"),
          icon: $globals.icons.information,
          value: data.buildId,
        },
        {
          name: i18n.t("about.application-mode"),
          icon: $globals.icons.devTo,
          value: data.production ? i18n.t("about.production") : i18n.t("about.development"),
        },
        {
          name: i18n.t("about.demo-status"),
          icon: $globals.icons.testTube,
          value: data.demoStatus ? i18n.t("about.demo") : i18n.t("about.not-demo"),
        },
        {
          name: i18n.t("about.api-port"),
          icon: $globals.icons.api,
          value: data.apiPort,
        },
        {
          name: i18n.t("about.api-docs"),
          icon: $globals.icons.file,
          value: data.apiDocs ? i18n.t("general.enabled") : i18n.t("general.disabled"),
        },
        {
          name: i18n.t("about.database-type"),
          icon: $globals.icons.database,
          value: data.dbType,
        },
        {
          name: i18n.t("about.database-url"),
          icon: $globals.icons.database,
          value: data.dbUrl,
        },
        {
          name: i18n.t("about.default-group"),
          icon: $globals.icons.group,
          value: data.defaultGroup,
        },
        {
          name: i18n.t("about.default-household"),
          icon: $globals.icons.household,
          value: data.defaultHousehold,
        },
        {
          slot: "recipe-scraper",
          name: i18n.t("settings.recipe-scraper-version"),
          icon: $globals.icons.primary,
          value: data.recipeScraperVersion,
        },
      ];
      return prettyInfo;
    }
    return data;
  });
  return statistics;
}
const appInfo = getAppInfo();
const bugReportDialog = ref(false);
const bugReportText = computed(() => {
  const ignore = {
    [i18n.t("about.database-url")]: true,
    [i18n.t("about.default-group")]: true,
  };
  let text = "**Details**\n";
  appInfo.value?.forEach((item) => {
    if (ignore[item.name as string]) {
      return;
    }
    text += `${item.name as string}: ${item.value as string}\n`;
  });
  const ignoreChecks: {
    [key: string]: boolean;
  } = {
    "application-version": true,
  };
  text += "\n**Checks**\n";
  simpleChecks.value.forEach((item) => {
    if (ignoreChecks[item.id]) {
      return;
    }
    const status = item.status ? i18n.t("general.yes") : i18n.t("general.no");
    text += `${item.text.toString()}: ${status}\n`;
  });
  text += `${i18n.t("settings.email-configured")}: ${appConfig.value.emailReady ? i18n.t("general.yes") : i18n.t("general.no")}\n`;
  return text;
});
</script>

<style scoped>
.wrap-word {
  white-space: normal;
  word-wrap: break-word;
}
</style>
