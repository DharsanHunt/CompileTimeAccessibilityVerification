// Buggy Program 14: State-Transition Focus Trap (Fallback target hidden in destination state)
toggle filterActive = false;
toggle detailsOpen = true;

Container(id="switch-root", x=0, y=0) {
  Button(id="switch-btn-1", x=10, y=10, label="Step 1: Select Category", tabindex=1);
  Group(id="filter-drawer", x=10, y=60, show_when=filterActive) {
    Button(id="switch-btn-filter-apply", x=10, y=70, label="Apply Selection", tabindex=2, focus_fallback="switch-btn-1");
  }
  Group(id="details-panel", x=10, y=120, show_when=detailsOpen) {
    // DEFECT: focus_fallback points to 'switch-btn-filter-apply', which is invisible when detailsOpen closes and filterActive is false!
    Button(id="switch-btn-close-details", x=10, y=130, label="Close Details", tabindex=3, focus_fallback="switch-btn-filter-apply");
  }
}
