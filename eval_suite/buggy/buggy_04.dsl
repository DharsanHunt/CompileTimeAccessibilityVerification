// Buggy Program 4: Unindexed and Positive Tabindex Mismatch (Static)
// WCAG 2.4.3: btn-first has no tabindex (treated as 0/default), but btn-second has tabindex=1,
// causing focus to jump to btn-second first before jumping back up to btn-first.
Container(id="nav-strip", x=0, y=0) {
  Button(id="btn-first", x=0, y=0, label="Home");
  Button(id="btn-second", x=120, y=0, label="Profile", tabindex=1);
}
