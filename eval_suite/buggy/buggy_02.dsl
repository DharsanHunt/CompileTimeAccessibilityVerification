// Buggy Program 2: Scrambled Form Tab Order (Static)
// WCAG 2.4.3: Three vertically stacked inputs with scrambled tabindex (3, 1, 2)
Container(id="scrambled-form", x=0, y=0) {
  Input(id="field-first-name", x=0, y=0, label="First Name", tabindex=3);
  Input(id="field-last-name", x=0, y=50, label="Last Name", tabindex=1);
  Input(id="field-email", x=0, y=100, label="Email Address", tabindex=2);
}
