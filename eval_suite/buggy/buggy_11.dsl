// Buggy Program 11: Nested Modal Focus Trap Defect (Child confirmation missing fallback)
toggle parentModalOpen = false;
toggle childModalOpen = false;

Container(id="app-root", x=0, y=0) {
  Button(id="open-parent-btn", x=0, y=0, label="Open Settings", tabindex=1);

  Group(id="parent-dialog", x=50, y=50, modal=true, show_when=parentModalOpen) {
    Button(id="open-child-btn", x=50, y=80, label="Delete Account...", tabindex=2, focus_fallback="open-parent-btn");

    Group(id="child-dialog", x=80, y=100, modal=true, show_when=parentModalOpen && childModalOpen) {
      // DEFECT: child-confirm-btn has NO focus_fallback when childModalOpen flips to false!
      Button(id="child-confirm-btn", x=80, y=130, label="Yes, Delete Permanently", tabindex=3);
    }
  }
}
