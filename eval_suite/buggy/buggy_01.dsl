// Buggy Program 1: Inverted Focus Order (Static)
// WCAG 2.4.3: Focus sequence jumps backwards from bottom to top
Container(id="form-root", x=0, y=0) {
  Button(id="top-action-btn", x=0, y=0, label="Save Draft", tabindex=2);
  Button(id="bottom-action-btn", x=0, y=80, label="Publish Now", tabindex=1);
}
