from pathlib import Path
S=Path('vendor/NetHack-NetHack-3.6.7_Released')
p=S/'src/cmd.c';s=p.read_text();a='    flush_screen(1); /* Flush screen buffer. Put the cursor on the hero. */';assert s.count(a)==1;s=s.replace(a,a+'\n    if (getenv("BH_EVENTS")) {\n        (void) printf("\\033]777;command\\007");\n        (void) fflush(stdout);\n    }');p.write_text(s)
p=S/'win/tty/wintty.c';s=p.read_text();a='    bh_event("input", 0);';s=s.replace(a,a+'\n    if (getenv("BH_EVENTS")) (void) printf("\\033]777;input\\007");');p.write_text(s)
