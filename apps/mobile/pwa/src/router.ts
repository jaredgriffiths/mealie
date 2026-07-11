export type Route = 'login' | 'dashboard' | 'recipes' | 'lists' | 'settings';

export class Router {
  private currentRoute: Route = 'login';
  private routeListeners: ((route: Route) => void)[] = [];

  constructor() {
    // Listen to back button if needed
    window.addEventListener('popstate', (event) => {
      if (event.state && event.state.route) {
        this.navigateInternal(event.state.route, false);
      }
    });
  }

  public getRoute(): Route {
    return this.currentRoute;
  }

  public navigate(route: Route) {
    this.navigateInternal(route, true);
  }

  private navigateInternal(route: Route, pushState: boolean) {
    // Check authentication redirect
    const token = localStorage.getItem('mealie_token');
    let targetRoute = route;

    if (!token && route !== 'login') {
      targetRoute = 'login';
    } else if (token && route === 'login') {
      targetRoute = 'dashboard';
    }

    if (this.currentRoute === targetRoute) return;

    this.currentRoute = targetRoute;

    if (pushState) {
      window.history.pushState({ route: targetRoute }, '', `#${targetRoute}`);
    }

    this.routeListeners.forEach((listener) => listener(targetRoute));
  }

  public onRouteChanged(listener: (route: Route) => void) {
    this.routeListeners.push(listener);
  }

  public initialize() {
    const hash = window.location.hash.replace('#', '') as Route;
    const initialRoute: Route = ['login', 'dashboard', 'recipes', 'lists', 'settings'].includes(hash) ? hash : 'dashboard';
    this.navigateInternal(initialRoute, false);
  }
}

export const router = new Router();
