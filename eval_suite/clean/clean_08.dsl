// Clean Program 8: Dropdown Action Menu (1 toggle, 7 elements)
toggle menuOpen = false;

Container(id="action-menu-root", x=0, y=0) {
  Button(id="menu-trigger", x=0, y=0, label="Actions Menu", tabindex=1);
  Text(id="item-name", x=140, y=0, label="Selected File: report.pdf");
  Group(id="menu-popup", x=0, y=40, show_when=menuOpen) {
    Button(id="act-rename", x=0, y=40, label="Rename File", tabindex=2, focus_fallback="menu-trigger");
    Button(id="act-duplicate", x=0, y=70, label="Duplicate File", tabindex=3, focus_fallback="menu-trigger");
    Button(id="act-delete", x=0, y=100, label="Delete File", tabindex=4, focus_fallback="menu-trigger");
  }
}
