Run learning_app_gui.py to load the application. You can then design and load questions. Heres examples of the two json files it uses, 1. progressiontree.json:

{
  "topics": [
    {
      "name": "Functions",
      "prerequisites": [],
      "completed": true,
      "conditions": {
        "min_questions": 5,
        "min_accuracy": 0.8,
        "min_streak": 3
      }
    },
    {
      "name": "Differentiation",
      "prerequisites": [
        "Functions"
      ],
      "completed": true,
      "conditions": {
        "min_questions": 6,
        "min_accuracy": 0.75,
        "min_streak": 2
      }
    },
    {
      "name": "Integration",
      "prerequisites": [
        "Differentiation"
      ],
      "completed": false,
      "conditions": {
        "min_questions": 7,
        "min_accuracy": 0.8,
        "min_streak": 3
      }
    },
    {
      "name": "Trigonometry",
      "prerequisites": [
        "Functions"
      ],
      "completed": false,
      "conditions": {
        "min_questions": 5,
        "min_accuracy": 0.85,
        "min_streak": 2
      }
    }
  ]
}

2. questions.json

{
  "Functions": [
      {
    "question": "Describe what a linear function is.",
    "difficulty": 2,
    "randomize": false,
    "is_integer": false,
    "params": {},
    "correct_answer": "A function with a constant rate of change",
    "image": null,
    "choices": [],
    "question_type": 2,
    "exact_match": false
    },
    {
      "question": "What is the value of f(x) = {a}x + {b} when x = {c}?",
      "difficulty": 3,
      "randomize": true,
      "is_integer": true,
      "params": {
        "a": { "value": 2, "sd": 0.5 },
        "b": { "value": 1, "sd": 0.5 },
        "c": { "value": 4, "sd": 1 }
      },
      "correct_answer": "{a} * {c} + {b}",
      "image": "based2.png",
      "question_type": 0,
      "choices": [],
      "exact_match": false
    },
    {
      "question": "Solve f(x) = {a}x + {b}, when x = {c}. What is f({c})?",
      "difficulty": 2,
      "randomize": false,
      "is_integer": false,
      "params": {
        "a": { "value": 5, "sd": 0 },
        "b": { "value": 10, "sd": 0 },
        "c": { "value": 3, "sd": 0 }
      },
      "correct_answer": "25",
      "image": "based2.png",
      "question_type": 0,
      "choices": [],
      "exact_match": false
    },
    {
      "question": "Which of the following best describes a linear function?",
      "difficulty": 2,
      "randomize": false,
      "is_integer": false,
      "params": {},
      "correct_answer": "A function with a constant rate of change",
      "image": null,
      "choices": [
        "A function with a constant rate of change",
        "A function that forms a parabola",
        "A function that is undefined at x=0",
        "A function that oscillates"
      ],
      "question_type": 1,
      "exact_match": false
    }
  ],
  "Differentiation": [
    {
      "question": "Differentiate f(x) = {a}x**2 + {b}x + {c}",
      "difficulty": 6,
      "randomize": true,
      "is_integer": true,
      "params": {
        "a": { "value": 3, "sd": 1 },
        "b": { "value": 4, "sd": 1 },
        "c": { "value": 5, "sd": 1 }
      },
      "correct_answer": "2 * {a} * {c} + {b}",
      "image": null,
      "question_type": 0,
      "choices": [],
      "exact_match": false
    },
    {
      "question": "Find the derivative of f(x) = {a}x**3 + {b}x**2",
      "difficulty": 7,
      "randomize": true,
      "is_integer": true,
      "params": {
        "a": { "value": 2, "sd": 0.5 },
        "b": { "value": 1, "sd": 0.5 }
      },
      "correct_answer": "3 * {a} * {c}**2 + 2 * {b} * {c}",
      "image": null,
      "question_type": 0,
      "choices": [],
      "exact_match": false
    },
    {
      "question": "What is the derivative of f(x) = {a}x**2 + {b}x when x = {c}?",
      "difficulty": 5,
      "randomize": false,
      "is_integer": false,
      "params": {
        "a": { "value": 2, "sd": 0 },
        "b": { "value": 3, "sd": 0 },
        "c": { "value": 5, "sd": 0 }
      },
      "correct_answer": "23",
      "image": null,
      "question_type": 0,
      "choices": [],
      "exact_match": false
    }
  ]
}




