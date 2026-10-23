#!/bin/bash
# install.sh — punto de entrada del instalador del paquete en la raíz del
# árbol del bundle. Delega al instalador real instaladores/linux/install.sh
# cumpliendo Manual 7 §2.3.
# cumple Manual 9 §4.1: distribución para Linux — el instalador debe existir
# en la raíz del paquete.
exec bash "$(dirname "$0")/instaladores/linux/install.sh" "$@"
