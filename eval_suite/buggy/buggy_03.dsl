// Buggy Program 3: Column Order Mismatch (Static)
// WCAG 2.4.3: Visual reading order is left-to-right, top-to-bottom, but tab jumps randomly across columns
Container(id="two-column-layout", x=0, y=0) {
  Button(id="col1-row1", x=0, y=0, label="Col 1 Top", tabindex=4);
  Button(id="col2-row1", x=200, y=0, label="Col 2 Top", tabindex=1);
  Button(id="col1-row2", x=0, y=60, label="Col 1 Bottom", tabindex=2);
  Button(id="col2-row2", x=200, y=60, label="Col 2 Bottom", tabindex=3);
}
