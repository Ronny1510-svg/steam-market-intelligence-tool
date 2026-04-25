"""
PROYECTO: Steam Specials Intelligent Scraper
AUTOR: [Ronny1510-svg]
DESCRIPCIÓN: Script de automatización de alto nivel diseñado para extraer ofertas 
             reales de Steam, superando bloqueos de contenido dinámico y 
             generando reportes profesionales en Excel.
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time

def scraping_steam_final_v3():
    # --- CONFIGURACIÓN DEL NAVEGADOR (MODO SIGILO) ---

    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Descomenta para ocultar la ventana
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # Inicialización automatizada del WebDriver de Chrome

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # Steam carga los precios mediante scripts y selenium renderiza ese contenido.
        url = "https://store.steampowered.com/search/?specials=1"
        driver.get(url)

        # GESTIÓN DE CARGA DINÁMICA: 
        # Espera hasta 20s que el DOM contenga los resultados para evitar posibles errores de sincronización
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search_result_row")))
        
        # Scroll estratégico: Algunos elementos solo se activan al simular el desplazamiento del usuario.
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(3)
        # Se captura el HTML final ya procesado por el motor de JavaScript de Chrome
        sopa = BeautifulSoup(driver.page_source, 'html.parser')
    finally:
        driver.quit()

    # --- EXTRACCIÓN Y LIMPIEZA DE DATOS (DATA WRANGLING) ---

    juegos = sopa.find_all('a', class_='search_result_row')
    lista_juegos = []

    print(f"Analizando {len(juegos)} juegos encontrados...")

    for juego in juegos:
        try:
            # Extracción de Título
            titulo_el = juego.find('span', class_='title')
            titulo = titulo_el.text.strip() if titulo_el else "Sin Título"
            
            # Localización del Porcentaje de Descuento
            # Nota: Se usan selectores basados en la estructura dinámica 'discount_pct'
            desc_div = juego.find('div', class_='discount_pct')
            porcentaje = 0
            if desc_div:
                # Se extrae el número del texto '-70%'
                nums = "".join(filter(str.isdigit, desc_div.get_text()))
                porcentaje = int(nums) if nums else 0

            # Extracción del Precio Final (Valor de Mercado)
            # El precio final se encuentra en la clase 'discount_final_price' tras la rebaja
            precio_el = juego.find('div', class_='discount_final_price')
            # Solo se indexan juegos que representen una oferta real (> 0%)
            if precio_el:
                precio_final = precio_el.get_text(strip=True)
            else:
                # Fallback: Si no hay descuento, se intenta capturar el precio base
                precio_normal = juego.find('div', class_='search_price')
                precio_final = precio_normal.get_text(strip=True) if precio_normal else "N/A"

            if titulo != "Sin Título":
                lista_juegos.append({
                    "Titulo": titulo,
                    "Descuento_Valor": porcentaje,
                    "Precio Final": precio_final
                })
        except:
            continue
    # --- PROCESAMIENTO Y EXPORTACIÓN (PANDAS & OPENPYXL) ---
    if lista_juegos:
        df = pd.DataFrame(lista_juegos)
        # Se ordena el TOP 50 basándose en la magnitud del descuento.
        df_ofertas = df[df["Descuento_Valor"] > 0].copy()
        df_final = df_ofertas.sort_values(by="Descuento_Valor", ascending=False).head(50)
        df_final["Descuento %"] = "-" + df_final["Descuento_Valor"].astype(str) + "%"
        
        resultado = df_final[["Titulo", "Descuento %", "Precio Final"]]
        
        nombre_archivo = "top_50_ofertas_steam.xlsx"

        # Generación de Excel con formato de celdas inteligente (Auto-fit columns)
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            resultado.to_excel(writer, index=False, sheet_name='Ofertas')
            ws = writer.sheets['Ofertas']
            
            for col in ws.columns:
                max_length = 0
                column_letter = col[0].column_letter
                
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = (max_length + 2)
                ws.column_dimensions[column_letter].width = adjusted_width
        
        print(f"LOGRADO Archivo '{nombre_archivo}' generado correctamente.")
    else:
        print("No se pudo extraer la información.")

if __name__ == "__main__":
    scraping_steam_final_v3()