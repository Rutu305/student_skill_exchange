import json
import re
import requests
from flask import current_app

def generate_mcqs_with_gemini(skill):
    """
    Generates 5 MCQ questions for a given skill using the Gemini API.
    Falls back gracefully to rich predefined questions if API is unavailable,
    quota is exceeded, or key is invalid.
    """
    api_key = current_app.config.get('GEMINI_API_KEY')
    api_url = current_app.config.get('GEMINI_API_URL')
    
    if not api_key:
        return get_predefined_questions(skill)

    prompt = f"""Generate 5 multiple choice questions for a skill test on '{skill}'. 
Each question should have 4 options with exactly one correct answer.
Format the response as a valid JSON array only, no extra text.
Use this exact format:
[
    {{
        "question": "question text here",
        "options": ["option1", "option2", "option3", "option4"],
        "correct": 0
    }}
]
where 'correct' is the index (0-3) of the correct option.
Make questions progressively difficult (easy to hard).
Ensure questions test real knowledge of {skill}."""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        url = f"{api_url}?key={api_key}"
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts and "text" in parts[0]:
                    raw_text = parts[0]["text"]
                    cleaned_text = re.sub(r'```(?:json)?|\s*```', '', raw_text).strip()
                    questions = json.loads(cleaned_text)
                    if isinstance(questions, list) and len(questions) == 5:
                        # Validate structure
                        valid = True
                        for q in questions:
                            if not (isinstance(q, dict) and 'question' in q and 'options' in q and 'correct' in q):
                                valid = False
                                break
                            if not (isinstance(q['options'], list) and len(q['options']) == 4 and 0 <= q['correct'] <= 3):
                                valid = False
                                break
                        if valid:
                            return questions
    except Exception as e:
        print(f"[Gemini API Warning]: {e}. Using predefined questions for '{skill}'.")

    return get_predefined_questions(skill)


