// Buggy Program 6: Unlabeled Form Input Field (Static)
// WCAG 4.1.2: Input element lacking a label attribute
Container(id="feedback-form", x=0, y=0) {
  Text(id="form-title", x=0, y=0, label="User Feedback");
  Input(id="feedback-text-input", x=0, y=30, tabindex=1);
  Button(id="send-feedback-btn", x=0, y=80, label="Submit Feedback", tabindex=2);
}
