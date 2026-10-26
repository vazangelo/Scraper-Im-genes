import os
from playwright.sync_api import sync_playwright

URL_SITIO = "https://fichasalertanacional.segob.gob.mx/" #Ejemplo
CARPETA_SALIDA = "fichas"
os.makedirs(CARPETA_SALIDA, exist_ok=True)

imagenes_descargadas = set()

# Pre carga
for archivo in os.listdir(CARPETA_SALIDA):
    if archivo.endswith(".png"):
        imagenes_descargadas.add(archivo)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    print(f"Navegando a {URL_SITIO}...")
    page.goto(URL_SITIO)
    page.wait_for_timeout(5000)

    # Monitoreo continuo, para sitios con carrucel de imagenes
    for ciclo in range(12):
        print(f"\n--- Ciclo {ciclo + 1}/20 ---")

        # Extraer todos los src presentes en el DOM actual
        todos_los_src = page.evaluate("""
            Array.from(document.querySelectorAll('img'))
                 .map(img => img.src || img.getAttribute('src'))
                 .filter(Boolean)
        """)

        # Filtro con la ruta exacta que apareció en tus logs
        alertas = [
            s for s in todos_los_src if "/api/alertas/" in s and s.endswith(".png")
        ]
        print(f"Imágenes de alerta visibles en este turno: {len(alertas)}")

        for url_img in alertas:
            nombre_archivo = url_img.split("/")[-1].split("?")[0]

            if nombre_archivo not in imagenes_descargadas:
                ruta_local = os.path.join(CARPETA_SALIDA, nombre_archivo)
                try:
                    # page.request hereda la sesión activa y bypass de bloqueos
                    respuesta = page.request.get(url_img)
                    if respuesta.status == 200:
                        with open(ruta_local, "wb") as f:
                            f.write(respuesta.body())
                        imagenes_descargadas.add(nombre_archivo)
                        print(f"  [+] GUARDADA: {nombre_archivo}")
                    else:
                        print(
                            f"  [!] HTTP {respuesta.status} en: {nombre_archivo}"
                        )
                except Exception as e:
                    print(f"  [!] Error al descargar {nombre_archivo}: {e}")

        # Hacemos scroll suave para disparar componentes o carruseles lazy
        page.mouse.wheel(0, 500)
        page.wait_for_timeout(5000)

    browser.close()

print(f"\nTerminado. Total fichas/alertas guardadas: {len(imagenes_descargadas)}")