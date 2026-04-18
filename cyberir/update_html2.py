import codecs
path = 'c:/Users/PDM/Pictures/CYBER/cyberir/frontend/templates/base.html'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

script_inj = '''  <script>
    if (localStorage.getItem('sidebarCollapsed') === 'true') {
      document.documentElement.classList.add('sidebar-collapsed');
    }
  </script>
</head>'''
text = text.replace('</head>', script_inj)

old_btn = '''        <button class="mobile-menu-btn" id="mobileMenuBtn"\n          style="display:none;background:none;border:none;font-size:1.4rem;cursor:pointer;padding:4px 8px;margin-right:10px;">☰</button>'''
new_btn = '''        <button class="sidebar-menu-btn" id="sidebarToggleBtn"\n          style="background:none;border:none;font-size:1.4rem;cursor:pointer;padding:4px 8px;margin-right:10px;color:var(--text-primary);display:flex;">☰</button>'''
text = text.replace(old_btn, new_btn)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(text)
print('Updated base.html')
