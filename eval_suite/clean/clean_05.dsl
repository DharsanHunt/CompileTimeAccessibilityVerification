// Clean Program 5: Settings Drawer (1 toggle, 8 elements)
toggle drawerOpen = false;

Container(id="settings-page", x=0, y=0) {
  Button(id="toggle-drawer-btn", x=0, y=0, label="Open Settings Drawer", tabindex=1);
  Text(id="page-heading", x=180, y=0, label="User Dashboard");
  Group(id="drawer", x=0, y=50, show_when=drawerOpen) {
    Text(id="drawer-heading", x=0, y=50, label="Preferences");
    Button(id="btn-dark-mode", x=0, y=80, label="Toggle Dark Theme", tabindex=2, focus_fallback="toggle-drawer-btn");
    Button(id="btn-notifications", x=0, y=120, label="Toggle Notifications", tabindex=3, focus_fallback="toggle-drawer-btn");
    Button(id="close-drawer-btn", x=0, y=160, label="Close Drawer", tabindex=4, focus_fallback="toggle-drawer-btn");
  }
}
