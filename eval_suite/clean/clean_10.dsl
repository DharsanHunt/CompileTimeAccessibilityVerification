// Clean Program 10: Multi-State Dashboard (3 toggles, 14 elements)
toggle navDrawerOpen = false;
toggle notifTrayOpen = false;
toggle quickSearchOpen = false;

Container(id="dashboard-root", x=0, y=0) {
  Button(id="btn-nav-toggle", x=0, y=0, label="Toggle Navigation", tabindex=1);
  Button(id="btn-search-toggle", x=200, y=0, label="Quick Search", tabindex=2);
  Button(id="btn-notif-toggle", x=400, y=0, label="Notification Feed", tabindex=3);

  Group(id="nav-drawer", x=0, y=50, show_when=navDrawerOpen) {
    Text(id="nav-header", x=0, y=50, label="Navigation Menu");
    Button(id="nav-home", x=0, y=70, label="Dashboard Home", tabindex=4, focus_fallback="btn-nav-toggle");
    Button(id="nav-reports", x=0, y=100, label="Reports & Analytics", tabindex=7, focus_fallback="btn-nav-toggle");
  }

  Group(id="search-tray", x=200, y=50, show_when=quickSearchOpen) {
    Input(id="search-input-box", x=200, y=70, label="Search everything...", tabindex=5, focus_fallback="btn-search-toggle");
    Button(id="search-exec-btn", x=200, y=100, label="Execute Search", tabindex=8, focus_fallback="btn-search-toggle");
  }

  Group(id="notif-tray", x=400, y=50, show_when=notifTrayOpen) {
    Text(id="notif-header", x=400, y=50, label="Recent Alerts");
    Button(id="btn-clear-all-notifs", x=400, y=70, label="Clear All Notifications", tabindex=6, focus_fallback="btn-notif-toggle");
  }
}
