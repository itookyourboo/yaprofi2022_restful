from flask import Flask, jsonify
from flask_restful import reqparse, abort, Api, Resource
from flask_restful_swagger import swagger
from random import shuffle
from model import *


promos = {}
participants = {}
prizes = {}


prize_map = lambda p_id: asdict(prizes[p_id])
participant_map = lambda p_id: asdict(participants[p_id])


class PromosListApi(Resource):
    """
    Working with list of promos
    """
    post_parser = reqparse.RequestParser()
    post_parser.add_argument('name', type=str, required=True)
    post_parser.add_argument('description', type=str, required=False)

    @swagger.operation(
        notes='Получение краткой информации (без информации об участниках и призах) обо всех промоакциях',
        nickname='get'
    )
    def get(self):
        return list(map(lambda p: p.short_dict(), promos.values()))

    @swagger.operation(
        notes='Добавление промоакции с возможностью указания названия (name), описания (description) ',
        nickname='post',
        parameters=[
            {
                'name': 'name',
                'required': True,
                'dataType': "string",
                'paramType': 'body'
            },
            {
                'name': 'description',
                'required': False,
                'dataType': "string",
                'paramType': 'body'
            }
        ],
        responseMessages=[
            {
                'code': 200,
                'message': 'Returns ID of created promo'
            },
            {
                'code': 400,
                'message': 'Bad request'
            },
        ]
    )
    def post(self):
        args = PromosListApi.post_parser.parse_args()
        promo = Promo(
            id=len(promos) + 1,
            name=args['name'],
            description=args.get('description'),
        )
        promos[promo.id] = promo
        return jsonify(promo.id)


class PromoApi(Resource):
    put_parser = reqparse.RequestParser()
    put_parser.add_argument('name', type=str, required=False)
    put_parser.add_argument('description', type=str, required=False)

    @swagger.operation(
        notes='Получение полной информации (с информацией об участниках и призах) о промоакции по идентификатору',
        nickname='get',
        parameters=[
            {
                'name': 'promo_id',
                'required': True,
                'dataType': "number",
                'paramType': 'path'
            },
        ],
        responseMessages=[
            {
                'code': 200,
                'message': 'Returns full information about promo'
            },
            {
                'code': 404,
                'message': 'Promo not found'
            },
        ]
    )
    def get(self, promo_id):
        promo = abort_if_promo_not_found(promo_id)
        return promo.full_dict(prize_map, participant_map)

    @swagger.operation(
        notes='''Редактирование промо-акции по идентификатору промо-акции
        Редактировать можно только свойства name, description
        Удалить имя таким образом нельзя, описание – можно''',
        nickname='put',
        parameters=[
            {
                'name': 'promo_id',
                'required': True,
                'dataType': "number",
                'paramType': 'path'
            },
            {
                'name': 'name',
                'required': False,
                'dataType': "string",
                'paramType': 'body'
            },
            {
                'name': 'name',
                'required': False,
                'dataType': "string",
                'paramType': 'body'
            },
        ],
        responseMessages=[
            {
                'code': 200,
                'message': 'Changed promo information'
            },
            {
                'code': 400,
                'message': 'Bad request'
            },
            {
                'code': 404,
                'message': 'Promo not found'
            },
        ]
    )
    def put(self, promo_id):
        promo = abort_if_promo_not_found(promo_id)
        args = PromoApi.put_parser.parse_args()
        if args.get('name', ''):
            promo.name = args['name']
        if args.get('description'):
            promo.description = args['description']

        return promo.short_dict()

    @swagger.operation(
        notes='Удаление промоакции по идентификатору',
        nickname='delete',
        parameters=[
            {
                'name': 'promo_id',
                'required': True,
                'dataType': "number",
                'paramType': 'path'
            },
        ],
        responseMessages=[
            {
                'code': 200,
                'message': 'Deleted'
            },
            {
                'code': 404,
                'message': 'Promo not found'
            },
        ]
    )
    def delete(self, promo_id):
        abort_if_promo_not_found(promo_id)
        promos.pop(promo_id)

        return jsonify('OK')


class ParticipantsListApi(Resource):
    post_parser = reqparse.RequestParser()
    post_parser.add_argument('name', type=str, required=True)

    @swagger.operation(
        notes='Добавление участника в промоакцию по идентификатору промоакции',
        nickname='post',
        parameters=[
            {
                'name': 'promo_id',
                'required': True,
                'dataType': "number",
                'paramType': 'path'
            },
            {
                'name': 'name',
                'required': True,
                'dataType': "string",
                'paramType': 'body'
            }
        ],
        responseMessages=[
            {
                'code': 200,
                'message': 'Returns ID of added participant'
            },
            {
                'code': 400,
                'message': 'Bad request'
            },
            {
                'code': 404,
                'message': 'Promo not found'
            },
        ]
    )
    def post(self, promo_id):
        promo = abort_if_promo_not_found(promo_id)

        args = ParticipantsListApi.post_parser.parse_args()
        participant = Participant(
            id=len(participants) + 1,
            name=args['name']
        )
        participants[participant.id] = participant
        promo.participants.append(participant.id)

        return jsonify(participant.id)


