// Clean Program 1: Expandable Toolbar (1 toggle, 6 elements)
toggle toolsExpanded = false;

Container(id="toolbar-root", x=0, y=0) {
  Button(id="btn-edit", x=0, y=0, label="Edit document", tabindex=1);
  Button(id="btn-save", x=100, y=0, label="Save document", tabindex=2);
  Button(id="btn-more", x=200, y=0, label="More tools", tabindex=3);
  Group(id="extra-tools", x=0, y=50, show_when=toolsExpanded) {
    Button(id="btn-export", x=0, y=50, label="Export as PDF", tabindex=4, focus_fallback="btn-more");
    Button(id="btn-print", x=100, y=50, label="Print document", tabindex=5, focus_fallback="btn-more");
  }
}
