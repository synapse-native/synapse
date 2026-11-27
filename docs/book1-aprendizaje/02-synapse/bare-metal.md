# Programación Bare-Metal en Synapse

La programación bare-metal permite ejecutar código directamente sobre
hardware sin sistema operativo. Synapse soporta este paradigma mediante
bloques `inseguro` y acceso directo a memoria.

## ¿Qué es Bare-Metal?

Bare-metal significa ejecutar tu código directamente sobre el procesador,
sin capa de abstracción de un SO. Es común en:

- Microcontroladores (ARM Cortex-M, RISC-V)
- Sistemas embebidos
- Drivers de hardware
- Sistemas de tiempo real

```synapse
// Punto de entrada bare-metal
#[no_mangle]
fn _start() {
    // Configurar stack pointer
    // Inicializar hardware
    // Ejecutar código principal
    loop {
        // Mantener vivo
    }
}
```

## Acceso a Memoria con `inseguro`

La palabra clave `inseguro` permite operaciones que el compilador no puede
verificar seguridad:

```synapse
fn leer_registro(direccion: entero) -> u32 {
    inseguro {
        let ptr = direccion.como_puntero::<u32>()
        ptr.leer()
    }
}

fn escribir_registro(direccion: entero, valor: u32) {
    inseguro {
        let ptr = direccion.como_puntero::<u32>()
        ptr.escribir(valor)
    }
}
```

## Registros de Hardware

Los registros de hardware se mapean en direcciones de memoria específicas:

```synapse
// Direcciones de ejemplo para STM32
const GPIOA_BASE: u32 = 0x40020000
const GPIOA_MODER: u32 = GPIOA_BASE + 0x00
const GPIOA_ODR: u32 = GPIOA_BASE + 0x14
const RCC_AHB1ENR: u32 = 0x40023830

fn configurar_gpio() {
    // Habilitar reloj para GPIOA
    let actual = leer_registro(RCC_AHB1ENR)
    escribir_registro(RCC_AHB1ENR, actual | 0x01)

    // Configurar pin 5 como salida
    let moder = leer_registro(GPIOA_MODER)
    // Limpiar bits 10:11 y poner 01 (salida)
    let nuevo = (moder & !0xC00) | 0x400
    escribir_registro(GPIOA_MODER, nuevo)
}

fn escribir_pin(numero: entero, estado: bool) {
    let odr = leer_registro(GPIOA_ODR)
    if estado {
        escribir_registro(GPIOA_ODR, odr | (1 << numero))
    } else {
        escribir_registro(GPIOA_ODR, odr & !(1 << numero))
    }
}
```

## Ejemplo: LED Parpadeante

```synapse
// Driver completo para LED en STM32
const RCC_AHB1ENR: u32 = 0x40023830
const GPIOA_BASE: u32 = 0x40020000
const GPIOA_MODER: u32 = GPIOA_BASE + 0x00
const GPIOA_ODR: u32 = GPIOA_BASE + 0x14

fn inicializar_hardware() {
    // Habilitar reloj GPIOA
    let rcc = leer_registro(RCC_AHB1ENR)
    escribir_registro(RCC_AHB1ENR, rcc | 0x01)

    // Pin 5 como salida (MODER5 = 01)
    let moder = leer_registro(GPIOA_MODER)
    moder = (moder & !(0x3 << 10)) | (0x1 << 10)
    escribir_registro(GPIOA_MODER, moder)
}

fn led_on() {
    let odr = leer_registro(GPIOA_ODR)
    escribir_registro(GPIOA_ODR, odr | (1 << 5))
}

fn led_off() {
    let odr = leer_registro(GPIOA_ODR)
    escribir_registro(GPIOA_ODR, odr & !(1 << 5))
}

fn delay(ciclos: u32) {
    var i = 0
    while i < ciclos {
        inseguro { __asm__("nop") }
        i += 1
    }
}

fn _start() {
    inicializar_hardware()

    loop {
        led_on()
        delay(1_000_000)
        led_off()
        delay(1_000_000)
    }
}
```

## Vectores de Interrupción

```synapse
// Tabla de vectores de interrupción
#[no_mangle]
static VECTOR_TABLA: [fn(); 48] = [
    stack_top,      // 0: Initial SP
    reset_handler,  // 1: Reset
    nmi_handler,    // 2: NMI
    hard_fault,     // 3: Hard Fault
    // ... más handlers
]

fn reset_handler() {
    // Copiar .data de flash a RAM
    // Limpiar .bss
    // Llamar main
    main()
}

fn hard_fault() {
    // Error fatal: parpadeo rápido LED
    loop {
        led_on()
        delay(100_000)
        led_off()
        delay(100_000)
    }
}

#[no_mangle]
fn systick_handler() {
    // Timer tick cada 1ms
    // Actualizar contadores
    // Llamar scheduler si hay preempt
}
```

## Configuración de Reloj

```synapse
fn configurar_reloj() {
    // STM32F4: PLL para 168 MHz desde HSE (8MHz)
    const RCC_CR: u32 = 0x40023800
    const RCC_PLLCFGR: u32 = 0x40023804
    const RCC_CFGR: u32 = 0x40023808

    // Habilitar HSE
    let cr = leer_registro(RCC_CR)
    escribir_registro(RCC_CR, cr | (1 << 16))

    // Esperar HSE listo
    while (leer_registro(RCC_CR) & (1 << 17)) == 0 {}

    // Configurar PLL
    let pllcfg = (8 << 0)     // PLLM = 8
               | (336 << 6)   // PLLN = 336
               | (0 << 16)    // PLLP = 2
               | (1 << 22)    // PLLSRC = HSE
               | (7 << 24)    // PLLQ = 7
    escribir_registro(RCC_PLLCFGR, pllcfg)

    // Habilitar PLL
    let cr = leer_registro(RCC_CR)
    escribir_registro(RCC_CR, cr | (1 << 24))

    // Esperar PLL listo
    while (leer_registro(RCC_CR) & (1 << 25)) == 0 {}

    // Configurar flash y prescalers
    // ...
}
```

## Consideraciones de Seguridad

1. **Siempre use `inseguro`** para acceso a memoria crudo
2. **Valide direcciones** antes de acceder a registros
3. **No desreferencie punteros inválidos** - causan fault
4. **Use volatile** para lecturas/escrituras de hardware
5. **Documente cada dirección** de registro que use
