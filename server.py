import os
from urllib.parse import urlparse

from flask import Flask, json, render_template, request
import psycopg2
from psycopg2.extras import RealDictCursor as Cursor
from sklearn import svm


app = Flask(__name__)
app.config.update(dict(
    DATABASE_URL=os.environ.get('DATABASE_URL')
))
print(app.config.get('DATABASE_URL'))
url = urlparse(app.config.get('DATABASE_URL'))
db_conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)


def flatten(arr):
    return sum(arr, [])


class NumberDrawingPredictor:
    """Service that predicts a digit (0-9) based on an 8x8 pixel art.

    The service utilizes machine learning to make informed decision.
    """
    def __init__(self):
        self.classifier = svm.SVC(gamma=0.001, C=100.0)
        self._train()

    def _train(self):
        """load training data and feed classification engine"""
        with db_conn.cursor(cursor_factory=Cursor) as cursor:
            cursor.execute("SELECT digit, pixels FROM numbers;")
            data = cursor.fetchall()
            labels, images = zip(
                *map(lambda r: (r['digit'], flatten(r['pixels'])), data)
            )
            self.classifier.fit(list(images), list(labels))

    @staticmethod
    def update(drawing_id, digit):
        with db_conn.cursor(cursor_factory=Cursor) as cursor:
            cursor.execute(
                "UPDATE numbers SET digit = %(digit)s WHERE id = %(id)s",
                {'digit': digit, 'id': drawing_id})
            db_conn.commit()

    def predict(self, pixels):
        # NOTE: pixels is a 2D (8 x 8) integer array
        with db_conn.cursor(cursor_factory=Cursor) as cursor:
            cursor.execute(
                "INSERT INTO numbers (pixels) VALUES (%(pixels)s) RETURNING id",
                dict(pixels=pixels)
            )
            res = cursor.fetchone()
            db_conn.commit()
            return int(self.classifier.predict([flatten(pixels)])[0]), res.get('id')


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/api/drawings', methods=['POST'])
def draw_digit():
    predictor = NumberDrawingPredictor()
    # TODOL replace drawn with image (mapped to 8 x 8) from request
    drawn = [[0, 0, 0, 20, 20, 0, 0, 0]] * 8
    guess, identifier = predictor.predict(drawn)
    return json.dumps({'guess': guess, 'id': identifier}), 201


@app.route('/api/drawings/<int:id>', methods=['PATCH'])
def update_result(id):
    correct_digit = int(request.get_json().get('digit'))
    NumberDrawingPredictor.update(id, correct_digit)
    return "", 204
