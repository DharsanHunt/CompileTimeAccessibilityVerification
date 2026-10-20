// Buggy Program 13: Transpiled React Component with Missing Accessible Label on Input
toggle isSearchOpen = true;

Container(id="react-root", x=0, y=0) {
  Button(id="search-toggle-btn", x=0, y=0, label="Search Bar", tabindex=1);
  Group(id="search-box", x=0, y=40, show_when=isSearchOpen) {
    // DEFECT: Input has NO label attribute (FR6 / WCAG 4.1.2)
    Input(id="search-query-field", x=0, y=40, tabindex=2, focus_fallback="search-toggle-btn");
  }
}
