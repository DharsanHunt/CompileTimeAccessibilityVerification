// Clean Program 3: Tab Navigation System (2 toggles, 8 elements)
toggle tabGeneral = true;
toggle tabSecurity = false;

Container(id="tabs-root", x=0, y=0) {
  Button(id="tab-btn-1", x=0, y=0, label="General Tab", tabindex=1);
  Button(id="tab-btn-2", x=120, y=0, label="Security Tab", tabindex=2);
  Group(id="panel-general", x=0, y=60, show_when=tabGeneral && !tabSecurity) {
    Text(id="gen-header", x=0, y=60, label="General Settings");
    Input(id="display-name", x=0, y=90, label="Display Name", tabindex=3, focus_fallback="tab-btn-1");
  }
  Group(id="panel-security", x=0, y=60, show_when=tabSecurity && !tabGeneral) {
    Text(id="sec-header", x=0, y=60, label="Security Configuration");
    Button(id="btn-2fa", x=0, y=90, label="Enable Two-Factor Auth", tabindex=3, focus_fallback="tab-btn-2");
  }
}
