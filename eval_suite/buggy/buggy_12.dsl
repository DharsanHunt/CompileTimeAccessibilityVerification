// Buggy Program 12: Enterprise Multi-Toggle Dashboard (8 toggles) with Missing Accessible Label
toggle t0 = false;
toggle t1 = false;
toggle t2 = false;
toggle t3 = false;
toggle t4 = false;
toggle t5 = false;
toggle t6 = false;
toggle t7 = false;

Container(id="enterprise-root", x=0, y=0) {
  Button(id="btn-master-menu", x=0, y=0, label="Global Menu", tabindex=1);

  Group(id="cluster-panel", x=0, y=40, show_when=t0 && t1) {
    // DEFECT: cluster-action-unlabeled is missing required label attribute!
    Button(id="cluster-action-unlabeled", x=0, y=40, tabindex=2, focus_fallback="btn-master-menu");
  }
}
