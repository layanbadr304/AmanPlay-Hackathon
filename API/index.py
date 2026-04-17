import os
from flask import Flask, render_template, request, redirect, url_for
from openai import OpenAI


app = Flask(__name__, 
            template_folder='../templates', 
            static_folder='../static')

app.config['UPLOAD_FOLDER'] = '/tmp'

# إعدادات العميل (OpenAI / Elm)
SHARED_API_KEY = "sk-jOfXp5r3BJHbH2erd8VFEg" 
BASE_URL = "https://elmodels.ngrok.app/v1"

client = OpenAI(api_key=SHARED_API_KEY, base_url=BASE_URL)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detection')
def detection():
    return render_template('analysis.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    user_text = ""
    text_input = request.form.get('text_input')

    # أولاً: التحقق من وجود ملف صوتي
    if 'audio_file' in request.files and request.files['audio_file'].filename != '':
        file = request.files['audio_file']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        try:
            with open(file_path, "rb") as audio:
                transcript = client.audio.transcriptions.create(
                    model="elm-asr",
                    file=audio
                )
            user_text = transcript.text
        except Exception as e:
            return f"خطأ في تحويل الصوت: {e}"
        finally:
            if os.path.exists(file_path): 
                os.remove(file_path)
    else:
        # ثانياً: إذا لم يوجد صوت، نأخذ النص من الحقل النصي
        user_text = text_input

    # ثالثاً: تحليل النص باستخدام نموذج Nuha
    if user_text:
        try:
            response = client.chat.completions.create(
                model="nuha-2.0",
                messages=[
                    {"role": "system", "content": "أنت خبير كشف تنمر. حلل النص ورد بكلمة واحدة: YES للتنمر، NO للسليم."},
                    {"role": "user", "content": user_text}
                ],
                temperature=0
            )
            prediction = response.choices[0].message.content.strip().upper()

            if "YES" in prediction:
                return render_template('alerts.html', detected_text=user_text)
            else:
                return render_template('recognition.html', result=user_text)

        except Exception as e:
            return f"خطأ في تحليل النص: {e}"

    return redirect(url_for('detection'))

# ـ Vercel
if __name__ == '__main__':
    app.run(debug=True)
