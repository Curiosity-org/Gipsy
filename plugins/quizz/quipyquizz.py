"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import json
import requests


class QuiPyQuizz:
    """
    QuiPyQuizz
    Utilise l'API de quipoquiz.com afin de créer un quizz interactif sur Discord
    """
    def __init__(self):
        with open("plugins/quizz/data/quizz.json", "r", encoding="utf-8") as file:
            self.data = json.load(file)

    @staticmethod
    def request_questions(quizz):
        """
        Récupère les questions d'un quizz depuis l'API de quipoquiz.com

        :param quizz: ID du quizz
        :type quizz: int

        :return: Dictionnaire contenant les questions et/ou les erreurs
        :rtype: dict

        >>> QuiPyQuizz.request_questions(1)
            {
                "errcode": 0,
                "errmesg": "",
                "questions": [
                    {
                        "image": "/sn_uploads/quizzes/a10e63da6494d4ee5c588cbf251ceb401465146801107.jpeg",
                        "question": "La phrase « j’ignore si j’ai un ecchymose ou un hématome » est juste.",
                        "credit": "Myk-haematoma. By MykReeve [CC BY-SA 3.0 or GFDL], via Wikimedia Commons",
                        "uid_variation": "25"
                    },
                    ...
                ]
            }
        """
        params = {"quiz": str(quizz)}  # Payload
        request = requests.get(
            url="https://quipoquiz.com/module/sed/quiz/fr/start_quiz.snc",
            params=params,
            timeout=10
        )
        payload = json.loads(request.text)
        return payload["questions"]

    @staticmethod
    def request_answer(uid_variation, question_id, answer: str):
        """
        Demande à l'API de quipoquiz.com si la réponse est correcte

        :param uid_variation: ID de la variation de la question
        :type uid_variation: int
        :param question_id: ID de la question
        :type question_id: int
        :param answer: Réponse à la question
        :type answer: str

        :return: Dictionnaire contenant la réponse et/ou les erreurs
        :rtype: dict

        >>> QuiPyQuizz.request_answer(25, 1, "vrai")
        {
            "answer": {
                "correct": false,
                "explanation": "La réponse est FAUX. "
            },
            "errcode": 0,
            "errmesg": ""
        }
        """
        params = {
            "quiz": uid_variation,  # Payload
            "answer": answer.lower(),
            "question": question_id,
        }
        request = requests.get(
            url="https://quipoquiz.com/module/sed/quiz/fr/answer_question.snc",
            params=params,
            timeout=10
        )
        payload = json.loads(request.text)
        return payload["answer"]

    @staticmethod
    def request_stats(quizz):
        """
        Récupère les statistiques d'un quizz depuis l'API de quipoquiz.com

        :param quizz: ID du quizz
        :type quizz: int

        :return: Dictionnaire contenant les statistiques et/ou les erreurs
        :rtype: dict

        >>> QuiPyQuizz.request_stats(1)
        {
            "result": {
                "statistics": {
                    "new_avg": 73.6717463,
                    "nb_attempt": "208286"
                },
                "correct": "0",
                "total": "10"
            },
            "errcode": 0,
            "errmesg": ""
        }
        """
        params = {"quiz": str(quizz)}  # Payload
        request = requests.get(
            url="https://quipoquiz.com/module/sed/quiz/fr/end_quiz.snc",
            params=params,
            timeout=10
        )
        payload = json.loads(request.text)
        return payload["result"]["statistics"]

    def get_name(self, quizz_id):
        """
        Récupère le nom d'un quizz à partir de son ID

        :param quizz_id: ID du quizz
        :type quizz_id: int

        :return: Nom du quizz
        :rtype: str

        >>> QuiPyQuizz.get_name(1)
        "Quizz de test"
        """
        if quizz_id in self.data:
            return self.data[quizz_id]["name"]
        return None

    def get_url(self, quizz_id):
        """
        Récupère l'URL d'un quizz à partir de son ID

        :param quizz_id: ID du quizz
        :type quizz_id: int

        :return: URL du quizz
        :rtype: str

        >>> QuiPyQuizz.get_url(1)
        "https://quipoquiz.com/quiz/quizz-de-test"
        """
        if quizz_id in self.data:
            return f"https://quipoquiz.com/quiz/{self.data[quizz_id]['url']}"
        return None

    def get_question(self, quizz_id, question_id):
        """
        Récupère une question d'un quizz à partir de leurs ID

        :param quizz_id: ID du quizz
        :type quizz_id: int
        :param question_id: ID de la question
        :type question_id: int

        :return: Dictionnaire contenant les informations de la question
        :rtype: dict

        >>> QuiPyQuizz.get_question(1, 1)
            {
            "question": "<p>Les chytridiomycètes sont-ils des champignons aquatiques ou semi-aquatiques ?</p>",
            "credit": "Wikipedia",
            "image": "/sn_uploads/quizzes/13_wiki_Synchytrium_on_Erodium_cicutarium.jpg"
            }

        """
        if quizz_id in self.data and question_id in self.data[quizz_id]["questions"]:
            return self.data[quizz_id]["questions"][question_id]
        return None

    def get_questions(self, quizz_id):
        """
        Récupère toutes les questions d'un quizz à partir de son ID

        :param quizz_id: ID du quizz
        :type quizz_id: int

        :return: Dictionnaire contenant les informations de toutes les questions
        :rtype: dict

        >>> QuiPyQuizz.get_questions(1)
            {
                "14180": {
                    "question": "<p>Les chytridiomycètes sont des champignons aquatiques ou semi-aquatiques.</p>",
                    "credit": "Wikipedia",
                    "image": "/sn_uploads/quizzes/13_wiki_Synchytrium_on_Erodium_cicutarium.jpg"
                },
                ...
            }
        """
        if quizz_id in self.data:
            return self.data[quizz_id]["questions"]
        return None

    def get_answer(self, quizz_id, question_id):
        """
        Récupère la réponse d'une question d'un quizz à partir de leurs ID

        :param quizz_id: ID du quizz
        :type quizz_id: int
        :param question_id: ID de la question
        :type question_id: int

        :return: Dictionnaire contenant les informations de la réponse
        :rtype: dict

        >>> QuiPyQuizz.get_answer(1, 1)
            {
                "real_answer": true,
                "explanation": "La réponse est VRAI. <p>C'est le seul champignon à avoir des spores uniflagellées.</p>"
            }
        """
        if quizz_id in self.data and question_id in self.data[quizz_id]["answers"]:
            return self.data[quizz_id]["answers"][question_id]
        return None
