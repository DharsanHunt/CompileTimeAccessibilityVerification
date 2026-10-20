// Clean Program 14: Switch-Access Optimized UI (Short Jumps < 150px)
@profile switch-access-first;

toggle filterActive = false;

Container(id="switch-root", x=0, y=0) {
  Button(id="switch-btn-1", x=10, y=10, label="Step 1: Select Category", tabindex=1);
  Button(id="switch-btn-2", x=10, y=60, label="Step 2: Choose Filter", tabindex=2);
  Group(id="filter-drawer", x=10, y=110, show_when=filterActive) {
    Button(id="switch-btn-filter-apply", x=10, y=120, label="Apply Selection", tabindex=3, focus_fallback="switch-btn-2");
  }
  Button(id="switch-btn-3", x=10, y=170, label="Step 3: Confirm Submission", tabindex=4);
}
