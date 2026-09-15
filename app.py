import os
import json
import pickle
import sqlite3

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

from groq import Groq
import pandas as pd
from model_training import train_model
from workout_generator import generate_workout_plan


app = Flask(__name__)
app.secret_key = "your-secret-key"

# ================================
# SQLITE DATABASE
# ================================

DATABASE = "users.db"


def init_db():
    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ================================
# LOAD GROQ API KEY FROM Api-2.txt
# ================================

def load_api_key():
    try:
        with open("Api-2.txt", "r") as f:
            key = f.read().strip()

        if not key.startswith("gsk_"):
            raise Exception("Invalid Groq API Key Format!")

        return key

    except FileNotFoundError:
        raise Exception("Api-2.txt not found in project root!")

    except Exception as e:
        raise Exception(f"API Key Error: {str(e)}")


api_key = load_api_key()
client = Groq(api_key=api_key)


# ================================
# LOAD OR TRAIN MODEL
# ================================

try:
    with open("nutrition_model.pkl", "rb") as f:
        model = pickle.load(f)

except FileNotFoundError:
    print("Model not found. Training model now...")
    train_model()

    with open("nutrition_model.pkl", "rb") as f:
        model = pickle.load(f)


# ================================
# REGISTER ROUTE
# ================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            return render_template(
                "register.html",
                error="All fields are required"
            )

        if password != confirm_password:
            return render_template(
                "register.html",
                error="Passwords do not match"
            )

        if len(password) < 6:
            return render_template(
                "register.html",
                error="Password must be at least 6 characters"
            )

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return render_template(
                "register.html",
                error="Email already registered"
            )

        hashed_password = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
            """,
            (name, email, hashed_password)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# ================================
# LOGIN ROUTE
# ================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name, email, password FROM users WHERE email = ?",
            (email,)
        )

        user = cursor.fetchone()
        conn.close()

        if user is None:
            return render_template(
                "login.html",
                error="Invalid email or password"
            )

        user_id, name, user_email, hashed_password = user

        if not check_password_hash(hashed_password, password):
            return render_template(
                "login.html",
                error="Invalid email or password"
            )

        session["user_id"] = user_id
        session["user"] = user_email
        session["name"] = name

        return redirect(url_for("home"))

    return render_template("login.html")


# ================================
# LOGOUT ROUTE
# ================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ================================
# HOME ROUTE
# ================================

@app.route("/")
def home():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "index.html",
        username=session.get("name")
    )


# ================================
# RESULT ROUTE
# ================================

@app.route("/result")
def result():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("result.html")


# ================================
# PREDICTION ROUTE
# ================================

@app.route("/predict", methods=["POST"])
def predict():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Please login first"
        }), 401

    try:
        data = request.get_json(silent=True) or {}

        age = int(data.get("age", 25))
        gender = int(data.get("gender", 0))
        height = float(data.get("height", 165))
        weight = float(data.get("weight", 65))
        activity_level = int(data.get("activity_level", 1))
        goal = int(data.get("fitness_goal", 1))

        workout_experience = data.get(
            "workout_experience",
            "beginner"
        )

        workout_location = data.get(
            "workout_location",
            "home"
        )

        # ================================
        # BMI
        # ================================

        if height <= 0 or weight <= 0:
            raise ValueError("Height and weight must be greater than 0.")

        bmi = weight / ((height / 100) ** 2)

        # ================================
        # BMR - Mifflin-St Jeor
        # ================================

        if gender == 1:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

        # ================================
        # TDEE
        # ================================

        activity_multipliers = {
            0: 1.2,
            1: 1.375,
            2: 1.55,
            3: 1.725,
            4: 1.9
        }

        tdee = bmr * activity_multipliers.get(
            activity_level,
            1.55
        )

        # ================================
        # ML NUTRITION PREDICTION
        # ================================

        feature_df = pd.DataFrame(
            [[
                age,
                gender,
                height,
                weight,
                bmi,
                activity_level,
                goal
            ]],
            columns=[
                "Age",
                "Gender",
                "Height",
                "Weight",
                "BMI",
                "ActivityLevel",
                "Goal"
            ]
        )

        predictions = model.predict(feature_df)[0]

        cals, protein, carbs, fat = predictions

        # ================================
        # DIET INFORMATION
        # ================================

        diet_type = data.get(
            "diet_type",
            "Vegetarian"
        )

        disease = data.get(
            "health_condition",
            "None"
        )

        diet_type_label = diet_type

        if diet_type == "NonVeg":
            diet_type_label = "Non-Veg"
        elif diet_type == "Eggetarian":
            diet_type_label = "Egg"

        constraints = ""

        if diet_type == "Vegetarian":
            constraints = (
                "Strictly Vegetarian. "
                "No eggs, chicken, fish or meat."
            )

        elif diet_type == "Eggetarian":
            constraints = (
                "Eggetarian. Eggs are allowed. "
                "No chicken, fish or meat."
            )

        elif diet_type == "NonVeg":
            constraints = (
                "Non-Vegetarian. "
                "Chicken, fish and eggs are allowed."
            )

        if disease and disease.lower() != "none":
            constraints += (
                f" User has {disease}. "
                "Avoid foods that may be harmful for this condition."
            )

            disease_note = (
                f"For a person with {disease}, set "
                '"disease_friendly" to true only for suitable meals.'
            )

        else:
            disease_note = (
                'Set "disease_friendly" to true for all meals.'
            )

        # ================================
        # GROQ - GENERATE ONE DAY AT A TIME
        # ================================
        # Generating 7 complete days in one request can make the model
        # accidentally omit a meal. One-day-at-a-time generation is much
        # more reliable and keeps the frontend response format unchanged.

        required_meals = [
            "Breakfast",
            "MidMorningSnack",
            "Lunch",
            "EveningSnack",
            "Dinner"
        ]

        required_fields = [
            "name",
            "diet_type",
            "disease_friendly",
            "ingredients",
            "steps"
        ]
        def generate_one_day(day_number):
            day_key = f"Day{day_number}"

            system_prompt = f"""
        You are an expert Indian diet planner.

        Generate ONLY {day_key}.

        RETURN ONLY VALID JSON.
        Do NOT use markdown.
        Do NOT use ```json.
        Do NOT add explanations.
        Do NOT add comments.

        The JSON MUST contain exactly these 5 keys:

        Breakfast
        MidMorningSnack
        Lunch
        EveningSnack
        Dinner

        Each meal MUST contain exactly these 5 fields:

        "name": string
        "diet_type": string
        "disease_friendly": boolean
        "ingredients": array of strings
        "steps": array of strings

        Allowed diet_type values:
        "Veg", "Egg", "Non-Veg"

        IMPORTANT JSON RULES:
        - Use double quotes only for JSON syntax.
        - Never put double quotation marks inside a string value.
        - Do not use newline characters inside strings.
        - ingredients must be short strings.
        - steps must be short strings.
        - disease_friendly must be true or false.
        - Do not omit any meal.
        - Do not create extra keys.
        - Keep the response compact.

        Diet type:
        {diet_type_label}

        Dietary constraints:
        {constraints}

        Health condition:
        {disease}

        Health rule:
        {disease_note}

        Create practical Indian meals.
        """

            user_prompt = f"""
        Generate {day_key}.

        Daily nutrition target:
        Calories: {cals:.0f} kcal
        Protein: {protein:.0f} g
        Carbs: {carbs:.0f} g
        Fat: {fat:.0f} g

        Return ONLY the JSON object.

        Required meals:
        Breakfast
        MidMorningSnack
        Lunch
        EveningSnack
        Dinner
        """

            last_error = None

            for attempt in range(3):

                try:
                    response = client.chat.completions.create(
                        model="openai/gpt-oss-20b",
                        messages=[
                            {
                                "role": "system",
                                "content": system_prompt
                            },
                            {
                                "role": "user",
                                "content": user_prompt
                            }
                        ],
                        temperature=0,
                        reasoning_effort="low",
                        max_completion_tokens=4000,
                        top_p=1,
                        stream=False,
                       response_format={
    "type": "json_schema",
    "json_schema": {
        "name": "daily_diet_plan",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "Breakfast": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "diet_type": {"type": "string"},
                        "disease_friendly": {"type": "boolean"},
                        "ingredients": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "steps": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": [
                        "name",
                        "diet_type",
                        "disease_friendly",
                        "ingredients",
                        "steps"
                    ],
                    "additionalProperties": False
                },
                "MidMorningSnack": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "diet_type": {"type": "string"},
                        "disease_friendly": {"type": "boolean"},
                        "ingredients": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "steps": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": [
                        "name",
                        "diet_type",
                        "disease_friendly",
                        "ingredients",
                        "steps"
                    ],
                    "additionalProperties": False
                },
                "Lunch": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "diet_type": {"type": "string"},
                        "disease_friendly": {"type": "boolean"},
                        "ingredients": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "steps": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": [
                        "name",
                        "diet_type",
                        "disease_friendly",
                        "ingredients",
                        "steps"
                    ],
                    "additionalProperties": False
                },
                "EveningSnack": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "diet_type": {"type": "string"},
                        "disease_friendly": {"type": "boolean"},
                        "ingredients": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "steps": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": [
                        "name",
                        "diet_type",
                        "disease_friendly",
                        "ingredients",
                        "steps"
                    ],
                    "additionalProperties": False
                },
                "Dinner": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "diet_type": {"type": "string"},
                        "disease_friendly": {"type": "boolean"},
                        "ingredients": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "steps": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": [
                        "name",
                        "diet_type",
                        "disease_friendly",
                        "ingredients",
                        "steps"
                    ],
                    "additionalProperties": False
                }
            },
            "required": [
                "Breakfast",
                "MidMorningSnack",
                "Lunch",
                "EveningSnack",
                "Dinner"
            ],
            "additionalProperties": False
        }
    }
}
                    )

                    raw = (
                        response.choices[0].message.content or ""
                    ).strip()

                    print(f"\n========== {day_key} RAW RESPONSE ==========")
                    print(raw)
                    print("============================================\n")

                    # Remove markdown fences if model accidentally adds them
                    if raw.startswith("```"):
                        raw = raw.replace("```json", "", 1)
                        raw = raw.replace("```JSON", "", 1)

                        if raw.endswith("```"):
                            raw = raw[:-3]

                        raw = raw.strip()

                    # Find the JSON object if extra text somehow appears
                    start = raw.find("{")
                    end = raw.rfind("}")

                    if start == -1 or end == -1 or end <= start:
                        raise ValueError(
                            f"{day_key}: AI did not return a valid JSON object."
                        )

                    raw = raw[start:end + 1]

                    # Parse JSON
                    day_plan = json.loads(raw)

                    if not isinstance(day_plan, dict):
                        raise ValueError(
                            f"{day_key}: response is not a JSON object."
                        )

                    # Required meals
                    required_meals = [
                        "Breakfast",
                        "MidMorningSnack",
                        "Lunch",
                        "EveningSnack",
                        "Dinner"
                    ]

                    required_fields = [
                        "name",
                        "diet_type",
                        "disease_friendly",
                        "ingredients",
                        "steps"
                    ]

                    # Check every meal
                    for meal in required_meals:

                        if meal not in day_plan:
                            raise ValueError(
                                f"{day_key} is missing {meal}."
                            )

                        meal_data = day_plan[meal]

                        if not isinstance(meal_data, dict):
                            raise ValueError(
                                f"{day_key} {meal} is not valid."
                            )

                        # Check required fields
                        for field in required_fields:

                            if field not in meal_data:
                                raise ValueError(
                                    f"{day_key} {meal} is missing {field}."
                                )

                        # Validate data types
                        if not isinstance(meal_data["name"], str):
                            raise ValueError(
                                f"{day_key} {meal} name is invalid."
                            )

                        if meal_data["diet_type"] not in [
                            "Veg",
                            "Egg",
                            "Non-Veg"
                        ]:
                            raise ValueError(
                                f"{day_key} {meal} has invalid diet_type."
                            )

                        if not isinstance(
                            meal_data["disease_friendly"],
                            bool
                        ):
                            raise ValueError(
                                f"{day_key} {meal} disease_friendly must be true/false."
                            )

                        if not isinstance(
                            meal_data["ingredients"],
                            list
                        ):
                            raise ValueError(
                                f"{day_key} {meal} ingredients must be a list."
                            )

                        if not isinstance(
                            meal_data["steps"],
                            list
                        ):
                            raise ValueError(
                                f"{day_key} {meal} steps must be a list."
                            )

                    # Return only required meals
                    return {
                        meal: day_plan[meal]
                        for meal in required_meals
                    }

                except json.JSONDecodeError as e:

                    last_error = e

                    print(
                        f"{day_key} JSON error on attempt "
                        f"{attempt + 1}: {e}"
                    )

                    # Make the next attempt even stricter
                    user_prompt = f"""
        Generate {day_key} again.

        IMPORTANT:
        Your previous answer was NOT valid JSON.

        Return ONLY a valid JSON object.

        Do NOT use markdown.
        Do NOT use code fences.
        Do NOT write explanations.
        Do NOT use double quotes inside meal text.
        Do NOT omit Dinner.

        The object MUST contain exactly:

        Breakfast
        MidMorningSnack
        Lunch
        EveningSnack
        Dinner

        Each meal MUST contain:

        name
        diet_type
        disease_friendly
        ingredients
        steps

        Daily target:
        Calories: {cals:.0f}
        Protein: {protein:.0f}
        Carbs: {carbs:.0f}
        Fat: {fat:.0f}
        """

                except ValueError as e:

                    last_error = e

                    print(
                        f"{day_key} validation error on attempt "
                        f"{attempt + 1}: {e}"
                    )

                    user_prompt += f"""

        IMPORTANT RETRY:
        The previous response failed validation because:

        {str(e)}

        Return ONLY valid JSON.
        Include all five meals.
        Especially include Dinner.
        """

                except Exception as e:

                    last_error = e

                    print(
                        f"{day_key} API error on attempt "
                        f"{attempt + 1}: {e}"
                    )

            raise ValueError(
                f"{day_key} could not be generated completely: {last_error}"
    )

        # Build the final 7-day object in Python.
        # This guarantees Day1-Day7 all exist and every day has five meals.
        diet_plan = {}

        for day_number in range(1, 8):
            print(f"Generating Day {day_number}/7...")
            diet_plan[f"Day{day_number}"] = generate_one_day(day_number)

        # ================================
        # GENERATE WORKOUT PLAN
        # ================================

        workout_plan = generate_workout_plan(
            bmi=bmi,
            goal=goal,
            experience=workout_experience,
            location=workout_location,
            health_condition=disease
        )

        # ================================
        # FINAL RESPONSE
        # ================================

        return jsonify({
            "success": True,

            "metrics": {
                "bmi": round(bmi, 1),
                "bmr": round(bmr),
                "tdee": round(tdee),
                "calories": round(cals),
                "protein": round(protein),
                "carbs": round(carbs),
                "fat": round(fat)
            },

            "diet_plan": diet_plan,
            "workout_plan": workout_plan,
            "diet_type": diet_type_label,
            "disease": disease,
            "workout_experience": workout_experience,
            "workout_location": workout_location
        })

    except Exception as e:

        print("========== PREDICT ERROR ==========")
        print(str(e))
        print("===================================")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ================================
