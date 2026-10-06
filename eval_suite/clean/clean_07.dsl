// Clean Program 7: Checkout Multi-Step Wizard (2 toggles, 11 elements)
toggle stepShipping = true;
toggle stepPayment = false;

Container(id="wizard-container", x=0, y=0) {
  Button(id="step-1-indicator", x=0, y=0, label="Step 1: Shipping", tabindex=1);
  Button(id="step-2-indicator", x=150, y=0, label="Step 2: Payment", tabindex=2);
  Group(id="shipping-section", x=0, y=50, show_when=stepShipping) {
    Input(id="street-address", x=0, y=50, label="Street Address", tabindex=3, focus_fallback="step-1-indicator");
    Input(id="postal-code", x=0, y=90, label="Postal Code", tabindex=4, focus_fallback="step-1-indicator");
    Button(id="to-payment-btn", x=0, y=130, label="Continue to Payment", tabindex=5, focus_fallback="step-1-indicator");
  }
  Group(id="payment-section", x=0, y=50, show_when=stepPayment) {
    Input(id="card-number", x=0, y=50, label="Credit Card Number", tabindex=3, focus_fallback="step-2-indicator");
    Button(id="complete-order-btn", x=0, y=90, label="Place Order", tabindex=4, focus_fallback="step-2-indicator");
  }
}
