from flask import Flask, render_template, request
# Use a pipeline as a high-level helper
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

pipe = pipeline("text-classification", model="blanchefort/rubert-base-cased-sentiment")
tokenizer = AutoTokenizer.from_pretrained("ai-forever/rugpt3medium_based_on_gpt2")
model = AutoModelForCausalLM.from_pretrained("ai-forever/rugpt3medium_based_on_gpt2")

app = Flask(__name__)

@app.route(rule='/', methods=['GET', 'POST'])
def index():
    recommendation = ""
    user_text = ""

    if request.method == 'POST':
        user_text = request.form['message']

        result = pipe(user_text)[0]
        label = result['label']

        if label == 'POSITIVE':
            mood= 'У тебя всё прекрасно'
        elif label == 'NEGATIVE':
           mood = 'У тебя всё плохо!'
        else:
            mood = 'Ты нейтрал'
        def generate_recommendation(mood):
            prompt = (f"Посоветуй один популярный фильм для человека ,у которого {mood} настроение."
                        f"Назови фильм и кратко объясни почему.")
            inputs = tokenizer(prompt,return_tensors = "pt")
            outputs = model.generate(
                **inputs,
                max_length=70,
                do_sample=True,
                top_p=0.9,
                temperature=0.9
            )
            text = tokenizer.decode(outputs[0], skip_speacial_tokens=True)
            return text[len(prompt):].strip()
        
        ai_text = generate_recommendation(mood)
        recommendation = f"Настроение: {mood} <br>Рекоминдации: {ai_text}"
    return render_template("index.html", recommendation=recommendation, user_text=user_text)


# @app.route(rule='/submit', methods=["POST"])
# def submit():
#     user_message = request.form.get("message", "")
#     if not user_message.strip():
#         reply = "Ты ничего не написал, БЕЗДАРЬ!"
#     else:
#         reply = f"Я получил твой текст: {user_message}"

#     return render_template(template_name_or_list="result.html", user_message=user_message, reply=reply)

if __name__ == "__main__":
    app.run(debug=True)