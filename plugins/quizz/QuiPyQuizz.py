import requests
import json
import os


class QuiPyQuizz:
    def __init__(self):
        with open("plugins/quizz/data/quizz.json", "r", encoding="utf-8") as f:
            self.data = json.load(f)

    @staticmethod
    def request_questions(quizz):
        params = {"quiz": str(quizz)}  # Payload
        r = requests.get(
            url="https://quipoquiz.com/module/sed/quiz/fr/start_quiz.snc", params=params
        )
        paulaod = json.loads(r.text)
        return paulaod["questions"]

    @staticmethod
    def request_answer(uid_variation, question_id, answer: str):
        params = {
            "quiz": uid_variation,  # Payload
            "answer": answer.lower(),
            "question": question_id,
        }
        r = requests.get(
            url="https://quipoquiz.com/module/sed/quiz/fr/answer_question.snc",
            params=params,
        )
        pauload = json.loads(r.text)
        return pauload["answer"]

    @staticmethod
    def request_stats(quizz):
        params = {"quiz": str(quizz)}  # Payload
        r = requests.get(
            url="https://quipoquiz.com/module/sed/quiz/fr/end_quiz.snc", params=params
        )
        pauload = json.loads(r.text)
        return pauload["result"]["statistics"]

    def get_name(self, quizz_id):
        if quizz_id in self.data:
            return self.data[quizz_id]["name"]
        else:
            return None

    def get_url(self, quizz_id):
        if quizz_id in self.data:
            return f"https://quipoquiz.com/quiz/{self.data[quizz_id]['url']}"
        else:
            return None

    def get_question(self, quizz_id, question_id):
        if quizz_id in self.data and question_id in self.data[quizz_id]["questions"]:
            return self.data[quizz_id]["questions"][question_id]
            """
            Exemple:
            {
                "question": "<p>Les chytridiomycètes sont des champignons aquatiques ou semi-aquatiques.</p>\n",
                "credit": "Wikipedia",
                "image": "/sn_uploads/quizzes/13_wiki_Synchytrium_on_Erodium_cicutarium.jpg"
            }
            """
        else:
            return None

    def get_questions(self, quizz_id):
        if quizz_id in self.data:
            return self.data[quizz_id]["questions"]
            """
            Exemple:
            {
              "14180": {
                "question": "<p>Les chytridiomycètes sont des champignons aquatiques ou semi-aquatiques.</p>\n",
                "credit": "Wikipedia",
                "image": "/sn_uploads/quizzes/13_wiki_Synchytrium_on_Erodium_cicutarium.jpg"
              },
              ...
            }
            """
        else:
            return None

    def get_answer(self, quizz_id, question_id):
        if quizz_id in self.data and question_id in self.data[quizz_id]["answers"]:
            return self.data[quizz_id]["answers"][question_id]
            """
            Exemple:
            {
              "real_answer": true,
              "explanation": "La réponse est VRAI. <p>Ce sont les seuls champignons à avoir encore des spores uniflagellées.</p>\n"
            }
            """
        else:
            return None
