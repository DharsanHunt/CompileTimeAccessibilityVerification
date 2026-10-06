// Buggy Program 8: Modal Close Vanishing Focus (State-Dependent Transition Defect)
// WCAG 2.4.3, 2.1.2: Modal close button disappears on modalOpen: true -> false with no focus_fallback
toggle modalOpen = true;

Container(id="modal-root", x=0, y=0) {
  Button(id="open-modal-trigger", x=0, y=0, label="Open Help Modal", tabindex=1);
  Group(id="modal-window", x=50, y=50, show_when=modalOpen) {
    Text(id="modal-heading", x=50, y=50, label="Help Center");
    Button(id="modal-close-action", x=50, y=90, label="Close Help", tabindex=2);
  }
}
