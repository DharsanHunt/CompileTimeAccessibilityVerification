// Clean Program 9: Product Card Grid (1 toggle, 9 elements)
toggle detailsOpen = false;

Container(id="catalog-root", x=0, y=0) {
  Text(id="product-title", x=0, y=0, label="Accessibility Auditing Suite");
  Button(id="toggle-details-btn", x=0, y=30, label="View Specifications", tabindex=1);
  Button(id="buy-btn", x=160, y=30, label="Purchase License", tabindex=2);
  Group(id="spec-panel", x=0, y=70, show_when=detailsOpen) {
    Text(id="spec-text-1", x=0, y=70, label="WCAG 2.1 AA Compliance");
    Text(id="spec-text-2", x=0, y=95, label="Deterministic Verification Engine");
    Button(id="download-datasheet-btn", x=0, y=125, label="Download Datasheet PDF", tabindex=3, focus_fallback="toggle-details-btn");
  }
}
