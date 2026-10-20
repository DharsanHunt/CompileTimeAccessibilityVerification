// Clean Program 15: Accordion Component with Multi-Section Fallback Synchronization
toggle sec1Open = true;
toggle sec2Open = false;

Container(id="accordion-root", x=0, y=0) {
  Button(id="acc-hdr-1", x=0, y=0, label="Section 1: General Info", tabindex=1);
  Group(id="acc-body-1", x=0, y=40, show_when=sec1Open) {
    Input(id="acc-input-name", x=0, y=50, label="Full Legal Name", tabindex=2, focus_fallback="acc-hdr-1");
    Button(id="acc-save-1", x=0, y=90, label="Save Section 1", tabindex=3, focus_fallback="acc-hdr-1");
  }

  Button(id="acc-hdr-2", x=0, y=140, label="Section 2: Payment Details", tabindex=4);
  Group(id="acc-body-2", x=0, y=180, show_when=sec2Open) {
    Input(id="acc-input-card", x=0, y=190, label="Credit Card Number", tabindex=5, focus_fallback="acc-hdr-2");
    Button(id="acc-save-2", x=0, y=230, label="Authorize Payment", tabindex=6, focus_fallback="acc-hdr-2");
  }
}
