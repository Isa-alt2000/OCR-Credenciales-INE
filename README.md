### Contenido
Se cuenta con un módulo de 3 archivos;  
- main.py  
- extracción.py  
- parseo.py  

Con su respectivo archivo de requerimentos. 

### Flujo
EL programa buscará las areas con texto y procederá a leerlas con easyORC, despúes las almacenará en un archivo.txt temporal y posteriormente filtrará y limpiará el texto buscando matches. FInalmente almcenará de forma ordenada en un JSON. Sin embargo, si hay al menos 1 campo vacío, se hará un preprocesamiento de imágen con OpenCV que se encarga de redimensionar, transformar a escala de grises, aplicar contraste CLAHE y reducción de ruido. Este preprocesamiento se almacena en una imagen temporal que posteriormente pasará por la extracción y filtrado de datos nuevamente generando un nuevo JSON. 
Finalmente compara ambos JSON, apuntando a 
- Rellenar valores vacíos
- Sustituír palabras que pudieron ser añadidas por error como valores de campos (como nombre: FECHA)

### Detalles técnicos
Contenidos de `extraccion.py`:  


- Clase `INNEExtractor` cuenta con 4 métodos importantes:

  - `preprocesar_imagen` - Haciendo uso de libreria cv2 (OpenCV), se encarga de redimensionar, transformar a escala de grises, aplicar contraste CLAHE y reducción de ruido.  

  - `extraer_texto` - Devuelve 2 argumentos; texto crudo como primer argumento en un string, y texto con información que podría resultar útil para debug en una lista.   

  - `visualizar_detecciones` -  Almacena la visualización de OpenCV sobre la imágen con cajas verdes    
 
  - `procesar_ine`  -  MÉTODO PRINCIPAL QUE SE ENCARGA DE CORRER LOS DEMÁS. Intenta extraer la información del INE primero sin preprocesar y luego con preprocesamiento si el resultado del JSON es incompleto o si la variable para forzar está definida en True. 


Contenidos de `parseo.py`:

- `fuzzy_similar` - Fuzzy simple para buscar coincidencias de palabras/conceptos clave, se encarga de meter en tuplas letra por letra del texto recibido y del texto esperado para posteriormente compararlos y sumarlos. 1 es coincidencia completa. 

- `parsear_datos_ine` - Se encarga de pasar la información extraída por `extraer_texto` al JSON haciendo uso de matches, coincidencias y busquedas. 

- `combinar_jsons` Recibe el primer JSON generado de la imagen sin preprocesado y el segundo con preprocesado. Devuelve un tercer JSON combinando los mejores valores de ambos OCR.  

   - Si json1 tiene un campo vacío y json2 no, usa json2.
   - Si json1 tiene valores incorrectos ('NOMBRE', 'FECHA', etc.), usa json2.
   - Usará el valor de mayor longitud si resultan ser diferentes.


#### Contenido de muestra esperado en el JSON:
**(Estos campos son extrídos del INE de muestra oficial)**

```json
{
    "apellido_paterno": "LEYVA",
    "apellido_materno": "CASTAÑARES",
    "nombre": "MABEL IVONNE",
    "fecha_nacimiento": "17/09/1979",
    "sexo": "M",
    "domicilio": "Devrie AND SAN MARCOS MZ 1 LT 8 | 2",
    "curp": "LECM79O9I7MDFYSBO4"
}
```

### Salidas esperadas
3 archivos:
- JSON de datos extraidos  
- Imagen escaneada con opencv con texto detectado (debug)  
- .txt con datos crudos (debug)  


### Debug
- Se puede definir la variable DEBUG en main.py como True o False para NO almacenar la imagen con las cajas verdes, ni el .txt de datos crudos, únicamente el JSON final.

- Se puede forzar el uso de imágen normal y preprocesada para resultados más refinados.