// Clean Program 2: Login Dialog (1 toggle, 7 elements)
toggle loginOpen = false;

Container(id="page-root", x=0, y=0) {
  Button(id="open-login-btn", x=0, y=0, label="Log in to account", tabindex=1);
  Text(id="welcome-banner", x=150, y=0, label="Welcome to Portal");
  Group(id="login-dialog", x=50, y=100, show_when=loginOpen) {
    Text(id="login-title", x=50, y=100, label="Account Credentials");
    Input(id="username-input", x=50, y=140, label="Username", tabindex=2, focus_fallback="open-login-btn");
    Input(id="password-input", x=50, y=180, label="Password", tabindex=3, focus_fallback="open-login-btn");
    Button(id="submit-login-btn", x=50, y=220, label="Sign In", tabindex=4, focus_fallback="open-login-btn");
  }
}
