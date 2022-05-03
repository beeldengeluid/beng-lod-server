from flask_restx import Namespace, Resource

api = Namespace("Pong", description="Used for monitoring and DevOps.")


@api.hide
@api.route("pong", "ping")
class Pong(Resource):
    def get(self):
        return "pong"
