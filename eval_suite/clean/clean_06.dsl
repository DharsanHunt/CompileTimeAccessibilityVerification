// Clean Program 6: Search & Filter Grid (2 toggles, 10 elements)
toggle filterOpen = false;
toggle searchFocused = false;

Container(id="search-view", x=0, y=0) {
  Input(id="query-input", x=0, y=0, label="Search documents", tabindex=1);
  Button(id="toggle-filters-btn", x=220, y=0, label="Filter options", tabindex=2);
  Group(id="filter-panel", x=0, y=50, show_when=filterOpen) {
    Text(id="filter-title", x=0, y=50, label="Refine Search");
    Button(id="filter-recent", x=0, y=80, label="Last 7 Days", tabindex=3, focus_fallback="toggle-filters-btn");
    Button(id="filter-starred", x=120, y=80, label="Starred Only", tabindex=4, focus_fallback="toggle-filters-btn");
    Button(id="clear-filters-btn", x=240, y=80, label="Reset Filters", tabindex=5, focus_fallback="toggle-filters-btn");
  }
}
