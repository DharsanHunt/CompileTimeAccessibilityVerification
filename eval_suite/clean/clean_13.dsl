// Clean Program 13: Transpiled React Modal Component Output
toggle isOpen = false;

Container(id="react-root", x=0, y=0) {
  Button(id="open-btn", x=0, y=0, label="Open Alerts", tabindex=1);
  Group(id="alert-modal", x=0, y=40, modal=true, show_when=isOpen, focus_fallback="open-btn") {
    Button(id="close-btn", x=0, y=70, label="Dismiss", tabindex=2, focus_fallback="open-btn");
    Text(id="alert-msg", x=0, y=110, label="You have 3 unread messages.");
  }
}
