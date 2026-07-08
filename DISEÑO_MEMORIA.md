# Diseño de Memoria: Ownership y Borrowing para Synapse

## 1. Auditoría de Runtime

### `synapse_rt.c`
- `pool_alloc()`: reserva un bloque fijo dentro de un `MemoryPool` global protegido por mutex.
- `pool_free(void* ptr)`: libera el bloque dentro del pool si el puntero pertenece a la región administrada; de lo contrario, delega en `free(ptr)`.
- `_pool_malloc(size_t tamano)`: emplea `pool_alloc()` para asignaciones pequeñas (<= `TAMANO_BLOQUE`) y usa `malloc()` como fallback si el pool está agotado.

### Significado para el generador de código
- El generador puede renunciar a `malloc` directo para tipos administrados y usar un modelo de memoria administrada basada en el runtime.
- Debe insertar automáticamente llamadas a:
  - `pool_free(...)` al finalizar el scope para valores poseídos que no se transfieren.
  - `free(...)` para datos heap externos cuyo ciclo de vida no administra el pool.
- Para valores con owner explícito (`Tensor`, `CadenaSegura`, `Canal` y punteros nativos), el generador debe:
  - generar `pool_free()` cuando el propietario deja de vivir en su scope;
  - omitir la liberación si el valor es movido (`->`) a otro propietario;
  - generar el código de liberación correcto al regresar de funciones.

## 2. Reglas de Posesión (Borrow Checker)

### Reglas de Oro
1. Un valor tiene un único dueño activo en un momento dado.
2. Cuando el dueño sale de scope, el valor se libera automáticamente.
3. Se permiten múltiples préstamos inmutables simultáneos o un único préstamo mutable, pero no ambos.

### Semántica de Ownership
- Los valores `Tensor`, `CadenaSegura`, `Canal` y punteros de recursos son propietarios por defecto.
- La expresión `-> expr` en la firma de función o llamada indica transferencia de ownership.
- La asignación simple `x = y` para tipos poseídos debe comportarse como move semántico si `y` es un valor propietario, o como copia si el tipo lo permite explícitamente.

### Semántica de Borrowing
- Un préstamo inmutable crea una referencia de sólo lectura al valor original.
- Un préstamo mutable crea una referencia exclusiva que impide otros préstamos inmutables o mutables simultáneos.
- Los préstamos se invalidan cuando el dueño original sale de scope o cuando se produce una transferencia del dueño.

### Criterios para el analizador semántico
- Detectar `use after move`: uso de un valor después de que su ownership fue transferido.
- Detectar `double free`: generar error si un valor poseído es liberado dos veces.
- Detectar condiciones de préstamo inválidas:
  - préstamo mutable cuando ya existen préstamos inmutables activos;
  - préstamos múltiples cuando uno es mutable.
- Verificar que todos los valores poseídos terminen su scope con liberación o transferencia válida.

## 3. Extensión del AST y metadatos

### Metadatos recomendados para cada `NodoAST`
- `owner_id: entero` — identificador del propietario actual.
- `propietario: texto` — nombre simbólico del propietario.
- `is_owned: booleano` — indica si el nodo controla un recurso poseído.
- `es_prestado_inmutable: booleano` — true si el nodo representa un borrow inmutable.
- `es_prestado_mutable: booleano` — true si el nodo representa un borrow mutable.
- `lifetime_inicio: entero` — índice de scope o token donde inicia la vida.
- `lifetime_fin: entero` — índice de scope o token donde debe terminar la vida.
- `scope_id: entero` — scope léxico donde el valor vive.
- `borrow_count: entero` — conteo de préstamos inmutables activos.
- `has_mutable_borrow: booleano` — marca si hay un préstamo mutable activo.

### Metadatos específicos de nodos clave
- `Parametro`:
  - `es_transferencia: booleano` (ya existe en AST actual)
  - `es_prestamo: booleano` — indica si el parámetro recibe un borrow.
- `AsignacionVariable`:
  - `assigned_owner: texto` — nombre del dueño tras la asignación.
  - `is_move: booleano` — true si la operación transferirá ownership.
- `ArgumentoTransferido`:
  - `es_transferencia: booleano` — ya presente; clave para tracking de moves.
- `DefinicionFuncion`:
  - `retains_ownership: booleano` — si la función consume ownership de sus argumentos.
- `ExprObtenerDireccion` / `ExprDereferencia`:
  - `reference_kind: texto` — `inmutable` o `mutable`.

### Propuesta de modificación en `parser.syn`
- El parser debe anexar metadata en el momento de construir cada nodo.
- Para cada declaración de variable y cada parámetro de función se debe generar un `owner_id` único.
- Los nodos de expresión que devuelven referencias deben marcar `es_prestado_inmutable` o `es_prestado_mutable`.
- El propio `Nodo` base puede ampliarse con campos compatibles con este tracking:

```synapse
estructura Nodo:
    tipo: texto
    owner_id: entero
    propietario: texto
    is_owned: booleano
    es_prestado_inmutable: booleano
    es_prestado_mutable: booleano
    lifetime_inicio: entero
    lifetime_fin: entero
    scope_id: entero
    borrow_count: entero
    has_mutable_borrow: booleano
```

### Cómo usar estos metadatos durante el análisis
- `parsear_sentencia` y `parsear_expresion` asignan `scope_id` y `lifetime_inicio`.
- El analizador semántico crea un gráfico de ownership por scope.
- En `ArgumentoTransferido`, el AST marca `is_owned=false` para el original y `is_owned=true` para el receptor.
- `AsignacionVariable` actualiza `borrow_count` y verifica reglas de préstamo.

## 4. Recomendaciones para el generador de código

### Inserción automática de llamadas runtime
- En la generación de funciones, al cerrar un scope:
  - liberar con `pool_free(...)` los recursos de los nodos con `is_owned=true` que no hayan sido movidos.
  - no liberar los recursos cuyos nodos tengan `is_prestado_* = true`.
- En transferencias (`->`):
  - remover la liberación del origen en el scope original.
  - marcar el destino como nuevo propietario.
- En `return` con ownership:
  - determinar si el valor sale del scope y, de ser así, no liberar en el scope local.

### Tipos a rastrear
- `Tensor` y `tensor`
- `CadenaSegura` / `texto`
- `Canal` y recursos de archivo
- punteros crudos y `ExprObtenerDireccion` / `ExprDereferencia`

## 5. Conclusión del diseño

Este diseño habilita un Borrow Checker basado en el AST actual, apoyado por metadata de ownership y lifetime.
El runtime ya provee un pool seguro para las liberaciones, de modo que el siguiente paso es instrumentar el analizador semántico y el generador para que:
- construyan y validen gráficos de ownership,
- declaren préstamos inmutables/mutuables,
- inserten `pool_free` en los puntos correctos del código generado.