# AI FITNESS CHATBOT
# ================================

@app.route("/chat", methods=["POST"])
def chat():

    # Check login
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Your session has expired. Please login again."
        }), 401

    try:
        # Get JSON safely
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid request data."
            }), 400

        # Get message
        message = str(data.get("message", "")).strip()

        if not message:
            return jsonify({
                "success": False,
                "error": "Please enter a message."
            }), 400

        # Limit message size
        message = message[:1000]

        # Get plan context
        context = data.get("context", {})

        if not isinstance(context, dict):
            context = {}
            # ================================
        # SYSTEM PROMPT
        # ================================

        system_prompt = """
You are an AI Fitness Assistant inside an AI Workout & Diet Plan application.

Your job is to help users with:
- Workout plans
- Diet plans
- Healthy food alternatives
- Calories and macros
- Protein, carbohydrates and fats
- BMI, BMR and TDEE
- Beginner exercises
- Workout difficulty
- Fitness habits
- General nutrition information

Use the user's current fitness plan context when it is useful.

RESPONSE STYLE:
1. Answer the user's exact question directly.
2. Keep responses SHORT and conversational.
3. Normally answer in 2-5 sentences.
4. Use simple, beginner-friendly language.
5. Use bullet points only when useful.
6. Do NOT create tables unless the user specifically asks for a table.
7. Do NOT provide long exercise guides unless the user asks for detailed instructions.
8. Do NOT add unnecessary sections.
9. Do NOT repeat information that the user did not ask for.
10. If the user asks a simple question, give a simple answer.
11. If the user asks for steps, give only the necessary steps.

SAFETY:
1. Do not diagnose diseases.
2. Do not prescribe medicines.
3. Do not provide medication dosage.
4. If the user mentions a serious medical condition, pregnancy,
   serious symptoms, or medication, recommend consulting a qualified
   doctor, dietitian, or healthcare professional.
5. Do not pretend to be a doctor.

Always prioritize being clear, helpful, concise, and directly relevant
to the user's question.
"""

        # ================================
        # USER PROMPT
        # ================================

        user_prompt = f"""
User name:
{session.get("name", "User")}

Current fitness plan:
{json.dumps(context, ensure_ascii=False)[:10000]}

User question:
{message}
"""

        print("\n========== CHAT REQUEST ==========")
        print("User:", session.get("name", "User"))
        print("Message:", message)

        # ================================
        # GROQ REQUEST
        # ================================

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0.2,
            max_completion_tokens=1200,
            top_p=1,
            stream=False
        )
        # Get AI response
        reply = ""

        if response.choices:
            reply = response.choices[0].message.content or ""

        reply = reply.strip()

        if not reply:
            raise Exception("Groq returned an empty response.")

        print("AI:", reply)
        print("=================================\n")

        return jsonify({
            "success": True,
            "reply": reply
        })

    except Exception as e:

        print("\n========== CHAT ERROR ==========")
        print("Error type:", type(e).__name__)
        print("Error:", str(e))
        print("================================\n")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    except Exception as e:
        print("Chatbot Error:", str(e))
        return jsonify({
            "success": False,
            "error": "Something went wrong. Please try again."
        }), 500
# MAIN
# ================================

if __name__ == "__main__":

    os.makedirs("templates", exist_ok=True)
    os.makedirs("static/css", exist_ok=True)
    os.makedirs("static/js", exist_ok=True)

    app.run(
        debug=True,
        port=5000
    )