def get_predefined_questions(skill):
    """
    Returns curated, high-quality MCQs for the skill if Gemini is unreachable.
    """
    s = skill.lower()

    if 'java' in s and 'javascript' not in s:
        return [
            {'question': 'What is the correct way to declare a main method in Java?', 'options': ['public static void main(String[] args)', 'public void main(String[] args)', 'static void main(String[] args)', 'public static main(String[] args)'], 'correct': 0},
            {'question': 'Which keyword is used to inherit a class in Java?', 'options': ['implements', 'extends', 'inherits', 'super'], 'correct': 1},
            {'question': 'What is JVM in Java?', 'options': ['Java Variable Machine', 'Java Virtual Machine', 'Java Very Method', 'Java Verified Machine'], 'correct': 1},
            {'question': 'Which of the following is not a Java feature?', 'options': ['Object-oriented', 'Platform independent', 'Multiple inheritance using classes', 'Automatic memory management'], 'correct': 2},
            {'question': 'What is the default value of int variable in Java?', 'options': ['0', 'null', 'undefined', '1'], 'correct': 0}
        ]

    elif 'python' in s:
        return [
            {'question': 'Which of the following is used to print output in Python?', 'options': ['console.log()', 'echo', 'print()', 'system.out.println()'], 'correct': 2},
            {'question': 'What is the correct file extension for Python files?', 'options': ['.pyth', '.pt', '.py', '.pyt'], 'correct': 2},
            {'question': 'Which of the following is used to take user input in Python?', 'options': ['input()', 'scan()', 'read()', 'get()'], 'correct': 0},
            {'question': 'What will be the output of print(type(10)) in Python?', 'options': ['<class int>', '<class float>', '<class str>', '<class list>'], 'correct': 0},
            {'question': 'Which keyword is used to define a function in Python?', 'options': ['func', 'define', 'def', 'function'], 'correct': 2}
        ]

    elif 'javascript' in s or 'js' in s:
        return [
            {'question': 'How do you declare a variable in modern JavaScript?', 'options': ['var', 'let', 'const', 'All of the above'], 'correct': 3},
            {'question': 'What does DOM stand for?', 'options': ['Document Object Model', 'Data Object Model', 'Document Oriented Model', 'Display Object Model'], 'correct': 0},
            {'question': 'Which symbol is used for single-line comments in JavaScript?', 'options': ['<!-- -->', '//', '#', '/* */'], 'correct': 1},
            {'question': 'How do you write an if statement in JavaScript?', 'options': ['if (i === 5)', 'if i == 5 then', 'if i = 5', 'if i == 5:'], 'correct': 0},
            {'question': 'Which company originally developed JavaScript?', 'options': ['Microsoft', 'Netscape', 'Google', 'Apple'], 'correct': 1}
        ]

    elif 'react' in s:
        return [
            {'question': 'What is React primarily used for?', 'options': ['Database management', 'Building user interfaces', 'Operating systems', 'Network routing'], 'correct': 1},
            {'question': 'What is JSX in React?', 'options': ['A syntax extension for JavaScript', 'A database engine', 'A CSS preprocessor', 'A testing library'], 'correct': 0},
            {'question': 'Which React hook is used to manage local component state?', 'options': ['useEffect', 'useState', 'useContext', 'useRef'], 'correct': 1},
            {'question': 'How are props passed to a React child component?', 'options': ['Via HTML attributes', 'Through global variables', 'Using CSS selectors', 'Via server cookies'], 'correct': 0},
            {'question': 'What is the purpose of the Virtual DOM?', 'options': ['Direct hardware access', 'Optimizing UI updates and re-renders', 'Encrypting HTTP requests', 'Managing SQL queries'], 'correct': 1}
        ]

    elif 'node' in s:
        return [
            {'question': 'What engine powers Node.js?', 'options': ['SpiderMonkey', 'V8 JavaScript Engine', 'Chakra', 'Nitro'], 'correct': 1},
            {'question': 'What is NPM in the Node.js ecosystem?', 'options': ['Node Performance Monitor', 'Node Package Manager', 'New Python Module', 'Network Protocol Mode'], 'correct': 1},
            {'question': 'Which core module is used to handle file operations in Node.js?', 'options': ['path', 'fs', 'http', 'os'], 'correct': 1},
            {'question': 'Node.js runtime model is based on which paradigm?', 'options': ['Single-threaded event loop', 'Multi-threaded synchronous', 'Kernel thread pool only', 'Blocking synchronous'], 'correct': 0},
            {'question': 'How do you import a module using CommonJS syntax in Node.js?', 'options': ['import x from "x"', 'require("x")', 'include("x")', 'using "x"'], 'correct': 1}
        ]

    elif 'php' in s:
        return [
            {'question': 'What does PHP stand for?', 'options': ['Personal Home Page', 'Preprocessor Hypertext', 'PHP Hypertext Preprocessor', 'Private Home Page'], 'correct': 2},
            {'question': 'How do you start a session in PHP?', 'options': ['start_session()', 'session_start()', 'begin_session()', 'init_session()'], 'correct': 1},
            {'question': 'Which symbol is used to declare a variable in PHP?', 'options': ['$', '@', '#', '&'], 'correct': 0},
            {'question': 'Which extension or driver is commonly used for secure MySQL connections in modern PHP?', 'options': ['mysql_connect', 'PDO / MySQLi', 'sqlite3', 'postgre_driver'], 'correct': 1},
            {'question': 'What does $_POST superglobal do in PHP?', 'options': ['Sends data via URL query', 'Collects HTTP POST form data', 'Prints debug logs', 'Destroys the session'], 'correct': 1}
        ]

    elif 'html' in s or 'css' in s:
        return [
            {'question': 'What does HTML stand for?', 'options': ['Hyper Text Markup Language', 'High Tech Modern Language', 'Hyper Transfer Markup Language', 'Home Tool Markup Language'], 'correct': 0},
            {'question': 'Which tag is used for the primary highest-level heading in HTML?', 'options': ['<head>', '<h1>', '<title>', '<header>'], 'correct': 1},
            {'question': 'Which CSS property changes text color?', 'options': ['text-color', 'font-color', 'color', 'bgcolor'], 'correct': 2},
            {'question': 'What is the correct HTML element for inserting a line break?', 'options': ['<lb>', '<break>', '<br>', '<newline>'], 'correct': 2},
            {'question': 'Which CSS property controls the outer spacing around elements?', 'options': ['spacing', 'margin', 'padding', 'gap'], 'correct': 1}
        ]

    elif 'sql' in s or 'database' in s:
        return [
            {'question': 'What does SQL stand for?', 'options': ['Structured Query Language', 'Simple Question Language', 'Standard Quality Language', 'Sequential Query Logic'], 'correct': 0},
            {'question': 'Which SQL command is used to retrieve data from a database?', 'options': ['FETCH', 'GET', 'SELECT', 'OPEN'], 'correct': 2},
            {'question': 'Which clause is used to filter records in a SQL SELECT statement?', 'options': ['ORDER BY', 'WHERE', 'GROUP BY', 'HAVING'], 'correct': 1},
            {'question': 'What keyword is used to add new rows into a SQL table?', 'options': ['ADD ROW', 'INSERT INTO', 'PUT INTO', 'UPDATE'], 'correct': 1},
            {'question': 'What is a PRIMARY KEY in SQL?', 'options': ['A password to the DB', 'A unique identifier for each record in a table', 'The first column of any table', 'An encrypted field'], 'correct': 1}
        ]

    elif 'design' in s or 'ui' in s or 'ux' in s:
        return [
            {'question': 'What does UX stand for?', 'options': ['Universal XML', 'User Experience', 'User Extension', 'Unified Exploration'], 'correct': 1},
            {'question': 'What does UI stand for in digital product design?', 'options': ['User Interface', 'Universal Integration', 'User Internet', 'Unit Identifier'], 'correct': 0},
            {'question': 'What is a wireframe in UI/UX design?', 'options': ['Final production code', 'A low-fidelity visual guide of a page structure', 'A graphic animation', 'A database schema'], 'correct': 1},
            {'question': 'Which principle focuses on the visual weight of elements on a screen?', 'options': ['Hierarchy & Contrast', 'Bandwidth', 'Polymorphism', 'Refactoring'], 'correct': 0},
            {'question': 'What is the 60-30-10 rule commonly applied to in design?', 'options': ['Font sizes', 'Color palette distribution', 'Button border radius', 'Image compression'], 'correct': 1}
        ]

    elif 'english' in s:
        return [
            {'question': 'Which sentence is grammatically correct?', 'options': ['I went to school yesterday', 'I go to school yesterday', 'I goes to school yesterday', 'I am go to school yesterday'], 'correct': 0},
            {'question': 'What is the past tense of the verb "run"?', 'options': ['ran', 'runned', 'running', 'runs'], 'correct': 0},
            {'question': 'Choose the correct synonym for "Joyful":', 'options': ['Sad', 'Happy', 'Angry', 'Tired'], 'correct': 1},
            {'question': 'What is a noun?', 'options': ['An action word', 'A person, place, or thing', 'A describing word', 'A connecting conjunction'], 'correct': 1},
            {'question': 'Which sentence uses correct subject-verb agreement?', 'options': ['She dont like pizza', 'She doesn\'t like pizza', 'She don\'t likes pizza', 'She not like pizza'], 'correct': 1}
        ]

    elif 'spanish' in s:
        return [
            {'question': 'How do you say "Hello" in Spanish?', 'options': ['Hola', 'Buenos Dias', 'Adios', 'Gracias'], 'correct': 0},
            {'question': 'What does "Gracias" mean in English?', 'options': ['Goodbye', 'Please', 'Thank you', 'Excuse me'], 'correct': 2},
            {'question': 'What is the Spanish word for the number "1"?', 'options': ['Uno', 'Dos', 'Tres', 'Cuatro'], 'correct': 0},
            {'question': 'How do you say "Friend" in Spanish?', 'options': ['Familia', 'Amigo', 'Casa', 'Trabajo'], 'correct': 1},
            {'question': 'What color is "Rojo"?', 'options': ['Blue', 'Green', 'Yellow', 'Red'], 'correct': 3}
        ]

    elif 'french' in s:
        return [
            {'question': 'How do you say "Hello" or "Good day" in French?', 'options': ['Bonjour', 'Merci', 'Au revoir', 'S\'il vous plaît'], 'correct': 0},
            {'question': 'What does "Merci" mean in English?', 'options': ['Please', 'Thank you', 'Goodbye', 'Yes'], 'correct': 1},
            {'question': 'What is the French word for "Yes"?', 'options': ['Non', 'Oui', 'Bien', 'Très'], 'correct': 1},
            {'question': 'What does "Au revoir" mean?', 'options': ['Welcome', 'Good night', 'Goodbye', 'See you yesterday'], 'correct': 2},
            {'question': 'What number is "Trois" in English?', 'options': ['One', 'Two', 'Three', 'Four'], 'correct': 2}
        ]

    # Universal tech/skill fallback
    capitalized = skill.title()
    return [
        {'question': f'What is the fundamental first step when learning {capitalized}?', 'options': ['Mastering foundational concepts', 'Skipping straight to complex systems', 'Only memorizing formulas', 'Avoiding hands-on exercises'], 'correct': 0},
        {'question': f'Which approach is proven to accelerate mastery in {capitalized}?', 'options': ['Passive reading only', 'Hands-on practice and building projects', 'Never asking questions', 'Working with no feedback'], 'correct': 1},
        {'question': f'Why is peer collaboration valuable when learning {capitalized}?', 'options': ['Exchanging diverse problem-solving perspectives', 'Passing blame for errors', 'Avoiding personal practice', 'None of the above'], 'correct': 0},
        {'question': f'Which resource is recommended for continuing development in {capitalized}?', 'options': ['Official documentation & tutorials', 'Open source repositories', 'Community study groups', 'All of the above'], 'correct': 3},
        {'question': f'How can you effectively measure your competency in {capitalized}?', 'options': ['Building verifiable real-world projects', 'Guessing answers randomly', 'Ignoring errors', 'Relying only on subjective feelings'], 'correct': 0}
    ]