class ParticipantApi(Resource):
    @swagger.operation(
        notes='Удаление участника из промоакции по идентификаторам промоакции и участника',
        nickname='delete',
        parameters=[
            {
                'name': 'promo_id',
                'required': True,
                'dataType': "number",
                'paramType': 'path'
            },
            {
                'name': 'participant_id',
                'required': True,
                'dataType': "number",
                'paramType': 'path'
            }
        ],
        responseMessages=[
            {
                'code': 200,
                'message': 'OK'
            },
            {
                'code': 400,
                'message': 'Bad request'
            },
            {
                'code': 404,
                'message': 'Promo or participant in promo not found'
            },
        ]
    )
    def delete(self, promo_id, participant_id):
        promo = abort_if_promo_not_found(promo_id)
        if participant_id not in promo.participants:
            abort(404, message=f'Participant {participant_id} in promo {promo_id} not found')
        promo.participants.remove(participant_id)
        return jsonify('OK')


class PrizesListApi(Resource):
    post_parser = reqparse.RequestParser()
    post_parser.add_argument('description', type=str, required=True)

    @swagger.operation(
        notes='Добавление приза в промоакцию по идентификатору промоакции',
        nickname='post',
        parameters=[
            {
                'name': 'promo_id',
                'required': True,
                'dataType': "number",
                'paramType': 'path'
            },
            {
                'name': 'description',
                'required': True,
                'dataType': "string",
                'paramType': 'body'
            }
        ],
        responseMessages=[
            {
                'code': 200,
                'message': 'Returns ID of added prize'
            },
            {
                'code': 400,
                'message': 'Bad request'
            },
            {
                'code': 404,
                'message': 'Promo not found'
            },
        ]
    )
    def post(self, promo_id):
        promo = abort_if_promo_not_found(promo_id)

        args = PrizesListApi.post_parser.parse_args()
        prize = Prize(
            id=len(prizes) + 1,
            description=args['description']
        )
        prizes[prize.id] = prize
        promo.prizes.append(prize.id)

        return jsonify(prize.id)


class PrizeApi(Resource):
    @swagger.operation(
        notes='Удаление приза из промоакции по идентификаторам промоакции и приза',
        nickname='delete',
        parameters=[
            {
                'name': 'promo_id',
                'required': True,
                'dataType': "number",
                'paramType': 'path'
            },
            {
                'name': 'prize_id',
                'required': True,
                'dataType': "number",
                'paramType': 'path'
            }
        ],
        responseMessages=[
            {
                'code': 200,
                'message': 'OK'
            },
            {
                'code': 400,
                'message': 'Bad request'
            },
            {
                'code': 404,
                'message': 'Promo or prize in promo not found'
            },
        ]
    )
    def delete(self, promo_id, prize_id):
        promo = abort_if_promo_not_found(promo_id)
        if prize_id not in promo.prizes:
            abort(404, message=f'Prize {prize_id} in promo {promo_id} not found')
        promo.prizes.remove(prize_id)
        return jsonify('OK')


class RaffleApi(Resource):
    @swagger.operation(
        notes='''Проведение розыгрыша призов в промоакции по идентификатору промоакции Проведение розыгрыша возможно 
        только в том случае, когда количество участников и призов в промоакции совпадает (т.е., например, 
        если в промоакции в текущий момент 2 участника и 2 приза или 3 участника и 3 приза и т.д.)''',
        nickname='post',
        parameters=[
            {
                'name': 'promo_id',
                'required': True,
                'dataType': "number",
                'paramType': 'path'
            }
        ],
        responseMessages=[
            {
                'code': 200,
                'message': 'Returns list of results'
            },
            {
                'code': 404,
                'message': 'Promo not found'
            },
            {
                'code': 409,
                'message': 'Raffle is unavailable'
            },
        ]
    )
    def post(self, promo_id):
        promo = abort_if_promo_not_found(promo_id)

        if len(promo.participants) == 0:
            return jsonify('No participants'), 409

        if len(promo.prizes) == 0:
            return jsonify('No prizes'), 409

        if len(promo.participants) != len(promo.prizes):
            return jsonify('Conflict'), 409

        winners = promo.participants[:]
        w_prizes = promo.prizes[:]
        shuffle(promo.participants)
        shuffle(promo.prizes)

        return jsonify([
            {
               "winner": participant_map(winners[i]),
               "prize": prize_map(w_prizes[i])
            } for i in range(len(winners))
        ])


def abort_if_promo_not_found(promo_id):
    if promo_id in promos:
        return promos[promo_id]
    abort(404, message=f'Promo {promo_id} not found')


app = Flask(__name__, static_folder='static')

api = swagger.docs(
    Api(app, catch_all_404s=True),
    apiVersion="0.1",
    basePath="http://127.0.0.1:8080",
    resourcePath="/",
    produces=["application/json", "text/html"],
    api_spec_url="/docs",
    description="API розыгрышей",
)
api.add_resource(PromosListApi, '/promo')
api.add_resource(PromoApi, '/promo/<int:promo_id>')
api.add_resource(ParticipantsListApi, '/promo/<int:promo_id>/participant')
api.add_resource(ParticipantApi, '/promo/<int:promo_id>/participant/<int:participant_id>')
api.add_resource(PrizesListApi, '/promo/<int:promo_id>/prize')
api.add_resource(PrizeApi, '/promo/<int:promo_id>/prize/<int:prize_id>')
api.add_resource(RaffleApi, '/promo/<int:promo_id>/raffle')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
