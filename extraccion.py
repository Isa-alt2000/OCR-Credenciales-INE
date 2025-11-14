import cv2
import easyocr
import datetime
import json
from pathlib import Path
from parseo import parsear_datos_ine, combinar_jsons


class INEExtractor:
    def __init__(self, nombre_base=None):
        if nombre_base is None:
            nombre_base = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.nombre_base = nombre_base
        self.output_dir = Path(__file__).resolve().parent / "resultados"
        self.output_dir.mkdir(exist_ok=True)

        self.reader = easyocr.Reader(['es', 'en'], gpu=False)

    def preprocesar_imagen(self, ruta_imagen, activo=False):
        if not activo:
            return ruta_imagen

        img = cv2.imread(ruta_imagen)
        if img is None:
            raise ValueError(f"No se pudo leer la imagen en la ruta: {ruta_imagen}")

        # Redimension
        height, width = img.shape[:2]
        if width < 1500:
            scale = 1500 / width
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # escala de grises
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Contraste con CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast = clahe.apply(gray)

        # reducir ruido
        denoised = cv2.fastNlMeansDenoising(contrast, h=10)

        # crea archivo temporal
        temp_path = self.output_dir / f"ine_temp_procesada_{self.nombre_base}.jpg"
        cv2.imwrite(str(temp_path), denoised)

        return temp_path

    def extraer_texto(self, ruta_imagen, debug=False):

        resultados = self.reader.readtext(str(ruta_imagen), detail=1)

        texto_completo = ""
        texto_con_info = []

        for (bbox, text, confidence) in resultados:
            if confidence > 0.3:  # Filtro de confianza, reducir o aumentar segun sea conveniente
                texto_completo += text + "\n"
                texto_con_info.append({
                    "texto": text,
                    "confianza": confidence,
                    "posicion": bbox
                })

            # debug
            if debug:
                print(f"Texto: {text} | Confianza: {confidence:.2f}")
                ruta_txt = self.output_dir / f"texto_ocr_{self.nombre_base}.txt"
                with open(ruta_txt, "w", encoding="utf-8") as f:
                    f.write(texto_completo)

        return texto_completo, texto_con_info

    # debug
    def visualizar_detecciones(self, ruta_imagen):
        img = cv2.imread(ruta_imagen)
        resultados = self.reader.readtext(img, detail=1)

        for (bbox, text, confidence) in resultados:
            if confidence > 0.3:
                # Obtener coordenadas de las cajas verdes
                top_left = tuple([int(val) for val in bbox[0]])
                bottom_right = tuple([int(val) for val in bbox[2]])

                # Dibujar rectangulos
                cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 2)

                # Agregar texto
                cv2.putText(img, f"{text[:20]}",
                            (top_left[0], top_left[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        cv2.imwrite(self.output_dir / f'img_boxes_{self.nombre_base}.jpg', img)
        print("Imagen con cajas verdes de detecciones guardada")

    def procesar_ine(self, ruta_img, nombre_base, debug=False, forzar=False):
        texto_normal, texto_info = self.extraer_texto(ruta_img, debug=debug)
        json_normal = parsear_datos_ine(texto_normal)

        campos_vacios = sum(1 for v in json_normal.values() if not v)
        print(f"Campos vacíos en OCR normal: {campos_vacios}")

        # Guardar resultado inicial
        with open(self.output_dir / f"JSON_normal_{nombre_base}.json", "w", encoding="utf-8") as w:
            json.dump(json_normal, w, ensure_ascii=False, indent=4)

        if campos_vacios >= 1 or forzar is True:
            print("Resultado incompleto, reintentando con imagen preprocesada")
            imagen_proc = self.preprocesar_imagen(ruta_img, activo=True)
            texto_proc, texto_info = self.extraer_texto(imagen_proc, debug=debug)
            json_proc = parsear_datos_ine(texto_proc)

            with open(self.output_dir / f"JSON_preproc_{nombre_base}.json", "w", encoding="utf-8") as w:
                json.dump(json_proc, w, ensure_ascii=False, indent=4)

            json_final = combinar_jsons(json_normal, json_proc)
            with open(self.output_dir / f"JSON_final_{nombre_base}.json", "w", encoding="utf-8") as w:
                json.dump(json_final, w, ensure_ascii=False, indent=4)
            return json_final, imagen_proc
        else:
            print("Escaneo normal sin pre fue suficiente.")
            return json_normal, ruta_img
