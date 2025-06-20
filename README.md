# Lista de pasos para runear el Proyecto

#Nota antes de empezar

# VERIFICAR QUE NO TENGAN DJANGO INSTALADO DE FORMA GLOBAL PORQUE PUEDE GENERAR CONFLICTOS

ANTES DE ACTIVAR EL ENTORNO VIRTUAL HACER:
pip show django
pip show pillow

Si no muestran nada esta bien y ya pueden segir con el PASO 1

# SI LES APARECE UNA VERSION INSTALADA HACER:
pip uninstall django
 o
pip uninstall pillow
DEPENDIENDO DE CUAL DE LOS 2 TENGAN

# Paso 1 INSTALAR EL ENTORNO VIRTUAL
python -m venv env

# Paso 2 ACTIVAR EL ENTORNO VIRTUAL
env\Scripts\activate

# Paso 3 INSTALAR TODAS LAS DEPENDENCIAS
cd Proyecto_Veluweb_2.0

pip install -r requirements.txt

# Paso 4 ENTRAR A LA CARPETA DE LA RAIZ DEL PROYECTO Y APLICAR LAS MIGRACIONES
cd Proyecto_Veluweb

python manage.py migrate

# Paso 5 CARGAR LOS DATOS DE LA BASE DE DATOS (Nota:  Hay que ejecutar cada una de estas lineas POR SEPARADO y EN ESE MISMO ORDER de otra forma dara error)
python manage.py loaddata todo/fixtures/usuarios.json
python manage.py loaddata todo/fixtures/clientes.json
python manage.py loaddata todo/fixtures/productos.json
python manage.py loaddata todo/fixtures/facturas.json
python manage.py loaddata todo/fixtures/detallesfacturas.json

# Paso 6 RUNEAR EL SERVER
python manage.py runserver



# Nota para cada uno se creo un usuario basico que es "sunombreenminusculas@gmail.com" y la contraseña es "1234" + la primera inicial de su primer nombre 
Esto para que sea mas facil el proceso de logearse y demas


(probado por mi mismo :D)

