;; examples/syquex/counter/counter.wat
;; FASE 25 — SPA Ejemplo: Counter App en WebAssembly
;;
;; Este módulo WASM implementa un contador interactivo que:
;; - Importa funciones DOM de JavaScript (js_get_element_by_id, js_set_text, etc.)
;; - Exporta funciones para manipulación del contador (increment, decrement, reset)
;; - Usa memoria lineal para almacenar el valor del contador
;;
;; Compilar: wat2wasm counter.wat -o counter.wasm
;; Ejecutar: abrir index.html en navegador

(module
  ;; =====================================================================
  ;; Imports — Funciones DOM proporcionadas por JavaScript
  ;; =====================================================================

  ;; Obtener elemento por ID (retorna puntero al elemento)
  (import "env" "js_get_element_by_id"
    (func $js_get_element_by_id (param i32) (result i32)))

  ;; Establecer texto de un elemento
  (import "env" "js_set_text"
    (func $js_set_text (param i32 i32)))

  ;; Obtener el valor de un input como entero
  (import "env" "js_get_input_value"
    (func $js_get_input_value (param i32) (result i32)))

  ;; Mostrar alerta
  (import "env" "js_alert"
    (func $js_alert (param i32)))

  ;; =====================================================================
  ;; Memory — Almacén lineal para strings y estado
  ;; =====================================================================

  (memory 1)
  (export "memory" (memory 0))

  ;; Dirección base para strings en memoria
  ;; 0x0000 - 0x0FFF: strings estáticos
  ;; 0x1000 - 0x1FFF: buffers temporales
  ;; 0x2000+: heap dinámico

  ;; =====================================================================
  ;; Globals — Estado del contador
  ;; =====================================================================

  (global $counter (mut i32) (i32.const 0))

  ;; =====================================================================
  ;; Data — Strings estáticos en memoria
  ;; =====================================================================

  ;; "counter-value" (ID del elemento donde se muestra el contador)
  (data (i32.const 0) "counter-value")

  ;; "counter-input" (ID del input para valor personalizado)
  (data (i32.const 16) "counter-input")

  ;; "¡Contador reiniciado!" (mensaje de reset)
  (data (i32.const 32) "Counter reset!")

  ;; =====================================================================
  ;; Funciones exportadas — API para JavaScript
  ;; =====================================================================

  ;; increment(): incrementa el contador en 1 y actualiza el DOM
  (func $increment (export "increment")
    (local $elem_ptr i32)
    (local $text_ptr i32)

    ;; Incrementar el contador
    global.get $counter
    i32.const 1
    i32.add
    global.set $counter

    ;; Obtener elemento por ID "counter-value"
    i32.const 0  ;; puntero al string "counter-value" en memoria
    call $js_get_element_by_id
    local.set $elem_ptr

    ;; Convertir el contador a string y actualizar el DOM
    global.get $counter
    call $int_to_string
    local.set $text_ptr

    local.get $elem_ptr
    local.get $text_ptr
    call $js_set_text
  )

  ;; decrement(): decrementa el contador en 1 y actualiza el DOM
  (func $decrement (export "decrement")
    (local $elem_ptr i32)
    (local $text_ptr i32)

    ;; Decrementar el contador
    global.get $counter
    i32.const 1
    i32.sub
    global.set $counter

    ;; Obtener elemento por ID "counter-value"
    i32.const 0  ;; puntero al string "counter-value"
    call $js_get_element_by_id
    local.set $elem_ptr

    ;; Convertir el contador a string y actualizar el DOM
    global.get $counter
    call $int_to_string
    local.set $text_ptr

    local.get $elem_ptr
    local.get $text_ptr
    call $js_set_text
  )

  ;; reset(): reinicia el contador a 0 y actualiza el DOM
  (func $reset (export "reset")
    (local $elem_ptr i32)
    (local $text_ptr i32)

    ;; Reiniciar el contador
    i32.const 0
    global.set $counter

    ;; Obtener elemento por ID "counter-value"
    i32.const 0  ;; puntero al string "counter-value"
    call $js_get_element_by_id
    local.set $elem_ptr

    ;; Actualizar el DOM con "0"
    i32.const 0
    call $int_to_string
    local.set $text_ptr

    local.get $elem_ptr
    local.get $text_ptr
    call $js_set_text
  )

  ;; get_counter(): retorna el valor actual del contador
  (func $get_counter (export "get_counter") (result i32)
    global.get $counter
  )

  ;; main(): inicialización — se llama al cargar el módulo
  (func $main (export "main")
    (local $elem_ptr i32)
    (local $text_ptr i32)

    ;; Establecer contador inicial a 0
    i32.const 0
    global.set $counter

    ;; Obtener elemento y mostrar "0"
    i32.const 0  ;; puntero al string "counter-value"
    call $js_get_element_by_id
    local.set $elem_ptr

    i32.const 0
    call $int_to_string
    local.set $text_ptr

    local.get $elem_ptr
    local.get $text_ptr
    call $js_set_text
  )

  ;; =====================================================================
  ;; Funciones internas
  ;; =====================================================================

  ;; int_to_string(n): convierte entero a string en memoria lineal
  ;; Retorna puntero al string en la dirección 4096
  ;; Buffer de escritura: 4096..4115 (20 bytes max para i32)
  (func $int_to_string (param $n i32) (result i32)
    (local $buf i32)
    (local $end i32)
    (local $is_neg i32)
    (local $digit i32)

    ;; Puntero al buffer de trabajo
    i32.const 4115
    local.set $end

    ;; Null terminator
    local.get $end
    i32.const 0
    i32.store8

    ;; Manejar negativos
    local.get $n
    i32.const 0
    i32.lt_s
    if
      i32.const 1
      local.set $is_neg
      i32.const 0
      local.get $n
      i32.sub
      local.set $n
    else
      i32.const 0
      local.set $is_neg
    end

    ;; Caso especial: n = 0
    local.get $n
    i32.eqz
    if
      local.get $end
      i32.const 1
      i32.sub
      local.set $end
      local.get $end
      i32.const 48
      i32.store8
    else
      ;; Extraer dígitos en orden inverso
      block $break
        loop $loop
          local.get $n
          i32.eqz
          br_if $break

          ;; digit = n % 10
          local.get $n
          i32.const 10
          i32.rem_s
          local.set $digit

          ;; n = n / 10
          local.get $n
          i32.const 10
          i32.div_s
          local.set $n

          ;; *--end = '0' + digit
          local.get $end
          i32.const 1
          i32.sub
          local.set $end

          local.get $end
          local.get $digit
          i32.const 48
          i32.add
          i32.store8

          br $loop
        end
      end
    end

    ;; Agregar signo negativo
    local.get $is_neg
    if
      local.get $end
      i32.const 1
      i32.sub
      local.set $end
      local.get $end
      i32.const 45
      i32.store8
    end

    local.get $end
  )
)
