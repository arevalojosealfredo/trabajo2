# Llamando primero al modulo de Flask
from flask import Flask, render_template, request, redirect, url_for, flash


# Llamando al modulo de Flask para MySQL
from flask_mysqldb import MySQL
from textblob import TextBlob
import speech_recognition as sr



# Reconocer la entrada de voz del micrófono:
r = sr.Recognizer()
# --------------------------------------------



# Clase que tenemos que ejecutar para poder tener una conexión
app = Flask(__name__)
# --------------------------------------------------------------



# Para ejecutar el modulo para la base de datos dentro de la aplicación
mysql = MySQL(app)



# Aclaraciones para recordar sobre el lenguaje:
# Para poder empezar a ejecutar nuestro servidor utilizamos nuestra variable "app"
# Por parametros le doy el numero de puerto (por ejemplo)

# Un Flask, la sentencia debug = True nos permite que cada vez que hacemos un cambio
# dentro del servidor, esto reinicia automaticamete

# Para comprobar que archivo que se esta ejecutando es el archivo principal se valida que sea "name"
# que fue el nombrado arriba

# ----------------------------------------------------------------------------------------------------



# MySQL Conection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flaskdatos'
# --------------------------------------



# settings
app.secret_key = 'myscretkey'
# ---------------------------------

# cada vez que un usuario entre a nuestra ruta principal debemos responder
# por eso se define el Index. Se define la función para manejar esa visita

@app.route('/', methods=['POST', 'GET'])
def Index():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM articulos')
    data = cur.fetchall()
    return render_template('index.html', articulos=data)


@app.route('/producto/<id>')
def getProducto(id):
    
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM articulos WHERE id = %s', (id))
    data = cur.fetchall()

    op_cur = mysql.connection.cursor()
    op_cur.execute('SELECT * FROM comentarios WHERE idproducto = %s', (id))
    comentarios_data = op_cur.fetchall()

    polaridad = mysql.connection.cursor()
    polaridad.execute(
        'SELECT COUNT(polaridad) FROM comentarios WHERE polaridad > 0 AND idproducto = %s', (id))
    polaridad_data = polaridad.fetchall()

    negativa = mysql.connection.cursor()
    negativa.execute(
        'SELECT COUNT(polaridad) FROM comentarios WHERE polaridad < 0 AND idproducto = %s', (id))
    negativa_data = negativa.fetchall()

    total = mysql.connection.cursor()
    total.execute(
        'SELECT COUNT(*) FROM comentarios WHERE idproducto = %s', (id))
    total_data = total.fetchall()

    negativas = negativa_data[0][0]
    positivas = polaridad_data[0][0]
    total_calificaciones = total_data[0][0]

    if(total_calificaciones != 0):
        ponderacionPositiva = (positivas)*(100) / (total_calificaciones)
        ponderacionNegativa = (negativas)*(100) / (total_calificaciones)
    else:
        ponderacionPositiva = 0.0
        ponderacionNegativa = 0.0

    return render_template('producto.html', producto=data[0], comentarios=comentarios_data, positividad=ponderacionPositiva, negatividad=ponderacionNegativa)


@app.route('/calificar/<id>', methods=['GET'])
def Calificar(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM articulos WHERE id = %s', (id))
    data = cur.fetchall()

    if request.method == 'GET':
        with sr.Microphone() as source:
            print("Comentanos lo que opinas sobre el articulo...")
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio, language="es-ES")
                textoanalizado = TextBlob(text)
                textotraducido = textoanalizado.translate(to="en")
                print("Tu opinión: {}".format(text))

                cur.execute('INSERT INTO comentarios (texto, subjetividad, polaridad, idproducto) VALUES (%s, %s, %s, %s)',
                            (text, textotraducido.subjectivity, textotraducido.polarity, id))
                mysql.connection.commit()
                flash("El articulo ha sido calificado satisfactoriamente", category="exito")

                return redirect(url_for('getProducto', id=id))
            except:
                print("Se ha detectado un problema")
                flash("No se pudo capturar el comentario", category="error")
                return redirect(url_for('getProducto', id=id))

if __name__ == '__main__':
    app.run(port = 3000, debug = True)
