// Buggy Program 7: Dialog Buttons Missing Labels (Static)
// WCAG 4.1.2: Multiple interactive elements lacking accessible names
Container(id="alert-box", x=0, y=0) {
  Text(id="alert-msg", x=0, y=0, label="Are you sure you want to proceed?");
  Button(id="btn-confirm", x=0, y=40, tabindex=1);
  Button(id="btn-dismiss", x=100, y=40, tabindex=2);
}
