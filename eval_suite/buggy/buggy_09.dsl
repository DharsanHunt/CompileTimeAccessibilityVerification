// Buggy Program 9: Collapsible Sidebar with Vanishing Fallback Target (State-Dependent Transition Defect)
// WCAG 2.4.3, 2.1.2: menu-item-1 declares fallback to menu-item-2, but menu-item-2 ALSO vanishes on sidebarOpen: true -> false!
toggle sidebarOpen = true;

Container(id="nav-layout", x=0, y=0) {
  Button(id="toggle-sidebar-btn", x=0, y=0, label="Toggle Sidebar Menu", tabindex=1);
  Group(id="collapsible-sidebar", x=0, y=50, show_when=sidebarOpen) {
    Button(id="menu-item-1", x=0, y=50, label="User Profile", tabindex=2, focus_fallback="menu-item-2");
    Button(id="menu-item-2", x=0, y=90, label="Account Settings", tabindex=3, focus_fallback="toggle-sidebar-btn");
  }
}
