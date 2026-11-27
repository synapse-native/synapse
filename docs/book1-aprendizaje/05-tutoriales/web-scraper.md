# Tutorial: Web Scraper en Syquex

Este tutorial guía la creación de un web scraper en Syquex. Aprenderás a hacer peticiones HTTP, parsear HTML, extraer datos y almacenarlos de forma estructurada.

Al finalizar, tendrás un scraper funcional que puedes adaptar a diferentes sitios web.

<!-- cumple Manual 3 §12, §9 -->

## 1. Visión General

Construiremos un web scraper para extraer información de un sitio web:

- **Peticiones HTTP** asíncronas
- **Parsing HTML** con selectores CSS
- **Persistencia en JSON** o CSV
- **Rate limiting** para no sobrecargar el servidor
- **Manejo de errores** robusto

## 2. Estructura del Proyecto

```text
web_scraper/
├── main.syq
├── lib/
│   ├── scraper.syq
│   ├── parser.syq
│   ├── storage.syq
│   └── rate_limiter.syq
└── output/
```

## 3. Dependencias

Necesitaremos:
- `lib.web` (cliente HTTP) - Manual 3 §12
- `lib.html` (parser HTML) - Manual 3 §9 (FFI)
- `lib.fs` (filesystem) - Manual 3 §12
- `lib.regex` (regex) - Manual 3 §12

## 4. Rate Limiter

### `lib/rate_limiter.syq`

```syquex
#lang: es

importar lib.tiempo

estructura RateLimiter:
    solicitudes_por_segundo: entero
    ultima_solicitud: entero = 0
    
    crear(solicitudes_por_segundo: entero):
        self.solicitudes_por_segundo = solicitudes_por_segundo
    
    async metodo esperar():
        let ahora = tiempo_actual().timestamp()
        let tiempo_minimo = 1000 / self.solicitudes_por_segundo
        let tiempo_transcurrido = ahora - self.ultima_solicitud
        
        si tiempo_transcurrido < tiempo_minimo:
            let espera = tiempo_minimo - tiempo_transcurrido
            tiempo.dormir(espera.entero())
        
        self.ultima_solicitud = tiempo_actual().timestamp()
```

## 5. Parser HTML

### `lib/parser.syq`

```syquex
#lang: es

importar lib.html
importar lib.regex

estructura Elemento:
    tag: texto
    atributos: Mapa<texto, texto>
    texto: texto = ""
    hijos: Lista<Elemento>
    
    metodo seleccionar(selector: texto) -> Lista<Elemento>:
        // Implementación simplificada con selectores CSS básicos
        retornar html.seleccionar(self, selector)
    
    metodo obtener_atributo(nombre: texto) -> texto?:
        si self.atributos.contiene(nombre):
            return self.atributos[nombre]
        return nulo

funcion parsear_html(html_string: texto) -> Resultado<Elemento, texto>:
    intentar:
        retornar ok(html.parsear(html_string))
    atrapar e:
        retornar err("Error al parsear HTML: " + e)
```

## 6. Scraper Principal

### `lib/scraper.syq`

```syquex
#lang: es

importar lib.web
importar lib.html
importar lib.parser
importar lib.storage
importar lib.rate_limiter
importar lib.io

estructura ConfiguracionScraper:
    url_base: texto
    selectores: Mapa<texto, texto>
    paginacion: texto = ""
    rate_limit: entero = 5   // 5 req/segundo
    user_agent: texto = "ScraperBot/1.0"

estructura Scraper:
    config: ConfiguracionScraper
    rate_limiter: RateLimiter
    datos: Lista<Mapa<texto, texto>>
    
    crear(config: ConfiguracionScraper):
        self.config = config
        self.rate_limiter = RateLimiter(config.rate_limit)
        self.datos = Lista<Mapa<texto, texto>>()
    
    async metodo hacer_peticion(url: texto) -> Resultado<texto, texto>:
        intentar:
            await self.rate_limiter.esperar()
            let resp = await web.get(url, headers: {
                "User-Agent": self.config.user_agent
            })
            si resp.status != 200:
                retornar err("HTTP " + resp.status.texto() + " en " + url)
            retornar ok(resp.cuerpo)
        atrapar e:
            retornar err("Error en petición: " + e)
    
    async metodo extraer_pagina(url: texto) -> Resultado<Lista<Mapa<texto, texto>>, texto>:
        let html = await self.hacer_peticion(url)?
        let doc = parsear_html(html)?
        let items = doc.seleccionar(self.config.selectores["item"])
        
        let resultados = Lista<Mapa<texto, texto>>()
        para item en items:
            let datos_item = Mapa<texto, texto>()
            para campo, selector en self.config.selectores:
                si campo != "item" y campo != "paginacion":
                    let elementos = item.seleccionar(selector)
                    si elementos.len() > 0:
                        datos_item[campo] = elementos[0].texto.trim()
            resultados.agregar(datos_item)
        
        retornar ok(resultados)
    
    async metodo ejecutar() -> Resultado<entero, texto>:
        let url_actual = self.config.url_base
        let pagina = 1
        
        mientras url_actual != "":
            io.escribir_linea("Scrapeando página " + pagina.texto() + ": " + url_actual)
            
            let items = await self.extraer_pagina(url_actual)?
            para item en items:
                self.datos.agregar(item)
            
            io.escribir_linea("  → " + items.len().texto() + " items extraídos (total: " + self.datos.len().texto() + ")")
            
            // Paginación
            si self.config.paginacion != "":
                let html = await self.hacer_peticion(url_actual)?
                let doc = parsear_html(html)?
                let siguiente = doc.seleccionar(self.config.paginacion)
                si siguiente.len() > 0:
                    let href = siguiente[0].obtener_atributo("href")
                    si href != nulo:
                        url_actual = href
                        pagina = pagina + 1
                    sino:
                        romper
                sino:
                    romper
            sino:
                romper
        
        retornar ok(self.datos.len())
    
    metodo obtener_datos() -> Lista<Mapa<texto, texto>>:
        retornar self.datos
```

