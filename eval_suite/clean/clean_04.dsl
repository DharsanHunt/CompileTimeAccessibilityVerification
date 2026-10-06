// Clean Program 4: FAQ Accordion Panels (2 toggles, 9 elements)
toggle faq1Open = false;
toggle faq2Open = false;

Container(id="faq-root", x=0, y=0) {
  Button(id="faq-header-1", x=0, y=0, label="What is A11yCC?", tabindex=1);
  Group(id="faq-body-1", x=0, y=40, show_when=faq1Open) {
    Text(id="faq-text-1", x=0, y=40, label="An a11y verification compiler.");
    Button(id="faq-link-1", x=0, y=70, label="Read Docs", tabindex=2, focus_fallback="faq-header-1");
  }
  Button(id="faq-header-2", x=0, y=110, label="How does state-space checking work?", tabindex=3);
  Group(id="faq-body-2", x=0, y=150, show_when=faq2Open) {
    Text(id="faq-text-2", x=0, y=150, label="It checks all 2^k reachable states.");
    Button(id="faq-link-2", x=0, y=180, label="View Spec", tabindex=4, focus_fallback="faq-header-2");
  }
}
