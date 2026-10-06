// Clean E-Commerce Cart with Accessible Collapsible Drawer
toggle cartDrawerOpen = false;

Container(id="store-root", x=0, y=0) {
  Button(id="browse-btn", x=0, y=0, label="Browse Catalog", tabindex=1);
  Button(id="open-cart-btn", x=180, y=0, label="View Cart", tabindex=2);

  Group(id="cart-drawer", x=0, y=55, show_when=cartDrawerOpen) {
    Text(id="cart-header", x=0, y=55, label="Shopping Cart Summary");
    Input(id="promo-code", x=0, y=85, label="Enter Promo Code", tabindex=3, focus_fallback="open-cart-btn");
    Button(id="checkout-btn", x=220, y=85, label="Proceed to Checkout", tabindex=4, focus_fallback="open-cart-btn");
    Button(id="close-cart-btn", x=0, y=135, label="Close Cart Drawer", tabindex=5, focus_fallback="open-cart-btn");
  }
}
