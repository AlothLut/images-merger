from flask import Flask, render_template
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import RadioField
from werkzeug.utils import secure_filename
import os
import shutil
import cv2
from PIL import Image
import matplotlib.pyplot as plt

app = Flask(__name__)
SECRET_KEY = 'secret'
app.config['SECRET_KEY'] = SECRET_KEY
app.config['RECAPTCHA_USE_SSL'] = False
# ключи recaptcha или по-умолчанию для localhost
app.config['RECAPTCHA_PUBLIC_KEY'] = os.getenv('RECAPTCHA_PUBLIC_KEY', "6Le2wSspAAAAAAyiDVrT6alooDLsGju7fedE2A5d")
app.config['RECAPTCHA_PRIVATE_KEY'] = os.getenv('RECAPTCHA_PRIVATE_KEY', "6Le2wSspAAAAAKa4MyvEjqu7AjDgAbPDa-mmE0op")
app.config['RECAPTCHA_OPTIONS'] = {'theme': 'white'}


class MergingPicForm(FlaskForm):
    pic_1 = FileField(label='Load first image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')]
                      )
    pic_2 = FileField(label='Load second image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')]
                      )
    merge_type = RadioField(label='Merge type', validators=[DataRequired()],
                            choices=[('horizontal', 'horizontal'), ('vertical', 'vertical')]
                            )
    recaptcha = RecaptchaField()
    submit = SubmitField(label='Submit')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = MergingPicForm()
    result_image_path = None
    graph_pic1 = None
    graph_pic2 = None
    graph_result = None
    if form.validate_on_submit():
        # создаем директорию для хранения загруженных изображений
        images_path = './static'
        if not os.path.exists(images_path) and not os.path.exists(os.path.join(images_path, 'graphs/')):
            os.makedirs(images_path)
            os.makedirs(os.path.join(images_path, 'graphs/'))
        else:
            # удаляем чтобы сохранить место в storage
            shutil.rmtree(images_path)
            os.makedirs(images_path)
            os.makedirs(os.path.join(images_path, 'graphs/'))

        # сохраняем изображения
        pic_1_data = form.pic_1.data
        pic_1_name = secure_filename(pic_1_data.filename)
        pic_1_path = os.path.join(images_path, pic_1_name)
        pic_1_data.save(pic_1_path)
        graph_pic1 = get_color_graph(pic_1_path, pic_1_name)

        pic_2_data = form.pic_2.data
        pic_2_name = secure_filename(pic_2_data.filename)
        pic_2_path = os.path.join(images_path, pic_2_name)
        pic_2_data.save(pic_2_path)
        graph_pic2 = get_color_graph(pic_2_path, pic_2_name)

        # из формы выбирается тип склеивания
        merge_type = form.merge_type.data
        if merge_type == "horizontal":
            result = get_merge_h(Image.open(pic_1_path), Image.open(pic_2_path))
        if merge_type == "vertical":
            result = get_merge_v(Image.open(pic_1_path), Image.open(pic_2_path))
        if result:
            result.save(os.path.join(images_path, "result.png"))
            result_image_path = os.path.join("./static", "result.png")
            graph_result = get_color_graph(result_image_path, "result.png")

    return render_template(
        'form.html',
        form=form,
        result_image_path=result_image_path,
        graph_pic1=graph_pic1,
        graph_pic2=graph_pic2,
        graph_result=graph_result
    )


def get_merge_h(pic_1, pic_2):
    dst = Image.new('RGB', (pic_1.width + pic_2.width, pic_1.height))
    dst.paste(pic_1, (0, 0))
    # paste кортеж из двух элементов определяет где левый верхний угол
    # смещаем угол на ширину первой картинки для вставки второго изображения
    dst.paste(pic_2, (pic_1.width, 0))
    return dst


def get_merge_v(pic_1, pic_2):
    dst = Image.new('RGB', (pic_1.width, pic_1.height + pic_2.height))
    dst.paste(pic_1, (0, 0))
    # paste кортеж из двух элементов определяет где левый верхний угол
    # смещаем угол на высоту первой картинки для вставки второго изображения
    dst.paste(pic_2, (0, pic_1.height))
    return dst


def get_color_graph(img_path, name):
    image = cv2.imread(img_path)

    # конфертируем из  BGR в RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # разделяем изображение на компоненты RGB.
    r, g, b = cv2.split(image_rgb)

    # рассчитываем гистограммы для отдельных цветовых каналов
    r_hist = cv2.calcHist([r], [0], None, [256], [0, 256])
    g_hist = cv2.calcHist([g], [0], None, [256], [0, 256])
    b_hist = cv2.calcHist([b], [0], None, [256], [0, 256])

    # строим график
    plt.plot(r_hist, color='red', label='Red')
    plt.plot(g_hist, color='green', label='Green')
    plt.plot(b_hist, color='blue', label='Blue')
    plt.xlim([0, 256])
    plt.xlabel('Color Intensity')
    plt.ylabel('Pixel Count')
    plt.title("Graph for:" + name)
    plt.legend()
    result_path = os.path.join('./static', 'graphs', name)
    plt.savefig(result_path)
    plt.close()
    return result_path


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
