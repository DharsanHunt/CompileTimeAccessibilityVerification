// Buggy E-Commerce Cart: Close button missing focus_fallback
// WCAG 2.1.2 & 2.4.3: Focus lost to document root when cart closes!
toggle cartDrawerOpen = true;

Container(id="store-root", x=0, y=0) {
  Button(id="browse-btn", x=0, y=0, label="Browse Catalog", tabindex=1);
  Button(id="open-cart-btn", x=180, y=0, label="View Cart", tabindex=2);

  Group(id="cart-drawer", x=0, y=55, show_when=cartDrawerOpen) {
    Text(id="cart-header", x=0, y=55, label="Shopping Cart Summary");
    Button(id="close-cart-btn", x=0, y=95, label="Close Cart Drawer", tabindex=3);
  }
}