## 7. Persistencia

### `lib/storage.syq`

```syquex
#lang: es

importar lib.fs
importar lib.io

funcion guardar_json(datos: Lista<Mapa<texto, texto>>, ruta: texto) -> Resultado<booleano, texto>:
    intentar:
        let contenido = {
            "fecha": tiempo_actual().iso(),
            "total": datos.len(),
            "items": datos
        }.a_json(pretty: verdadero)
        fs.escribir(ruta, contenido)
        retornar ok(verdadero)
    atrapar e:
        retornar err("Error al guardar JSON: " + e)

funcion guardar_csv(datos: Lista<Mapa<texto, texto>>, ruta: texto) -> Resultado<booleano, texto>:
    si datos.vacio():
        retornar err("No hay datos para guardar")
    
    intentar:
        let columnas = Lista<texto>()
        para clave en datos[0].keys():
            columnas.agregar(clave)
        
        let lineas = Lista<texto>()
        lineas.agregar(columnas.unir(","))  // Header
        
        para item en datos:
            let valores = Lista<texto>()
            para col en columnas:
                valores.agregar("\"" + (item[col] o "") + "\"")
            lineas.agregar(valores.unir(","))
        
        fs.escribir_lines(ruta, lineas)
        retornar ok(verdadero)
    atrapar e:
        retornar err("Error al guardar CSV: " + e)
```

## 8. Programa Principal

### `main.syq`

```syquex
#lang: es

importar lib.scraper
importar lib.storage
importar lib.io

funcion principal() -> Resultado<nulo, texto>:
    // Configuración del scraper para un sitio de ejemplo
    let config = ConfiguracionScraper(
        url_base: "https://quotes.toscrape.com/",
        selectores: {
            "item": ".quote",
            "texto": ".text",
            "autor": ".author",
            "tags": ".tags .tag"
        },
        paginacion: ".next a",
        rate_limit: 2
    )
    
    let scraper = Scraper(config)
    let total = await scraper.ejecutar()?
    
    io.escribir_linea("\n✓ Scraping completado: " + total.texto() + " items")
    
    let datos = scraper.obtener_datos()
    
    // Guardar en JSON
    storage.guardar_json(datos, "output/datos.json")?
    io.escribir_linea("✓ Guardado en output/datos.json")
    
    // Guardar en CSV
    storage.guardar_csv(datos, "output/datos.csv")?
    io.escribir_linea("✓ Guardado en output/datos.csv")
    
    // Mostrar resumen
    io.escribir_linea("\nPrimeros 3 items:")
    para i = 0 mientras i < 3 y i < datos.len():
        let item = datos[i]
        io.escribir_linea("- [" + item["autor"] + "] " + item["texto"].substring(0, 80) + "...")
    
    retornar ok()
```

## 9. Compilar y Ejecutar

```bash
# Compilar
python main.py main.syq -o scraper.exe

# Ejecutar
./scraper.exe
```

### Salida Esperada

```
Scrapeando página 1: https://quotes.toscrape.com/
  → 10 items extraídos (total: 10)
Scrapeando página 2: https://quotes.toscrape.com/page/2/
  → 10 items extraídos (total: 20)
...

✓ Scraping completado: 100 items
✓ Guardado en output/datos.json
✓ Guardado en output/datos.csv

Primeros 3 items:
- [Albert Einstein] "The world as we have created it is a process of our thinking. It c...
- [J.K. Rowling] "It is our choices, Harry, that show what we truly are, far more th...
- [Albert Einstein] "Life is like riding a bicycle. To keep your balance you must kee...
```

## 10. Mejoras Posibles

1. **Scraping concurrente** con múltiples workers:

   ```syquex
   async funcion scrape_concurrente(urls: Lista<texto>) -> Lista<Mapa<texto, texto>>:
       let promesas = urls.mapear(async lambda url: scraper.extraer_pagina(url))
       let resultados = await Promise.all(promesas)
       return resultados.filtrar(lambda r: r.es_ok()).mapear(lambda r: r.desenvolver())
   ```

2. **User-Agent rotativo** para evitar bloqueos
3. **Proxies** configurables
4. **Reintentos con backoff** exponencial
5. **CLI con argumentos** para URL y selectores
6. **Soporte para JavaScript** con Playwright (FFI)

## 11. Consideraciones Éticas

- **Respeta `robots.txt`** del sitio
- **Rate limiting** apropiado
- **User-Agent identificable**
- **Términos de servicio** del sitio
- **Solo datos públicos**

## 12. Conceptos Aprendidos

- **Peticiones HTTP asíncronas**
- **Parsing HTML** con selectores
- **Rate limiting** para no sobrecargar
- **Manejo de errores** robusto
- **Persistencia** en JSON y CSV
- **Concurrencia** para múltiples URLs

## Referencias

- **Manual 3 §8**: Concurrencia y async/await
- **Manual 3 §9**: FFI a librerías HTML (libxml, BeautifulSoup-like)
- **Manual 3 §12**: Biblioteca estándar (`lib.web`, `lib.fs`, `lib.html`)
- **Manual 5 §6**: Patrones de scraping y workers

// cumple Manual 3 §12
