// Clean Program 11: Multi-Tier Nested Modal Scoping with Focus Restoration Stack
toggle parentModalOpen = false;
toggle childModalOpen = false;

Container(id="app-root", x=0, y=0) {
  Button(id="open-parent-btn", x=0, y=0, label="Open Settings", tabindex=1);

  Group(id="parent-dialog", x=50, y=50, modal=true, show_when=parentModalOpen) {
    Text(id="parent-title", x=50, y=50, label="Account Settings");
    Button(id="open-child-btn", x=50, y=80, label="Delete Account...", tabindex=2, focus_fallback="open-parent-btn");
    Button(id="parent-close-btn", x=150, y=80, label="Close Settings", tabindex=3, focus_fallback="open-parent-btn");

    Group(id="child-dialog", x=80, y=100, modal=true, show_when=parentModalOpen && childModalOpen) {
      Text(id="child-title", x=80, y=100, label="Confirm Permanent Deletion");
      Button(id="child-confirm-btn", x=80, y=130, label="Yes, Delete Permanently", tabindex=4, focus_fallback="open-parent-btn");
      Button(id="child-cancel-btn", x=220, y=130, label="Cancel", tabindex=5, focus_fallback="open-parent-btn");
    }
  }
}
