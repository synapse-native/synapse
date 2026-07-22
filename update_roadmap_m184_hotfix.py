import sys

with open('ROADMAP.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Update M18.4 status to include hotfix
old = 'M18.2/3 cimientos + M18.4 Ed25519. Verificacion de firma via TweetNaCl'
new = 'M18.4: Ed25519 + Hotfix. Tolerancia Cero autor vacío, TOML cleanup, wrapper seguro'

if old in content:
    content = content.replace(old, new, 1)
    print('Updated description')

# Add hotfix note
old_desc = 'Runtime 878KB (binario completo).'
new_desc = 'Runtime 878KB (binario completo). Hotfix: Tolerancia Cero autor invalido, _toml_nodo_liberar via wrapper _syn_axon_limpiar_toml.'

if old_desc in content:
    content = content.replace(old_desc, new_desc, 1)
    print('Updated runtime description')

with open('ROADMAP.md', 'w', encoding='utf-8') as f:
    f.write(content)

print('=== ROADMAP UPDATED ===')
