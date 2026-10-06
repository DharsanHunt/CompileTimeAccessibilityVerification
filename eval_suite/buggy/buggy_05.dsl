// Buggy Program 5: Unlabeled Icon Button (Static)
// WCAG 4.1.2: Button element without a label attribute
Container(id="icon-toolbar", x=0, y=0) {
  Button(id="search-icon-btn", x=0, y=0, tabindex=1);
  Button(id="help-btn", x=80, y=0, label="Help & Support", tabindex=2);
}
