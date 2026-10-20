// Buggy Program 15: Scrambled Tab Order Inversion (Focus Order Mismatch FR5 / WCAG 2.4.3)
Container(id="form-root", x=0, y=0) {
  // DEFECT: Top element given higher tabindex than bottom element, inverting natural tab flow
  Button(id="form-top-btn", x=0, y=0, label="Step 1: Top Option", tabindex=5);
  Button(id="form-mid-btn", x=0, y=50, label="Step 2: Middle Option", tabindex=2);
  Button(id="form-bot-btn", x=0, y=100, label="Step 3: Bottom Option", tabindex=1);
}
