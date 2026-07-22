import sys

with open('ROADMAP.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Update F18 status line
old = 'F18: Axon gestor de paquetes** | 🟢 **M18.3 COMPLETADO**'
new = 'F18: Axon gestor de paquetes** | 🟢 **M18.4 COMPLETADO**'

if old in content:
    content = content.replace(old, new, 1)
    print('Updated F18 version')
else:
    print('WARNING: F18 version not found')

# Update the description
old_desc = 'M18.2 cimientos + M18.3 HTTP/TAR/Lock. Red nativa'
new_desc = 'M18.2/3 cimientos + M18.4 Ed25519. Verificacion de firma via TweetNaCl'

if old_desc in content:
    content = content.replace(old_desc, new_desc, 1)
    print('Updated description')
else:
    print('WARNING: Description not found')

# Update micro-entregable section
old_m = '### Micro-entregable M18.3 — Red nativa + TAR + axon.lock'
new_m = '### Micro-entregable M18.4 — Verificacion Ed25519 de paquetes'

if old_m in content:
    content = content.replace(old_m, new_m, 1)
    print('Updated micro-entregable title')
else:
    print('WARNING: Micro-entregable title not found')

with open('ROADMAP.md', 'w', encoding='utf-8') as f:
    f.write(content)

print('=== ROADMAP UPDATED ===')
