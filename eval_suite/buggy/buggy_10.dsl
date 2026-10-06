// Buggy Program 10: Multi-Toggle Filter Cascading Focus Trap (State-Dependent Transition Defect)
// WCAG 2.4.3, 2.1.2: advanced-keyword input vanishes when filterPanelOpen: true -> false with no fallback
toggle filterPanelOpen = true;
toggle advancedSearch = true;

Container(id="catalog-filter-app", x=0, y=0) {
  Button(id="toggle-filter-btn", x=0, y=0, label="Show/Hide Filters", tabindex=1);
  Group(id="filter-container", x=0, y=50, show_when=filterPanelOpen) {
    Button(id="toggle-adv-btn", x=0, y=50, label="Advanced Filters", tabindex=2, focus_fallback="toggle-filter-btn");
    Group(id="adv-fields", x=0, y=90, show_when=advancedSearch) {
      Input(id="advanced-keyword", x=0, y=90, label="Keywords", tabindex=3);
    }
  }
}
