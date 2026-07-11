import './theme.css';
import { router } from './router';
import type { Route } from './router';
import { diagnostics } from './data/diagnostics';
import { renderDashboardView, attachDashboardListeners } from './ui/dashboard';
import { renderSettingsView, attachSettingsListeners } from './ui/settings';
import { renderRecipesListView, attachRecipesListeners, resetRecipeSelection } from './ui/recipes';
import { renderListsView, attachListsListeners, resetListsSelection } from './ui/lists';

// State management
let hostUrl = localStorage.getItem('mealie_host') || 'http://localhost:9091';

// Elements
const appDiv = document.getElementById('app')!;

function renderHeader(title: string, showLogout = false) {
  return `
    <header>
      <h1>${title}</h1>
      ${showLogout ? `<button id="header-logout-btn" class="btn" style="padding: 6px 12px; font-size: 0.875rem; background: var(--surface-variant);">Logout</button>` : ''}
    </header>
  `;
}

function renderNavBar(activeRoute: Route) {
  const navItems: { route: Route; label: string; icon: string }[] = [
    {
      route: 'dashboard',
      label: 'Home',
      icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`
    },
    {
      route: 'recipes',
      label: 'Recipes',
      icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`
    },
    {
      route: 'lists',
      label: 'Lists',
      icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>`
    },
    {
      route: 'settings',
      label: 'Settings',
      icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`
    }
  ];

  return `
    <nav class="nav-bar">
      ${navItems
        .map(
          (item) => `
        <div class="nav-item ${activeRoute === item.route ? 'active' : ''}" data-route="${item.route}">
          ${item.icon}
          <span>${item.label}</span>
        </div>
      `
        )
        .join('')}
    </nav>
  `;
}

function renderLogin() {
  appDiv.innerHTML = `
    <div class="login-container">
      <div class="login-header">
        <h1 class="login-title">Mealie Companion</h1>
        <p class="login-subtitle">Sign in to access your recipes and lists</p>
      </div>
      <div id="login-error" class="error-alert" style="display: none;"></div>
      <form id="login-form" class="card">
        <div class="form-group">
          <label class="form-label" for="host">Mealie Server Host</label>
          <input class="form-input" type="url" id="host" value="${hostUrl}" required placeholder="http://192.168.1.x:9091" />
        </div>
        <div class="form-group">
          <label class="form-label" for="username">Username / Email</label>
          <input class="form-input" type="text" id="username" required placeholder="chef" />
        </div>
        <div class="form-group">
          <label class="form-label" for="password">Password</label>
          <input class="form-input" type="password" id="password" required placeholder="••••••••" />
        </div>
        <button type="submit" class="btn" style="margin-top: 8px;">Sign In</button>
      </form>
    </div>
  `;

  const form = document.getElementById('login-form') as HTMLFormElement;
  const errorAlert = document.getElementById('login-error') as HTMLDivElement;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorAlert.style.display = 'none';

    const inputHost = (document.getElementById('host') as HTMLInputElement).value.trim();
    const inputUsername = (document.getElementById('username') as HTMLInputElement).value.trim();
    const inputPassword = (document.getElementById('password') as HTMLInputElement).value;

    hostUrl = inputHost.endsWith('/') ? inputHost.slice(0, -1) : inputHost;
    localStorage.setItem('mealie_host', hostUrl);

    try {
      const response = await fetch(`${hostUrl}/api/auth/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
          username: inputUsername,
          password: inputPassword
        })
      });

      if (!response.ok) {
        throw new Error(response.status === 401 ? 'Invalid username or password' : 'Failed to connect to server');
      }

      const data = await response.json();
      localStorage.setItem('mealie_token', data.access_token);
      diagnostics.checkReachability();
      router.navigate('dashboard');
    } catch (err: any) {
      errorAlert.textContent = err.message || 'An unexpected error occurred';
      errorAlert.style.display = 'block';
    }
  });
}

function handleLogout() {
  localStorage.removeItem('mealie_token');
  router.navigate('login');
}

async function renderRoute(route: Route) {
  if (route === 'login') {
    renderLogin();
    return;
  }

  let contentHtml = '';

  switch (route) {
    case 'dashboard':
      contentHtml = await renderDashboardView();
      break;
    case 'recipes':
      contentHtml = await renderRecipesListView();
      break;
    case 'lists':
      contentHtml = await renderListsView();
      break;
    case 'settings':
      contentHtml = await renderSettingsView();
      break;
  }

  appDiv.innerHTML = `
    ${renderHeader(route.charAt(0).toUpperCase() + route.slice(1), true)}
    <main>
      ${contentHtml}
    </main>
    ${renderNavBar(route)}
  `;

  // Attach nav events
  document.querySelectorAll('.nav-item').forEach((item) => {
    item.addEventListener('click', (e) => {
      const targetRoute = (e.currentTarget as HTMLElement).getAttribute('data-route') as Route;
      resetRecipeSelection();
      resetListsSelection();
      router.navigate(targetRoute);
    });
  });

  // Attach header logout event
  const headerLogout = document.getElementById('header-logout-btn');
  if (headerLogout) {
    headerLogout.addEventListener('click', handleLogout);
  }

  // View specific listeners
  if (route === 'dashboard') {
    attachDashboardListeners();
  } else if (route === 'recipes') {
    attachRecipesListeners(() => renderRoute('recipes'));
  } else if (route === 'lists') {
    attachListsListeners(() => renderRoute('lists'));
  } else if (route === 'settings') {
    attachSettingsListeners(() => renderRoute('settings'));
  }
}

// Subscribe to routing changes
router.onRouteChanged((route) => {
  renderRoute(route);
});

// Bootstrap
diagnostics.requestPersistence();
diagnostics.checkReachability();
router.initialize();
renderRoute(router.getRoute());
